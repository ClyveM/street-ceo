"""Standalone stock count page using isolated fixture mutations, never a live shop."""
import functools
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

root=Path(__file__).resolve().parents[1]
out=root/'data/qa-stock-count-history-20261102'
out.mkdir(parents=True,exist_ok=True)
shop='00000000-0000-0000-0000-000000000001'
p1='00000000-0000-0000-0000-000000000001'
p2='00000000-0000-0000-0000-000000000002'
products=[{'id':p1,'shop_id':shop,'name':'Coca-Cola 300ml','sku':'COKE-300','unit_price_cents':150,'stock_qty':18,'unit_cost_micros':1000000},
          {'id':p2,'shop_id':shop,'name':'Bread loaf','sku':'BREAD-700','unit_price_cents':180,'stock_qty':11,'unit_cost_micros':1200000}]
state={'counts':{},'posts':[],'history_error':False,'detail_error':False,'fail_confirm':False,'history_reads':0,'product_reads':0}

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
    def reply(value,status=200):r.fulfill(status=status,content_type='application/json',body=json.dumps(value),headers={'Access-Control-Allow-Origin':'*'})
    if req.method=='OPTIONS':r.fulfill(status=204,headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'});return
    if path=='/readyz':reply({'status':'ready'});return
    if path==f'/shops/{shop}':reply({'id':shop});return
    if path.endswith('/products'):state['product_reads']+=1;reply(products);return
    if path.endswith('/reports/sales'):
        start='2026-11-01' if 'preset=month' in url.query else '2026-11-02'
        reply({'start_date':start,'end_date':'2026-11-02','coverage_end_date':'2026-11-02','coverage':'historical_or_selected_range',
               'as_of':'2026-11-02T18:00:00Z','shop_timezone':'Africa/Harare','currency':'USD',
               'summary':{'sales_total_cents':0,'transaction_count':0,'cash_sales_cents':0,'bank_sales_cents':0,'other_tender_sales_cents':0,'cogs_micros':0,'missing_cogs_sale_count':0},
               'monthly':[],'daily':[],'products':[],'warnings':[],'stock_reversal_count':0});return
    if path.endswith('/stock-takes'):
        if req.method=='GET':
            state['history_reads']+=1
            if state['history_error']:reply({'detail':'Test history unavailable'},503);return
            reply(sorted(state['counts'].values(),key=lambda x:x['created_at'],reverse=True));return
        body=req.post_data_json;state['posts'].append((path,body));key=f"count-{len(state['counts'])+1}"
        record={**body,'id':key,'shop_id':shop,'status':'draft','created_at':f"2026-11-02T18:00:0{len(state['counts'])}Z",'confirmed_at':None,
                'expected_snapshot':{line['product_id']:next(p['stock_qty'] for p in products if p['id']==line['product_id']) for line in body['lines']}}
        state['counts'][key]=record;reply(record,201);return
    if '/stock-takes/' in path:
        key=path.split('/stock-takes/')[1].split('/')[0];record=state['counts'][key]
        if req.method=='GET':
            if state['detail_error']:reply({'detail':'Test detail unavailable'},503);return
            reply(record);return
        state['posts'].append((path,req.post_data_json));adjustments=[]
        for line in record['lines']:
            expected=record['expected_snapshot'][line['product_id']]
            if line['counted_qty']!=expected:
                adjustments.append({'id':f"audit-{key}",'stock_take_id':key,'shop_id':shop,'product_id':line['product_id'],
                                    'expected_qty':expected,'counted_qty':line['counted_qty'],'adjustment_qty':line['counted_qty']-expected,
                                    'actor':record['actor'],'reason':'confirmed on-demand count','recorded_at':'2026-11-02T18:10:00Z'})
            next(p for p in products if p['id']==line['product_id'])['stock_qty']=line['counted_qty']
        record.update(status='confirmed',confirmed_at='2026-11-02T18:10:00Z')
        if state['fail_confirm']:state['fail_confirm']=False;reply({'detail':'Test lost confirmation response'},503);return
        reply({'stock_take_id':key,'shop_id':shop,'status':'confirmed','adjustments':adjustments,'confirmed_at':record['confirmed_at']});return
    reply([])

try:
 with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,timeout=20000,args=['--disable-gpu'])
    context=browser.new_context(viewport={'width':390,'height':844},service_workers='block')
    context.route('**/*',route)
    context.add_init_script("""localStorage.setItem('street-ceo-api-config',JSON.stringify({baseUrl:'http://shop.invalid',shopId:'00000000-0000-0000-0000-000000000001'}));localStorage.setItem('street-ceo-hands-free-v1','off');const plugin={async addListener(){return{async remove(){}}},async start(){},async stop(){},async speak(){},async stopSpeaking(){}};window.Capacitor={getPlatform:()=> 'android',registerPlugin:()=>plugin};""")
    page=context.new_page();page.set_default_timeout(10000);page.set_default_navigation_timeout(30000)
    page.on('pageerror',lambda error:print('Mock-page JavaScript error:',str(error),flush=True))
    page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='domcontentloaded')
    page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Stock').click()
    page.get_by_role('button',name='Stock count →',exact=True).click()
    count=page.locator('.stock-count-page');history=count.locator('.stock-count-history')
    expect(count.get_by_role('heading',name='Stock count',exact=True)).to_be_visible()
    expect(history).to_contain_text('No saved stock counts yet')
    page.screenshot(path=str(out/'empty-390.png'),full_page=True)
    def start(value,actor='QA count'):
        count.get_by_role('button',name='Start stock count',exact=True).click()
        count.get_by_label('Count date',exact=True).fill('2026-11-02')
        count.get_by_label('Counted by',exact=True).fill(actor)
        count.get_by_label('Count notes / explanation',exact=True).fill('Synthetic physical count')
        expect(count.get_by_role('spinbutton',name='Counted units for Bread loaf',exact=True)).to_have_value('')
        count.get_by_role('spinbutton',name='Counted units for Coca-Cola 300ml',exact=True).fill(str(value))
        count.get_by_role('button',name='Save count draft for review',exact=True).click()
        expect(count.get_by_role('heading',name='Review stock count',exact=True)).to_be_visible()
        expect(count.get_by_role('button',name='Confirm reviewed stock adjustments',exact=True)).to_be_disabled()
        assert len(state['posts'][-1][1]['lines'])==1,'Blank second product must not become zero'
    start(16)
    expect(history).to_contain_text('Draft')
    count.get_by_role('button',name='Close count',exact=True).click()
    history.get_by_role('button',name='Open draft stock count').click()
    expect(count.get_by_role('checkbox')).not_to_be_checked()
    count.get_by_role('checkbox').check()
    count.get_by_role('button',name='Confirm reviewed stock adjustments',exact=True).click()
    expect(count).to_contain_text('Count confirmed by service')
    expect(history.get_by_role('button',name='Open confirmed stock count')).to_be_visible()
    assert products[0]['stock_qty']==16 and products[1]['stock_qty']==11
    count.get_by_role('button',name='Close count',exact=True).click()
    history.get_by_role('button',name='Open confirmed stock count').click()
    expect(count.get_by_role('heading',name='Saved stock count',exact=True)).to_be_visible()
    expect(count.get_by_role('button',name='Confirm reviewed stock adjustments',exact=True)).to_have_count(0)
    for width in (390,320):
        page.set_viewport_size({'width':width,'height':844})
        dimensions=page.evaluate('({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})')
        assert dimensions['client']==dimensions['scroll'],dimensions
        page.screenshot(path=str(out/f'confirmed-{width}.png'),full_page=True)
    count.get_by_role('button',name='Close count',exact=True).click()
    start(0,'QA recovery')
    count.get_by_role('checkbox').check();state['fail_confirm']=True;reads=state['product_reads']
    count.get_by_role('button',name='Confirm reviewed stock adjustments',exact=True).click()
    expect(count).to_contain_text('Outcome unconfirmed or baseline changed')
    expect(count.get_by_role('button',name='Start stock count',exact=True)).to_be_disabled()
    expect(page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Sell')).to_be_disabled()
    expect(page.get_by_role('button',name='Go to Street CEO home',exact=True)).to_be_disabled()
    page.locator('.shop-connection-check').click()
    expect(count).to_be_visible()
    expect(count.get_by_role('button',name='Confirm reviewed stock adjustments',exact=True)).to_be_disabled()
    assert len(state['posts'])==4
    count.get_by_role('button',name='Reload saved count',exact=True).click()
    expect(count.get_by_role('heading',name='Saved stock count',exact=True)).to_be_visible()
    expect(history.get_by_role('button',name='Open confirmed stock count')).to_have_count(2)
    expect(count.get_by_role('button',name='Start stock count',exact=True)).to_be_enabled()
    expect(page.get_by_role('button',name='Go to Street CEO home',exact=True)).to_be_enabled()
    assert state['product_reads']>reads,'Confirmed recovery must refresh current catalogue'
    assert products[0]['stock_qty']==0 and len(state['posts'])==4
    count.get_by_role('button',name='Close count',exact=True).click()
    for width in (390,320):
        page.set_viewport_size({'width':width,'height':844})
        page.screenshot(path=str(out/f'history-{width}.png'),full_page=True)
    state['history_error']=True
    count.get_by_role('button',name='Refresh stock count history',exact=True).click()
    expect(history.get_by_role('alert')).to_be_visible()
    expect(history).not_to_contain_text('No saved stock counts yet')
    page.screenshot(path=str(out/'error-320.png'),full_page=True)
    state['history_error']=False
    history.get_by_role('button',name='Try again',exact=True).click()
    expect(history.get_by_role('button',name='Open confirmed stock count')).to_have_count(2)
    state['detail_error']=True
    history.get_by_role('button',name='Open confirmed stock count').first.click()
    expect(history.get_by_role('alert')).to_be_visible()
    expect(count.locator('.stock-count-active')).to_have_count(0)
    state['detail_error']=False
    history.get_by_role('button',name='Open confirmed stock count').first.click()
    expect(count.get_by_role('heading',name='Saved stock count',exact=True)).to_be_visible()
    count.get_by_role('button',name='Close count',exact=True).click()
    page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Reports').click()
    reports=page.locator('.reports-page')
    reports.get_by_role('button',name='Month',exact=True).click()
    reports.get_by_role('button',name='Open stock count',exact=True).click()
    expect(count.get_by_role('button',name='Start stock count',exact=True)).to_be_visible()
    expect(history.get_by_role('button',name='Open confirmed stock count')).to_have_count(2)
    for width in (390,320):
        page.set_viewport_size({'width':width,'height':844})
        page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
        page.wait_for_function('window.scrollY===0')
        page.screenshot(path=str(out/f'history-top-{width}.png'))
    assert len(state['posts'])==4
    print('DOM PASS: Stock and Reports links standalonepage; empty; blanknotzero; saved draftresume requiresack; confirmhistoryrefresh; confirmedreadonly; lostconfirm503 blocksnav/home/start/reconfirm and connectioncheck preservespage; GETrecoveryrefreshesproducts/history no repeatPOST/unlocks; 390/320bounds; history/detailerror notempty+Retry',flush=True)
    print(str(out),flush=True)
    browser.close()
finally:
 server.shutdown();server.server_close()
