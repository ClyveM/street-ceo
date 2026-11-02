"""Saved sales table/details browser checks; all API records are synthetic/read-only."""
import functools
import json
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect

root=Path(__file__).resolve().parents[1];out=root/'data/qa-sales-history-20261102';out.mkdir(parents=True,exist_ok=True)
shop='00000000-0000-0000-0000-000000000001'
products=[{'id':'p1','shop_id':shop,'name':'Current renamed cola','sku':'COKE-NEW','unit_price_cents':99999,'stock_qty':999,'unit_cost_micros':9000000},
          {'id':'p2','shop_id':shop,'name':'Current bread fallback','sku':'BREAD-700','unit_price_cents':77777,'stock_qty':999,'unit_cost_micros':8000000}]
sales=[{'id':'cash-snapshot','shop_id':shop,'lines':[{'product_id':'p1','quantity':2},{'product_id':'deleted','quantity':1}],
        'tender':'cash','total_cents':500,'amount_received_cents':1000,'change_cents':500,'stock_after':{'p1':16,'deleted':4},'created_at':'2026-11-02T18:10:00Z',
        'receipt_lines':[{'product_id':'p1','product_name':'Historic Coca-Cola 300ml','sku':'COKE-300','quantity':2,'unit_price_cents':150,'line_total_cents':300},
                         {'product_id':'deleted','product_name':'Deleted product with a deliberately long historical receipt label','sku':'OLD-200','quantity':1,'unit_price_cents':200,'line_total_cents':200}]},
       {'id':'legacy-unknown-cash','shop_id':shop,'lines':[{'product_id':'p2','quantity':1},{'product_id':'lost-product-reference','quantity':2}],
        'tender':'cash','total_cents':360,'amount_received_cents':None,'change_cents':0,'stock_after':{},'created_at':'2026-11-01T18:10:00Z'},
       {'id':'bank-recorded','shop_id':shop,'lines':[{'product_id':'p2','quantity':1}],'tender':'bank','total_cents':180,'amount_received_cents':None,'change_cents':0,
        'stock_after':{'p2':8},'created_at':'2026-10-31T18:10:00Z'},
       {'id':'large-cash','shop_id':shop,'lines':[{'product_id':'p1','quantity':10000000}],'tender':'cash','total_cents':75000000,'amount_received_cents':80000000,
        'change_cents':5000000,'stock_after':{'p1':0},'created_at':'2026-10-30T18:10:00Z'},
       {'id':'zero-cash','shop_id':shop,'lines':[{'product_id':'p1','quantity':1}],'tender':'cash','total_cents':0,'amount_received_cents':0,'change_cents':0,
        'stock_after':{'p1':0},'created_at':'2026-10-29T18:10:00Z'}]
long_sale=json.loads(json.dumps(sales[0]));long_sale.update(id='long-cash',created_at='2026-11-02T18:11:00Z')
for number in range(5):
 pid=f'extra-{number}'
 long_sale['lines'].append({'product_id':pid,'quantity':1})
 long_sale['receipt_lines'].append({'product_id':pid,'product_name':f'Saved extra product with a deliberately long historical label {number}','sku':f'EXTRA-{number}','quantity':1,'unit_price_cents':0,'line_total_cents':0})
 long_sale['stock_after'][pid]=0
state={'mode':'normal','posts':[],'reads':0,'pending':None,'long':False}

class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root/'apps/web/dist')))
Thread(target=server.serve_forever,daemon=True).start()
def route(r):
 req=r.request;url=urlparse(req.url);path=url.path
 if url.hostname=='127.0.0.1' and url.port==server.server_port:
  dist=(root/'apps/web/dist').resolve();asset=(dist/(url.path.lstrip('/') or 'index.html')).resolve()
  if asset.is_relative_to(dist) and asset.is_file():r.fulfill(path=str(asset))
  else:r.fulfill(status=404,body='Missing isolated fixture asset')
  return
 if url.hostname!='shop.invalid':r.abort('blockedbyclient');return
 headers={'Access-Control-Allow-Origin':'*'}
 def reply(value,status=200):r.fulfill(status=status,content_type='application/json',body=json.dumps(value),headers=headers)
 if req.method=='OPTIONS':r.fulfill(status=204,headers={**headers,'Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'});return
 if req.method=='POST':state['posts'].append(path)
 if path=='/readyz':reply({'status':'ready'});return
 if path==f'/shops/{shop}':reply({'id':shop,'currency':'USD'});return
 if path.endswith('/products'):reply(products);return
 if path.endswith('/summary'):reply({'sales_total_cents':1040,'transaction_count':5,'low_stock_count':0,'sales_change_percent':None,'insight':'Synthetic records'});return
 if path.endswith('/sales'):
  state['reads']+=1
  if state['mode']=='hold':state['pending']=r;return
  if state['mode']=='error':reply({'detail':'Test history unavailable'},503);return
  reply([] if state['mode']=='empty' else sales+[sales[0]] if state['mode']=='invalid' else sales+([long_sale] if state['long'] else []));return
 reply([])

try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='msedge',headless=True,timeout=20000,args=['--disable-gpu'])
  context=browser.new_context(viewport={'width':390,'height':844});context.route('**/*',route)
  context.add_init_script("""localStorage.setItem('street-ceo-api-config',JSON.stringify({baseUrl:'http://shop.invalid',shopId:'00000000-0000-0000-0000-000000000001'}));localStorage.setItem('street-ceo-hands-free-v1','off');""")
  page=context.new_page();page.set_default_timeout(10000);page.set_default_navigation_timeout(30000)
  errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='domcontentloaded')
  page.locator('.stat-card-button').filter(has_text='view history').click()
  history=page.locator('.sales-history-page');table=history.locator('.sales-history-table');panel=history.locator('#history-selected-receipt')
  expect(history.get_by_role('heading',name='Sales history',exact=True)).to_be_visible()
  expect(table.locator('tbody tr')).to_have_count(5)
  expect(table.get_by_role('columnheader',name='Total')).to_contain_text('USD')
  for width in (390,320):
   page.set_viewport_size({'width':width,'height':844});page.evaluate("window.scrollTo({top:0,behavior:'instant'})");page.wait_for_function('window.scrollY===0')
   dimensions=page.evaluate('({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})');assert dimensions['client']==dimensions['scroll'],dimensions
   large=table.locator('tbody tr').filter(has=page.get_by_role('button',name='Open receipt large-cash',exact=True))
   expect(large.locator('.history-total-value')).to_have_text('750000.00')
   assert large.locator('.history-total-value').evaluate("el=>{const r=document.createRange();r.selectNodeContents(el);return r.getClientRects().length}")==1
   page.screenshot(path=str(out/f'history-top-{width}.png'))
  first=table.get_by_role('button',name='Open receipt cash-snapshot',exact=True)
  covered=[]
  for width in (390,320):
   page.set_viewport_size({'width':width,'height':844});page.evaluate("window.scrollTo({top:0,behavior:'instant'})");page.wait_for_function('window.scrollY===0')
   first.click();expect(panel).to_be_focused()
   page.evaluate('async()=>{await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))}')
   title=panel.get_by_role('heading',name='Sale details',exact=True).bounding_box()
   close=panel.get_by_role('button',name='Close saved receipt',exact=True).bounding_box()
   bar=page.locator('.topbar').bounding_box()
   page.screenshot(path=str(out/f'receipt-tap-{width}.png'))
   if not title or not close or not bar or title['y']<bar['y']+bar['height'] or close['y']<bar['y']+bar['height']:
    covered.append({'width':width,'title':title,'close':close,'topbar':bar})
   panel.get_by_role('button',name='Close saved receipt',exact=True).click()
  assert not covered,covered
  first.focus();first.press('Enter');expect(panel).to_be_focused()
  expect(panel.locator('.history-receipt-total')).to_contain_text('USD 5.00')
  expect(panel.locator('.history-payment').locator('strong').nth(0)).to_have_text('USD 10.00')
  expect(panel.locator('.history-payment').locator('strong').nth(1)).to_have_text('USD 5.00')
  expect(panel.locator('.history-receipt-products')).to_contain_text('Historic Coca-Cola 300ml')
  expect(panel.locator('.history-receipt-products')).to_contain_text('Deleted product with a deliberately long historical receipt label')
  expect(panel).not_to_contain_text('Current renamed cola');expect(panel).not_to_contain_text('999.99')
  expect(panel.locator('.history-receipt-products li').nth(0)).to_contain_text('× 2')
  panel.locator('.history-receipt-more summary').click()
  expect(panel.locator('.history-receipt-more')).to_contain_text('stock after sale 16')
  expect(panel.locator('.history-receipt-more')).not_to_contain_text('stock after sale 999')
  for width in (390,320):
   page.set_viewport_size({'width':width,'height':844});panel.scroll_into_view_if_needed()
   dims=page.evaluate('({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})');assert dims['client']==dims['scroll'],dims
   page.screenshot(path=str(out/f'receipt-{width}.png'),full_page=True)
  panel.press('Escape');expect(panel).to_have_count(0);expect(first).to_be_focused()
  first.press('Space');expect(panel).to_be_visible();panel.get_by_role('button',name='Close saved receipt',exact=True).click();expect(first).to_be_focused()
  table.get_by_role('button',name='Open receipt legacy-unknown-cash',exact=True).click()
  expect(panel.locator('.history-payment strong')).to_have_text(['Not supplied','Not supplied'])
  expect(panel).to_contain_text('Exact payment and change are unknown')
  expect(panel.locator('.history-receipt-products')).to_contain_text('Current bread fallback')
  expect(panel.locator('.history-receipt-products')).to_contain_text('lost-product-reference')
  expect(panel.locator('.history-receipt-total')).to_contain_text('USD 3.60')
  page.screenshot(path=str(out/'receipt-legacy-320.png'),full_page=True)
  table.get_by_role('button',name='Open receipt zero-cash',exact=True).click()
  expect(panel.locator('.history-payment strong')).to_have_text(['USD 0.00','USD 0.00'])
  table.get_by_role('button',name='Open receipt bank-recorded',exact=True).click()
  panel.locator('.history-receipt-more summary').click()
  expect(panel.locator('.history-receipt-more')).to_contain_text('settlement is not verified')
  table.get_by_role('button',name='Open receipt cash-snapshot',exact=True).click()
  state['mode']='hold';history.get_by_role('button',name='Refresh',exact=False).click()
  expect(history.locator('.history-loading')).to_be_visible();expect(history.locator('.history-empty')).to_have_count(0)
  assert state['pending'] is not None
  state['pending'].fulfill(status=503,content_type='application/json',body='{"detail":"Synthetic error"}',headers={'Access-Control-Allow-Origin':'*'});state['pending']=None;state['mode']='error'
  expect(history.locator('.history-error').first).to_contain_text('Previously loaded receipts are shown below')
  expect(history.locator('.history-empty')).to_have_count(0)
  page.screenshot(path=str(out/'history-error-320.png'),full_page=True)
  state['mode']='empty';history.get_by_role('button',name='Try again',exact=True).click()
  expect(history.locator('.history-empty')).to_be_visible()
  expect(panel.locator('.history-receipt-total')).to_have_count(0)
  expect(panel.get_by_role('alert')).to_contain_text('not in the latest verified history')
  panel.get_by_role('button',name='Close saved receipt',exact=True).click()
  expect(history.get_by_role('button',name='Back to Today',exact=False)).to_be_focused()
  page.evaluate("window.scrollTo({top:0,behavior:'instant'})");page.screenshot(path=str(out/'history-empty-320.png'))
  state['mode']='invalid';history.get_by_role('button',name='Refresh',exact=False).click()
  expect(history.locator('.history-error').first).to_contain_text('could not be verified')
  expect(table).to_have_count(0);expect(history.locator('.history-empty')).to_have_count(0)
  state['mode']='normal';history.get_by_role('button',name='Try again',exact=True).click();expect(table.locator('tbody tr')).to_have_count(5)
  state['long']=True;history.get_by_role('button',name='Refresh',exact=False).click();expect(table.locator('tbody tr')).to_have_count(6)
  covered=[]
  for width in (390,320):
   page.set_viewport_size({'width':width,'height':844});page.evaluate("window.scrollTo({top:0,behavior:'instant'})");page.wait_for_function('window.scrollY===0')
   table.get_by_role('button',name='Open receipt long-cash',exact=True).click();expect(panel).to_be_focused()
   page.evaluate('async()=>{await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))}')
   title=panel.get_by_role('heading',name='Sale details',exact=True).bounding_box();close=panel.get_by_role('button',name='Close saved receipt',exact=True).bounding_box();bar=page.locator('.topbar').bounding_box()
   page.screenshot(path=str(out/f'receipt-long-tap-{width}.png'))
   if not title or not close or not bar or title['y']<bar['y']+bar['height'] or close['y']<bar['y']+bar['height']:covered.append({'width':width,'title':title,'close':close,'topbar':bar})
   panel.get_by_role('button',name='Close saved receipt',exact=True).click()
  assert not covered,covered
  page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Stock').click();expect(page.locator('.stock-catalog-table')).to_be_visible()
  assert not state['posts'],state['posts'];assert not errors,errors
  print('DOM PASS: SaleshistoryDate/Payment/Total320390wholeamounts; readonlyrow Enter/Space/Escape/Closefocus; savedhistoricalnames/deletedfallback/qty/stock/no repricing; exactcashreceived/change vslegacyunknown andzero; bankunverifiednote; loading/errorcachedlabel/empty/invalid/refreshstaleremoval+focusfallback; Stocknav; zeroPOST',flush=True)
  print(str(out),flush=True)
  browser.close()
finally:
 server.shutdown();server.server_close()
