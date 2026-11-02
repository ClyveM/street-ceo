"""Actual built daily sheet UI with isolated deterministic API fixtures."""
import functools,io,json,copy
from pathlib import Path
from urllib.parse import urlparse
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from PIL import Image
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1];dist=root/'apps/web/dist';out=root/'data/qa-capture-integrated';out.mkdir(parents=True,exist_ok=True)
shop='00000000-0000-0000-0000-000000000001';product={'id':'p1','shop_id':shop,'name':'Bread loaf','sku':'BREAD','unit_price_cents':180,'stock_qty':20,'unit_cost_micros':1200000}
buf=io.BytesIO();Image.new('RGB',(15,15),'green').save(buf,format='PNG');png=buf.getvalue()
state={'record':None,'posts':[],'mode':'normal','counter':0}
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(dist)));Thread(target=server.serve_forever,daemon=True).start()
def draft():
 state['counter']+=1
 return {'id':f'sheet-{state["counter"]}','shop_id':shop,'record_type':'daily_sales_batch','status':'draft','business_date':'2026-11-02','created_at':'2026-11-02T18:00:00Z','confirmed_at':None,'filename':'sheet.png','content_type':'image/png','source_sha256':'a'*64,'source_ref':'sheet.png','ocr_lines':[{'raw_label':'Bread ?','product_id':'p1','quantity':3,'unit_price_cents':None,'line_total_cents':100}],'warnings':['Review every image value.'],'extraction_status':'review','lines':[],'cash_cents':None,'bank_cents':None,'total_cents':None,'actor':'','notes':'','reviewed_version':None,'stock_baseline':{},'existing_sales_total_cents':0,'existing_transaction_count':0,'existing_daily_summary_count':0}
def route(r):
 req=r.request;u=urlparse(req.url);path=u.path
 if u.hostname=='127.0.0.1' and u.port==server.server_port:
  f=(dist/(path.lstrip('/') or 'index.html')).resolve()
  if f.is_relative_to(dist.resolve()) and f.is_file():r.fulfill(path=str(f))
  else:r.fulfill(status=404,body='missing')
  return
 if u.scheme=='blob':r.continue_();return
 if u.hostname!='shop.invalid':r.abort();return
 headers={'Access-Control-Allow-Origin':'*'}
 def reply(v,status=200):r.fulfill(status=status,content_type='application/json',headers=headers,body=json.dumps(v))
 if req.method=='OPTIONS':r.fulfill(status=204,headers={**headers,'Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'});return
 if req.method=='POST':state['posts'].append((path,req.headers.get('idempotency-key'),req.post_data_json if 'application/json' in req.headers.get('content-type','') else 'multipart'))
 if path.endswith('/daily-sales-batches/extract'):state['record']=draft();reply(state['record'],201);return
 if path.endswith('/review'):
  body=req.post_data_json;record=state['record'];record.update(body,status='reviewed',total_cents=sum(i['line_total_cents'] for i in body['lines']),reviewed_version=('b' if record['reviewed_version']!='b'*64 else 'c')*64,stock_baseline={'p1':20})
  record['lines']=[{**i,'product_name':'Bread loaf','sku':'BREAD'} for i in body['lines']];reply(record);return
 if path.endswith('/confirm'):
  if state['mode']=='stale':reply({'detail':{'code':'paper_review_stale','message':'Review changed'}},409);return
  state['record'].update(status='confirmed',confirmed_at='2026-11-02T18:20:00Z',warnings=['Historical cost unknown.'])
  if state['mode']=='lost':reply({'detail':'Synthetic lost response'},503)
  else:reply(state['record'])
  return
 if '/daily-sales-batches' in path:
  if path.endswith('/image'):r.fulfill(body=png,content_type='image/png',headers=headers);return
  if path.endswith('/daily-sales-batches'):reply([state['record']] if state['record'] else []);return
  value=copy.deepcopy(state['record'])
  if state['mode']=='mismatch':value['reviewed_version']='f'*64
  reply(value);return
 if path=='/readyz':reply({'status':'ready'});return
 if path==f'/shops/{shop}':reply({'id':shop,'currency':'USD'});return
 if path.endswith('/products'):reply([product]);return
 if path.endswith('/summary'):reply(None);return
 reply([])
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='msedge',headless=True,args=['--disable-gpu'])
  context=browser.new_context(viewport={'width':390,'height':844},service_workers='block');context.route('**/*',route)
  context.add_init_script("""localStorage.setItem('street-ceo-api-config',JSON.stringify({baseUrl:'http://shop.invalid',shopId:'00000000-0000-0000-0000-000000000001'}));localStorage.setItem('street-ceo-hands-free-v1','off');""")
  page=context.new_page();page.set_default_timeout(10000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='load');page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Sell').click();page.get_by_role('button',name='Upload daily sales sheet',exact=True).click()
  sheet=page.locator('.paper-sales-page');expect(sheet).to_contain_text('No saved daily summaries yet.')
  sheet.get_by_label('Photo of your daily list').set_input_files({'name':'sheet.png','mimeType':'image/png','buffer':png});sheet.get_by_role('button',name='Read daily sales sheet',exact=True).click()
  expect(sheet.get_by_role('heading',name='Review the handwriting')).to_be_visible();expect(sheet.get_by_label('Quantity sold')).to_have_value('3');expect(sheet.get_by_label('Actual line amount')).to_have_value('1.00')
  sheet.get_by_label('Recorded by').fill('Tester');sheet.get_by_label('Cash sales',exact=True).fill('0.40');sheet.get_by_label('Bank sales',exact=True).fill('0.60');sheet.get_by_role('button',name='Save reviewed summary').click()
  expect(sheet.get_by_role('heading',name='Check this summary')).to_be_visible();expect(sheet).to_contain_text('mixed / unspecified unit price');confirm=sheet.get_by_role('button',name='Confirm daily summary & stock');expect(confirm).to_be_disabled()
  for checkbox in sheet.get_by_role('checkbox').all():checkbox.check()
  for width in (390,320):
   page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');sheet.screenshot(path=str(out/f'paper-reviewed-{width}.png'))
  state['mode']='lost';confirm.click();expect(sheet.get_by_role('heading',name='Check the original confirmation')).to_be_visible();assert len([x for x in state['posts'] if x[0].endswith('/confirm')])==1
  expect(page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Sell')).to_be_disabled()
  state['mode']='mismatch';sheet.get_by_role('button',name='Check saved summary').click();expect(sheet).to_contain_text('does not match the original reviewed version');expect(sheet.get_by_role('heading',name='Daily summary recorded',exact=True)).to_have_count(0)
  state['mode']='normal';sheet.get_by_role('button',name='Check saved summary').click();expect(sheet.get_by_role('heading',name='Daily summary recorded',exact=True)).to_be_visible();expect(sheet.get_by_role('button',name='Confirm daily summary & stock')).to_have_count(0)
  assert len([x for x in state['posts'] if x[0].endswith('/confirm')])==1
  sheet.screenshot(path=str(out/'paper-confirmed-320.png'))
  # A new reviewed summary becomes uncertain, then explicit stale rejection permits a fresh same-record review only.
  sheet.get_by_label('Photo of your daily list').set_input_files({'name':'sheet2.png','mimeType':'image/png','buffer':png});sheet.get_by_role('button',name='Read daily sales sheet',exact=True).click();sheet.get_by_label('Recorded by').fill('Tester');sheet.get_by_label('Cash sales',exact=True).fill('1.00');sheet.get_by_label('Bank sales',exact=True).fill('0');sheet.get_by_role('button',name='Save reviewed summary').click();expect(sheet.get_by_role('heading',name='Check this summary')).to_be_visible()
  for checkbox in sheet.get_by_role('checkbox').all():checkbox.check()
  # First503 need not mean server committed; original record remains reviewed in this scenario.
  state['mode']='lost';sheet.get_by_role('button',name='Confirm daily summary & stock').click();expect(sheet.get_by_role('heading',name='Check the original confirmation')).to_be_visible();state['record'].update(status='reviewed',confirmed_at=None);state['mode']='stale'
  sheet.get_by_role('button',name='Retry original confirmation').click();expect(sheet.get_by_role('button',name='Review this summary again')).to_be_visible();state['record'].update(status='confirmed',confirmed_at='2026-11-02T18:20:00Z');state['mode']='mismatch';sheet.get_by_role('button',name='Check saved summary').click();expect(sheet).to_contain_text('does not match the original reviewed version');expect(sheet.get_by_role('button',name='Review this summary again')).to_have_count(0);state['record'].update(status='reviewed',confirmed_at=None);state['mode']='stale';sheet.get_by_role('button',name='Retry original confirmation').click();expect(sheet.get_by_role('button',name='Review this summary again')).to_be_visible();sheet.get_by_role('button',name='Review this summary again').click();expect(sheet.get_by_role('heading',name='Review the handwriting')).to_be_visible();assert page.evaluate("Object.keys(localStorage).some(k=>k.includes(':retired:sheet-2'))")
  state['mode']='normal';sheet.get_by_role('button',name='Save reviewed summary').click();expect(sheet.get_by_role('button',name='Confirm daily summary & stock')).to_be_disabled();assert all(not c.is_checked() for c in sheet.get_by_role('checkbox').all())
  assert not errors,errors;browser.close();print('PASS paper upload/editmixedprices/3declarations/unknownrecovery/versionguard/stalereview/tombstone/320390')
finally:server.shutdown()


