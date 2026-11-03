"""Clickable catalogue table checks against isolated product/cost fixtures."""
import functools
import io
import json
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse
from PIL import Image
from playwright.sync_api import sync_playwright,expect

root=Path(__file__).resolve().parents[1];out=root/'data/qa-stock-table-20261102';out.mkdir(parents=True,exist_ok=True)
shop='00000000-0000-0000-0000-000000000001'
products=[{'id':'cola','shop_id':shop,'name':'Coca-Cola 300ml','sku':'COKE-300','unit_price_cents':150,'stock_qty':18,'unit_cost_micros':1000000},
          {'id':'bread','shop_id':shop,'name':'Bread loaf with a deliberately very long catalogue label','sku':'BREAD-700','unit_price_cents':180,'stock_qty':2,'unit_cost_micros':1200000},
          {'id':'zero','shop_id':shop,'name':'Zero stock soap','sku':'SOAP-ZERO','unit_price_cents':0,'stock_qty':0,'unit_cost_micros':None},
          {'id':'bulk','shop_id':shop,'name':'Bulk stock','sku':'BULK-100','unit_price_cents':75000000,'stock_qty':10000000,'unit_cost_micros':2000000}]
state={'posts':[],'draft':None,'demo':False,'reads':0,'hold_confirm':False,'pending':None}

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
 if url.scheme=='blob':r.continue_();return
 if url.hostname!='shop.invalid':r.abort('blockedbyclient');return
 def reply(value,status=200):r.fulfill(status=status,content_type='application/json',body=json.dumps(value),headers={'Access-Control-Allow-Origin':'*'})
 if req.method=='OPTIONS':r.fulfill(status=204,headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'});return
 if path=='/readyz':reply({'status':'ready'});return
 if path==f'/shops/{shop}':reply({'id':shop,'currency':'USD'});return
 if path.endswith('/summary'):reply(None);return
 if path.endswith('/products'):
  state['reads']+=1
  if state['demo']:reply({'detail':'Synthetic catalogue unavailable'},503);return
  reply(products);return
 if path.endswith('/cost-corrections'):
  state['posts'].append((path,req.post_data_json))
  state['draft']={**req.post_data_json,'id':'cost-draft','shop_id':shop,'product_id':'cola','status':'draft','created_at':'2026-11-02T18:00:00Z','confirmed_at':None}
  reply(state['draft'],201);return
 if path.endswith('/cost-corrections/cost-draft/confirm'):
  if state['hold_confirm']:
   state['posts'].append((path,None));state['pending']=r;return
  state['posts'].append((path,None));state['draft'].update(status='confirmed',confirmed_at='2026-11-02T18:10:00Z')
  products[0]['unit_cost_micros']=state['draft']['unit_cost_micros'];reply(state['draft']);return
 if req.method=='POST':state['posts'].append((path,req.post_data))
 reply([])

try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='msedge',headless=True,timeout=20000,args=['--disable-gpu'])
  context=browser.new_context(viewport={'width':390,'height':844},service_workers='block');context.route('**/*',route)
  context.add_init_script("""localStorage.setItem('street-ceo-api-config',JSON.stringify({baseUrl:'http://shop.invalid',shopId:'00000000-0000-0000-0000-000000000001'}));localStorage.setItem('street-ceo-hands-free-v1','off');""")
  page=context.new_page();page.set_default_timeout(10000);page.set_default_navigation_timeout(30000)
  page_errors=[]
  page.on('pageerror',lambda error:page_errors.append(str(error)))
  page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='domcontentloaded')
  page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Stock').click()
  catalog=page.locator('.stock-catalog-page');table=catalog.locator('.stock-catalog-table');panel=catalog.locator('.stock-product-panel')
  expect(table.locator('tbody tr')).to_have_count(4)
  expect(table.get_by_role('columnheader',name='Sell price')).to_contain_text('USD')
  expect(table.locator('.stock-quantity-badge')).to_have_count(2)
  expect(table.locator('tbody tr').filter(has_text='SOAP-ZERO')).to_contain_text('Out')
  for width in (390,320):
   page.set_viewport_size({'width':width,'height':844});page.evaluate("window.scrollTo({top:0,behavior:'instant'})");page.wait_for_function('window.scrollY===0')
   dims=page.evaluate('({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})');assert dims['client']==dims['scroll'],dims
   bulk=table.locator('tbody tr').filter(has_text='BULK-100')
   expect(bulk.locator('td').nth(1)).to_contain_text('10000000');expect(bulk.locator('td').last).to_have_text('750000.00')
   for cell in (bulk.locator('td').nth(1).locator('strong'),bulk.locator('td').last):
    assert cell.evaluate("el=>{const r=document.createRange();r.selectNodeContents(el);return r.getClientRects().length}")==1,'Numeric stock values must remain whole'
   page.screenshot(path=str(out/f'stock-top-{width}.png'))
   page.screenshot(path=str(out/f'stock-full-{width}.png'),full_page=True)
  page.set_viewport_size({'width':390,'height':844})
  search=catalog.get_by_role('searchbox',name='Search stock',exact=True)
  search.fill('bread-700');expect(table.locator('tbody tr')).to_have_count(1)
  expect(table.locator('tbody')).to_contain_text('deliberately very long')
  search.fill('cOcA');expect(table.locator('tbody tr')).to_have_count(1)
  search.fill('not-present');expect(catalog).to_contain_text('No matching products.')
  catalog.get_by_role('button',name='Clear search',exact=True).click();expect(search).to_be_focused();expect(table.locator('tbody tr')).to_have_count(4)
  cola=table.get_by_role('button',name='Coca-Cola 300ml COKE-300',exact=True)
  cola.focus();cola.press('Enter');expect(panel.get_by_role('heading',name='Coca-Cola 300ml',exact=True)).to_be_visible();expect(panel).to_be_focused()
  assert not state['posts']
  panel.press('Escape');expect(panel).to_have_count(0);expect(cola).to_be_focused()
  cola.press('Space');expect(panel).to_be_visible();panel.get_by_role('button',name='Close product details',exact=True).click();expect(cola).to_be_focused()
  table.locator('tbody tr').filter(has_text='BREAD-700').locator('td').last.click()
  expect(panel).to_contain_text('Bread loaf with a deliberately very long catalogue label')
  panel.get_by_role('button',name='Close product details',exact=True).click()
  cola.click();expect(panel).to_contain_text('USD 1.50');expect(panel).to_contain_text('USD 1.000000')
  for width in (390,320):
   page.set_viewport_size({'width':width,'height':844});panel.scroll_into_view_if_needed()
   dims=page.evaluate('({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})');assert dims['client']==dims['scroll'],dims
   page.screenshot(path=str(out/f'details-{width}.png'),full_page=True)
  panel.locator('.product-image-control summary').click()
  image=io.BytesIO();Image.new('RGB',(2,2),'green').save(image,format='PNG')
  panel.locator('input[type=file]').set_input_files({'name':'synthetic.png','mimeType':'image/png','buffer':image.getvalue()})
  expect(panel.get_by_text('Local preview · synthetic.png')).to_be_visible()
  expect(panel.get_by_role('button',name='Upload product image',exact=True)).to_be_enabled()
  assert not state['posts'],'Row taps and local image preview must not mutate API'
  panel.get_by_role('button',name='Edit recorded cost',exact=True).click()
  expect(panel.locator('.product-cost-editor')).to_have_count(1);expect(panel.locator('form')).to_have_count(1)
  def fill_cost(amount):
   panel.get_by_label('Cost per base unit (shop currency)',exact=True).fill(amount)
   panel.get_by_label('Effective date',exact=True).fill('2026-11-02')
   panel.get_by_label('Reason for correction',exact=True).fill('Synthetic review')
   panel.get_by_label('Source document or reference',exact=True).fill('QA source')
   panel.get_by_label('Recorded by',exact=True).fill('QA recorder')
   panel.get_by_role('button',name='Save cost draft for review',exact=True).click()
   try:expect(panel.get_by_role('button',name='Confirm cost correction',exact=True)).to_be_disabled()
   except AssertionError:
    print('Cost fixture diagnostics:',json.dumps(state['posts']),json.dumps(panel.inner_text(),ensure_ascii=True),flush=True)
    raise
   expect(panel.locator('.product-cost-editor')).to_have_count(1);expect(panel.locator('form')).to_have_count(0)
   expect(panel.get_by_text('Local preview · synthetic.png')).to_have_count(1)
  fill_cost('2.000000');assert products[0]['unit_cost_micros']==1000000
  panel.get_by_role('checkbox').check();panel.get_by_role('button',name='Confirm cost correction',exact=True).click()
  expect(panel).to_contain_text('Cost correction confirmed by the backend')
  expect(panel.locator('.product-cost-editor')).to_have_count(1);expect(panel.locator('form')).to_have_count(0)
  expect(panel.get_by_text('Local preview · synthetic.png')).to_be_visible()
  expect(panel.locator('.stock-product-cost')).to_contain_text('USD 2.000000')
  expect(panel.locator('.stock-product-numbers')).to_contain_text('18')
  assert products[0]['stock_qty']==18 and len(state['posts'])==2
  panel.get_by_role('button',name='Close cost editor',exact=True).click()
  panel.get_by_role('button',name='Receive a purchase',exact=True).click()
  expect(page.locator('.stock-catalog-page')).to_have_count(0)
  page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Stock').click()
  catalog.get_by_role('button',name='Stock count',exact=False).click();expect(page.locator('.stock-count-page')).to_be_visible()
  page.get_by_role('button',name='Back to Stock',exact=False).click()
  cola.click();panel.get_by_role('button',name='Edit recorded cost',exact=True).click();fill_cost('3.000000')
  panel.get_by_role('checkbox').check();state['hold_confirm']=True
  panel.get_by_role('button',name='Confirm cost correction',exact=True).click()
  expect(panel.locator('.product-cost-editor')).to_have_count(1)
  expect(panel.get_by_role('button',name='Close product details',exact=True)).to_be_disabled()
  expect(page.get_by_role('button',name='Go to Street CEO home',exact=True)).to_be_disabled()
  expect(page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Sell')).to_be_disabled()
  if page.get_by_role('button',name='Open Profile',exact=True).count():expect(page.get_by_role('button',name='Open Profile',exact=True)).to_be_disabled()
  assert state['pending'] is not None
  state['pending'].abort('failed');state['pending']=None
  expect(panel).to_contain_text('Cost request outcome is uncertain')
  expect(panel.locator('.product-cost-editor')).to_have_count(1)
  expect(panel.get_by_role('button',name='Confirm cost correction',exact=True)).to_be_disabled()
  expect(panel.get_by_role('button',name='Close product details',exact=True)).to_be_disabled()
  panel.get_by_role('button',name='Refresh cost audit',exact=True).click()
  expect(panel).to_contain_text('Cost request outcome is uncertain')
  assert len(state['posts'])==4,'No automatic replay after unknown cost response'
  state['demo']=True
  page.reload(wait_until='domcontentloaded')
  page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Stock').click()
  expect(catalog.locator('.stock-demo-note')).to_be_visible()
  table.locator('tbody tr').first.get_by_role('button').click()
  expect(panel.get_by_role('button',name='Edit recorded cost',exact=True)).to_be_disabled()
  panel.locator('.product-image-control summary').click()
  panel.locator('input[type=file]').set_input_files({'name':'demo-preview.png','mimeType':'image/png','buffer':image.getvalue()})
  expect(panel.get_by_role('button',name='Upload product image',exact=True)).to_be_disabled()
  assert len(state['posts'])==4
  assert not page_errors,page_errors
  print('DOM PASS: stocktable320390longnames/largeqtyprice/lowOut; nameSKUsearch/clear/empty; readonlyrow/Enter/Space/Esc/focus; localphotopreview noPOST; explicitcostdraftack/confirm selectedcostrefresh qtyunchanged; purchase/countlinks; pending+unknownmutationlocks/no replay; demoeditdisabled',flush=True)
  print(str(out),flush=True)
  browser.close()
finally:
 server.shutdown();server.server_close()
