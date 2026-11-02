import functools,io,json,hashlib
from pathlib import Path
from urllib.parse import urlparse
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from PIL import Image
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1];dist=root/'apps/web/dist';out=root/'data/qa-capture-integrated';out.mkdir(parents=True,exist_ok=True);shop='00000000-0000-0000-0000-000000000001'
products=[{'id':f'p{i}','shop_id':shop,'name':f'Product {i}','sku':f'SKU{i}','unit_price_cents':100,'stock_qty':10,'unit_cost_micros':500000} for i in range(100)]
lines=[{'product_id':p['id'],'product_name':p['name'],'quantity':1} for p in products]
initial={'request_id':'review-a','shop_id':shop,'status':'needs_clarification','transcript':', '.join('one '+p['name'] for p in products[:-1])+', one mystery','lines':[],'retained_lines':lines[:-1],'pending_items':[{'slot_id':99,'heard':'mystery','quantity':1,'product_id':None,'product_name':None}],'requires_match_confirmation':False,'clarification_question':'What product did you mean by mystery?','resolution_source':'local_clarification','provider_called':False}
final={**initial,'request_id':'review-b','status':'needs_match_confirmation','lines':lines,'retained_lines':[],'pending_items':[],'requires_match_confirmation':True,'intent':{'action':'record_sale','needs_confirmation':True},'clarification_question':'Review all100 products. Say yes to confirm all items.'}
key=f'street-ceo-retained-v1:http%3A%2F%2Fshop.invalid:{shop}'
buf=io.BytesIO();Image.new('RGB',(15,15),'blue').save(buf,format='PNG');png=buf.getvalue();sha=hashlib.sha256(png).hexdigest()
metadata={'id':'image-1','shop_id':shop,'product_id':'p0','filename':'product.png','content_type':'image/png','size_bytes':len(png),'sha256':sha,'storage_backend':'memory','storage_ref':'memory://product-images/image-1','uploaded_at':'2026-11-02T18:00:00Z'}
state={'posts':[],'lost':True,'images':True}
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(dist)));Thread(target=server.serve_forever,daemon=True).start()
def route(r):
 req=r.request;u=urlparse(req.url);path=u.path
 if u.hostname=='127.0.0.1' and u.port==server.server_port:
  f=(dist/(path.lstrip('/') or 'index.html')).resolve()
  if f.is_relative_to(dist.resolve()) and f.is_file():r.fulfill(path=str(f))
  else:r.fulfill(status=404,body='missing')
  return
 if u.scheme=='blob':r.continue_();return
 if u.hostname!='shop.invalid':r.abort();return
 h={'Access-Control-Allow-Origin':'*'}
 def reply(v,status=200):r.fulfill(status=status,content_type='application/json',headers=h,body=json.dumps(v))
 if req.method=='OPTIONS':r.fulfill(status=204,headers={**h,'Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'});return
 if req.method=='POST':state['posts'].append((path,req.headers.get('idempotency-key'),req.post_data_json))
 if path.endswith('/voice/transcript'):
  if state['lost']:reply({'detail':'Synthetic lost interpretation response'},503)
  else:reply(final)
  return
 if path.endswith('/voice/commit'):reply({'status':'needs_tender','review_id':'review-b','question':'Choose Cash or Bank for this sale.','amount_due_cents':10000,'allowed_tenders':['cash','bank'],'missing':['tender']});return
 if path=='/readyz':reply({'status':'ready'});return
 if path==f'/shops/{shop}':reply({'id':shop,'currency':'USD'});return
 if path.endswith('/products'):reply(products);return
 if path.endswith('/summary'):reply(None);return
 if path.endswith('/product-images'):reply([metadata] if state['images'] else []);return
 if path.endswith('/image/content'):r.fulfill(body=png,content_type='image/png',headers={**h,'ETag':'"'+sha+'"','X-Product-Image-ID':'image-1','Access-Control-Expose-Headers':'ETag,X-Product-Image-ID'});return
 reply([])
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='msedge',headless=True,args=['--disable-gpu'])
  context=browser.new_context(viewport={'width':390,'height':844},service_workers='block');context.route('**/*',route)
  context.add_init_script("""localStorage.setItem('street-ceo-api-config',JSON.stringify({baseUrl:'http://shop.invalid',shopId:'00000000-0000-0000-0000-000000000001'}));window.__listeners={};window.__prompts=[];window.__starts=0;window.__emit=(name,data={})=>{for(const fn of [...(window.__listeners[name]||[])])fn(data)};const plugin={async addListener(n,f){(window.__listeners[n]??=new Set()).add(f);return{async remove(){window.__listeners[n].delete(f)}}},async start(){window.__starts++;setTimeout(()=>window.__emit('speechReady'),5)},async stop(){},async speak({text}){window.__prompts.push(text);await new Promise(r=>setTimeout(r,10))},async stopSpeaking(){}};window.Capacitor={getPlatform:()=> 'android',registerPlugin:()=>plugin};""")
  page=context.new_page();page.set_default_timeout(10000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='load');page.evaluate('([key,review])=>localStorage.setItem(key,JSON.stringify({review,attempt:null}))',[key,initial]);page.reload(wait_until='load')
  expect(page.get_by_role('button',name='Resume basket',exact=True)).to_be_visible();expect(page.locator('.sale-product-photo')).to_have_count(1)
  page.get_by_role('button',name='Add Product 0',exact=True).click();page.get_by_role('button',name='Bank',exact=False).filter(has_text='Bank').first.click();expect(page.get_by_role('button',name='Review sale')).to_be_disabled();page.get_by_role('button',name='Remove one Product 0',exact=True).click()
  page.get_by_role('button',name='Resume basket',exact=True).click();dialog=page.get_by_role('dialog');expect(dialog).to_contain_text('99 products kept.')
  def say(text):
   page.wait_for_function("document.querySelector('.voice-status')?.textContent.includes('Listening') || document.querySelector('.voice-status')?.textContent.includes('Answer') || document.querySelector('.voice-status')?.textContent.includes('Say')")
   page.evaluate("text=>window.__emit('speech',{text,final:true})",text)
  say('Product 99');expect(dialog).to_contain_text('Retry this answer');assert len(state['posts'])==1
  attempt=state['posts'][0];assert attempt[2]=={'transcript':'Product 99','clarification_of':'review-a'}
  page.reload(wait_until='load');page.get_by_role('button',name='Resume basket',exact=True).click();dialog=page.get_by_role('dialog');state['lost']=False
  say('Retry');expect(dialog.locator('.counter-items > li')).to_have_count(100);assert state['posts'][1]==attempt
  expect(dialog.locator('.sale-basket-photo')).to_have_count(1);assert not any('/commit' in x[0] for x in state['posts'])
  say('Yes');expect(dialog.get_by_role('heading',name='Payment',exact=True)).to_be_visible();page.wait_for_function("window.__prompts.includes('Cash or bank?')");assert page.evaluate('key=>localStorage.getItem(key)',key) is None
  say('Cancel');expect(dialog).to_have_count(0)
  # Reload checkpoint can be explicitly discarded and malformed storage never permits manual posting.
  page.evaluate('([key,review])=>localStorage.setItem(key,JSON.stringify({review,attempt:null}))',[key,initial]);page.reload(wait_until='load');page.get_by_role('button',name='Discard basket',exact=True).click();assert page.evaluate('key=>localStorage.getItem(key)',key) is None
  page.evaluate('(key)=>localStorage.setItem(key,"bad-json")',key);page.reload(wait_until='load');expect(page.get_by_role('button',name='Discard unreadable saved basket',exact=True)).to_be_visible();page.get_by_role('button',name='Discard unreadable saved basket',exact=True).click();assert page.evaluate('key=>localStorage.getItem(key)',key) is None
  for width in (390,320):
   page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(out/f'sale-photos-{width}.png'))
  assert all('tender' not in x[2] for x in state['posts'] if '/commit' in x[0]);assert not errors,errors;browser.close();print('PASS retained99+focused100/ASRretryreloadsamekey/Yesbeforepayment/manualguard/discardmalformed/storedphotosreload')
finally:server.shutdown()



