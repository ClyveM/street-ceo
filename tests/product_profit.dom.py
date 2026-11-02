"""Sales/Profit UI with complete, loss, unknown and empty authoritative mock reports."""
import functools
import json
from datetime import date,timedelta
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright,expect

root=Path(__file__).resolve().parents[1];out=root/'data/qa-product-profit-20261102';out.mkdir(parents=True,exist_ok=True)
shop='00000000-0000-0000-0000-000000000001';today=date(2026,11,2)
state={'mode':'complete','queries':[],'posts':[]}

def product(name,revenue,cost,profit,margin):
 return {'product_id':name,'product_name':name,'sku':name.upper(),'label_source':'latest_receipt_snapshot','quantity_sold':1,
         'revenue_cents':revenue,'known_revenue_cents':revenue,'unknown_revenue_line_count':0,
         'cogs_micros':cost,'known_cogs_micros':cost or 0,'unknown_cogs_line_count':int(cost is None),
         'gross_profit_micros':profit,'margin_bps':margin}

def report(query):
 mode=state['mode'];preset=query.get('preset',['last1'])[0]
 start=today-timedelta(days=int(preset[4:])-1) if preset.startswith('last') else today
 rows=[product('Bread loaf',300,1000000,2000000,6667),product('Milk at a loss',100,2000000,-1000000,-10000),product('Soap',100,500000,500000,5000)]
 revenue,cost,profit,margin=500,3500000,1500000,3000
 if mode=='unknown':rows.append(product('Uncosted product',100,None,None,None));revenue,cost,profit,margin=600,None,None,None
 if mode=='loss':rows=[product('Loss-making product',100,3000000,-2000000,-20000)];revenue,cost,profit,margin=100,3000000,-2000000,-20000
 if mode=='tiny':rows=[product('Tiny loss',2,20001,-1,-1)];revenue,cost,profit,margin=2,20001,-1,-1
 if mode=='zero':rows=[product('Free product with cost',0,10000,-10000,None)];revenue,cost,profit,margin=0,10000,-10000,None
 if mode=='empty':rows=[];revenue,cost,profit,margin=0,0,0,None
 summary={'sales_total_cents':revenue,'transaction_count':len(rows),'cash_sales_cents':revenue,'bank_sales_cents':0,'other_tender_sales_cents':0,
          'cogs_micros':cost,'known_cogs_micros':sum(p['known_cogs_micros'] for p in rows),'missing_cogs_sale_count':int(cost is None),
          'unallocated_product_revenue_cents':0,'gross_profit_micros':profit,'margin_bps':margin}
 if mode=='invalid':summary['gross_profit_micros']=100
 return {'start_date':str(start),'end_date':str(today),'coverage_end_date':str(today),'coverage':'historical_or_selected_range',
         'as_of':'2026-11-02T18:00:00Z','shop_timezone':'Africa/Harare','currency':'USD','summary':summary,
         'monthly':[{'month':str(today)[:7],'sales_total_cents':revenue,'transaction_count':len(rows)}] if rows else [],
         'daily':[{'business_date':str(today),'sales_total_cents':revenue,'transaction_count':len(rows)}] if rows else [],
         'products':rows,'warnings':['Some saved receipt costs are unknown.'] if cost is None else [],'stock_reversal_count':0}

class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root/'apps/web/dist')))
Thread(target=server.serve_forever,daemon=True).start()
def route(r):
 req=r.request;url=urlparse(req.url)
 if url.hostname=='127.0.0.1' and url.port==server.server_port:r.continue_();return
 if url.hostname!='shop.invalid':r.abort('blockedbyclient');return
 headers={'Access-Control-Allow-Origin':'*'}
 if req.method=='OPTIONS':r.fulfill(status=204,headers={**headers,'Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'});return
 if req.method=='POST':state['posts'].append(url.path)
 value={'status':'ready'} if url.path=='/readyz' else {'id':shop} if url.path==f'/shops/{shop}' else []
 if url.path.endswith('/reports/sales'):
  query=parse_qs(url.query);state['queries'].append(query)
  if state['mode']=='error':r.fulfill(status=503,content_type='application/json',body='{"detail":"Test unavailable"}',headers=headers);return
  value=report(query)
 r.fulfill(status=200,content_type='application/json',body=json.dumps(value),headers=headers)

try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='msedge',headless=True,timeout=20000,args=['--disable-gpu'])
  context=browser.new_context(viewport={'width':390,'height':844});context.route('**/*',route)
  context.add_init_script("""localStorage.setItem('street-ceo-api-config',JSON.stringify({baseUrl:'http://shop.invalid',shopId:'00000000-0000-0000-0000-000000000001'}));localStorage.setItem('street-ceo-hands-free-v1','off');""")
  page=context.new_page();page.set_default_timeout(10000);page.set_default_navigation_timeout(30000)
  page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='domcontentloaded')
  page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Reports').click()
  reports=page.locator('.reports-page');expect(reports.locator('.report-hero')).to_contain_text('5.00')
  before=len(state['queries']);reports.get_by_role('button',name='Profit',exact=True).click()
  expect(reports.get_by_role('button',name='Profit',exact=True)).to_have_attribute('aria-pressed','true')
  expect(reports.locator('.report-profit-hero')).to_contain_text('USD 1.50')
  expect(reports.locator('.report-profit-hero')).to_contain_text('30.00%')
  expect(reports).to_contain_text('before shop expenses')
  assert len(state['queries'])==before,'View switch must use same verified report'
  expect(reports.locator('.report-profit-products li').first).to_contain_text('Bread loaf')
  expect(reports.locator('.report-product-loss')).to_contain_text('USD -1.00')
  for width in (390,320):
   page.set_viewport_size({'width':width,'height':844});page.evaluate("window.scrollTo({top:0,behavior:'instant'})");page.wait_for_function('window.scrollY===0')
   dims=page.evaluate('({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})');assert dims['client']==dims['scroll'],dims
   assert reports.locator('.report-profit-hero .report-hero-count strong').evaluate("el=>{const r=document.createRange();r.selectNodeContents(el);return r.getClientRects().length}")==1,'Ordinary margin must remain on one line'
   page.screenshot(path=str(out/f'profit-complete-top-{width}.png'))
   page.screenshot(path=str(out/f'profit-complete-full-{width}.png'),full_page=True)
  page.set_viewport_size({'width':390,'height':844})
  reports.get_by_role('button',name='20 days',exact=True).click();expect(reports.locator('.report-profit-hero')).to_contain_text('USD 1.50')
  assert state['queries'][-1]=={'preset':['last20']}
  def load(mode):
   state['mode']=mode
   reports.get_by_role('button',name='Refresh sales report',exact=True).click()
  load('loss');expect(reports.locator('.report-profit-hero')).to_contain_text('Gross loss');expect(reports.locator('.report-profit-hero')).to_contain_text('-200.00%')
  for width in (390,320):
   page.set_viewport_size({'width':width,'height':844});page.evaluate("window.scrollTo({top:0,behavior:'instant'})");page.wait_for_function('window.scrollY===0')
   assert reports.locator('.report-profit-hero .report-hero-count strong').evaluate("el=>{const r=document.createRange();r.selectNodeContents(el);return r.getClientRects().length}")==1,'Negative margin must remain on one line'
   page.screenshot(path=str(out/f'profit-loss-top-{width}.png'))
  page.set_viewport_size({'width':390,'height':844})
  load('tiny');expect(reports.locator('.report-profit-hero')).to_contain_text('Loss < USD 0.01')
  load('zero');expect(reports.locator('.report-profit-hero')).to_contain_text('Not defined');expect(reports.locator('.report-profit-products')).to_contain_text('USD -0.01')
  load('unknown');expect(reports.locator('.report-profit-hero')).to_contain_text('Incomplete');expect(reports.locator('.report-profit-products li').last).to_contain_text('Uncosted product')
  expect(reports.locator('.report-profit-products li').first).to_contain_text('Bread loaf');expect(reports.locator('.report-cost-notice')).to_be_visible()
  page.evaluate("window.scrollTo({top:0,behavior:'instant'})");page.screenshot(path=str(out/'profit-unknown-top-390.png'))
  load('empty');expect(reports.locator('.report-profit-hero')).to_contain_text('USD 0.00');expect(reports.locator('.report-profit-hero')).to_contain_text('Not defined')
  expect(reports.locator('.report-empty')).to_contain_text('No product sales')
  load('error');expect(reports.get_by_role('alert')).to_be_visible();expect(reports.locator('.report-profit-hero')).to_have_count(0)
  state['mode']='invalid';reports.get_by_role('button',name='Try again',exact=True).click();expect(reports.get_by_role('alert')).to_be_visible();expect(reports.locator('.report-profit-hero')).to_have_count(0)
  state['mode']='complete';reports.get_by_role('button',name='Try again',exact=True).click();expect(reports.locator('.report-profit-hero')).to_contain_text('USD 1.50')
  reports.get_by_role('button',name='Sales',exact=True).click();expect(reports.get_by_role('heading',name='Sales by product',exact=True)).to_be_visible()
  expect(reports.get_by_role('heading',name='Profit by product',exact=True)).to_have_count(0)
  assert not state['posts'],state['posts']
  print('DOM PASS: sameverifiedreport Sales/Profit, gross-before-expenses, exactknown/negative<-100/tinyLoss/zeroRevenue/unknownunranked/empty/error/invalidarithmetic, periodchange,320390bounds+screens; no APIposts',flush=True)
  print(str(out),flush=True);browser.close()
finally:
 server.shutdown();server.server_close()
