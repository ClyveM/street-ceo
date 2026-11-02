import http.client,json,uuid,hashlib,zipfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
connection=http.client.HTTPConnection('192.168.10.213',8000,timeout=45)
shop=None

def call(method,path,body=None,key=None,expected=200):
 headers={'Content-Type':'application/json'}
 if shop: headers['X-Shop-ID']=shop
 if key: headers['Idempotency-Key']=key
 connection.request(method,path,json.dumps(body) if body is not None else None,headers)
 response=connection.getresponse(); data=json.loads(response.read())
 assert response.status==expected,(path,response.status,data)
 return data

def result(name,data): print(name,json.dumps(data),flush=True)

result('health',call('GET','/healthz')); result('ready',call('GET','/readyz'))
created=call('POST','/shops',{'name':'Synthetic W6 QA '+uuid.uuid4().hex[:8]},expected=201)
shop=created['id']; result('synthetic_shop',{'id':shop})
base='/api/v1/shops/'+shop
product=call('POST','/shops/'+shop+'/products',{'sku':'QA-W6','name':'QA Biscuits','unit_price_cents':200},expected=201)
pid=product['id']
def purchase(ref,qty,cost):
 draft=call('POST',base+'/purchases',{'kind':'manual','reference':ref,'purchase_date':'2026-10-31','actor':'synthetic-qa','tender':'unpaid','total_cost_micros':qty*cost,'lines':[{'product_id':pid,'quantity':qty,'purchase_unit_cost_micros':cost,'line_total_micros':qty*cost}]},expected=201)
 return call('POST',base+'/purchases/'+draft['id']+'/confirm')
purchase('QA-1',10,1000000); p=purchase('QA-2',10,2000000)
products=call('GET','/shops/'+shop+'/products'); assert products[0]['stock_qty']==20 and products[0]['unit_cost_micros']==1500000
result('purchase_wac',{'stock':20,'unit_cost_micros':1500000})
payload={'lines':[{'product_id':pid,'quantity':2}],'tender':'cash'}
sale=call('POST','/shops/'+shop+'/sales',payload,'qa-sale',201)
assert sale['stock_after'][pid]==18 and sale['total_cents']==400
assert call('POST','/shops/'+shop+'/sales',payload,'qa-sale',201)==sale
call('POST','/shops/'+shop+'/sales',{**payload,'tender':'bank'},'qa-sale',409)
assert call('GET','/shops/'+shop+'/products')[0]['stock_qty']==18
result('sale_stock_idempotency',{'sale_id':sale['id'],'stock':18,'total_cents':400})
preview=call('GET',base+'/day-close/preview?business_date=2026-10-31');result('day_close_preview',preview)
closebody={'business_date':'2026-10-31','cash_counted_cents':400,'bank_card_counted_cents':0,'actor':'synthetic-qa','confirmed':True}
close=call('POST',base+'/day-close',closebody,'qa-close',201)
assert close['cash_variance_cents']==0 and close['bank_card_variance_cents']==0
assert call('POST',base+'/day-close',closebody,'qa-close',201)==close
result('day_close',close)
for name,path,body in [
 ('muse',base+'/muse',{'question':'What profit did I make today?'}),
 ('social_brief',base+'/social/brief',{'product_ids':[pid]}),
 ('social_draft',base+'/social/draft',{'product_ids':[pid],'brief':'Describe QA Biscuits using only verified catalogue facts.'}),
 ('social_image',base+'/social/image-generation',{'product_ids':[pid],'brief':'A simple product illustration for QA Biscuits','aspect_ratio':'1:1'})]:
 try:
  data=call('POST',path,body)
  # Return only bounded, non-media status evidence.
  result(name,{k:v for k,v in data.items() if k in ['status','source','reason','error','provider','answer','missing_data','catalogue_source','warnings','evidence_ids']})
 except Exception as e: result(name,{'error':str(e)[:1200]})
