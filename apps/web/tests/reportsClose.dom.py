"""Isolated built-app DOM/fake-native acceptance; no live API or physical microphone.
Run after npm run build. Requires local Playwright + Microsoft Edge.
"""
import functools
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright, expect

web=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(web/'dist')))
Thread(target=server.serve_forever,daemon=True).start()
shop='00000000-0000-0000-0000-000000000001'; date='2026-11-02'; version='a'*64
state={'opening':False,'posts':[],'voice_calls':0,'reports':[]}
preview={'business_date':date,'shop_timezone':'Africa/Harare','opening_cash_cents':None,'opening_source':'missing','requires_opening':True,'requires_payment_review':False,'expected_cash_cents':None,'sales_cash_cents':150,'paid_expenses_cash_cents':0,'paid_purchases_cash_cents':0,'refunds_cash_cents':0,'adjustments_cash_cents':0,'preview_version':version,'warnings':['Bank not counted'],'saved_close':None}
def route(request_route):
    req=request_route.request;parsed=urlparse(req.url);path=parsed.path
    def reply(value,status=200):request_route.fulfill(status=status,content_type='application/json',body=json.dumps(value),headers={'Access-Control-Allow-Origin':'*'})
    if req.method=='OPTIONS':request_route.fulfill(status=204,headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'});return
    if path=='/readyz':reply({'status':'ready'});return
    if path==f'/shops/{shop}':reply({'id':shop});return
    if path.endswith('/products'):reply([{'id':'00000000-0000-0000-0000-000000000002','shop_id':shop,'sku':'COKE','name':'Coke','unit_price_cents':150,'stock_qty':10,'unit_cost_micros':1000000}]);return
    if path.endswith('/summary'):reply(None);return
    if path.endswith('/sales') and '/reports/' not in path:reply([]);return
    if path.endswith('/voice/transcript'):
        state['voice_calls']+=1
        reply({'request_id':'review-next','shop_id':shop,'transcript':req.post_data_json['transcript'],'status':'needs_confirmation','intent':{'action':'record_sale','needs_confirmation':True},'lines':[{'product_id':'00000000-0000-0000-0000-000000000002','product_name':'Coke','quantity':1}],'requires_match_confirmation':False,'resolution_source':'catalogue_parser','provider_called':False});return
    if path.endswith('/voice/commit'):
        assert req.post_data_json.get('tender') is None, 'Simulated next sale must never receive paid tender'
        reply({'status':'needs_tender','review_id':'review-next','question':'Cash or Bank?','amount_due_cents':150,'allowed_tenders':['cash','bank'],'missing':['tender']});return
    if path.endswith('/cash-close/preview'):
        value={**preview}
        if state['opening']:value.update(opening_cash_cents=0,opening_source='explicit_opening',requires_opening=False,expected_cash_cents=150)
        reply(value);return
    if path.endswith('/cash-close/opening'):
        data=req.post_data_json;state['opening']=True;state['posts'].append((path,req.headers.get('idempotency-key'),data))
        reply({'id':'opening-1','shop_id':shop,'kind':'opening_balance','tender':'cash','amount_cents':data['opening_cash_cents'],'actor':data['actor'],'reason':'Explicit late start-of-day opening declaration: '+data['reason'],'occurred_at':'2026-11-01T22:00:00Z','created_at':'2026-11-02T17:00:00Z'},201);return
    if path.endswith('/cash-close'):
        data=req.post_data_json;state['posts'].append((path,req.headers.get('idempotency-key'),data))
        count=sum(1 for p in state['posts'] if p[0].endswith('/cash-close'))
        if count==1:reply({'detail':'trace persistence failed'},503);return
        reply({**preview,'opening_cash_cents':0,'requires_opening':False,'opening_source':'explicit_opening','expected_cash_cents':150,'id':'close-1','audit_id':'audit-1','shop_id':shop,'cash_counted_cents':data['cash_counted_cents'],'cash_variance_cents':data['cash_counted_cents']-150,'bank_card_counted_cents':None,'bank_card_variance_cents':None,'bank_status':'not_counted','source_version':version,'confirmed_at':'2026-11-02T17:00:00Z'},201);return
    if path.endswith('/reports/sales'):
        query=parse_qs(parsed.query);state['reports'].append(query);start=query.get('start_date',['2026-10-14'])[0];end=query.get('end_date',[date])[0]
        reply({'start_date':start,'end_date':end,'shop_timezone':'Africa/Harare','currency':'USD','coverage':'current_month_to_date','coverage_end_date':date,'as_of':'2026-11-02T17:00:00Z','summary':{'sales_total_cents':150,'transaction_count':1,'cash_sales_cents':150,'bank_sales_cents':0,'other_tender_sales_cents':0,'cogs_micros':None,'missing_cogs_sale_count':1},'daily':[{'business_date':date,'sales_total_cents':150,'transaction_count':1}],'monthly':[{'month':'2026-11','sales_total_cents':150,'transaction_count':1}],'products':[{'product_id':'old-product','product_name':'old-product','sku':None,'label_source':'product_id','quantity_sold':1,'revenue_cents':None,'known_revenue_cents':0,'unknown_revenue_line_count':1}],'stock_reversal_count':1,'warnings':['Legacy multi-product revenue is incomplete']});return
    reply({'detail':'mock route unavailable'},404)
try:
 with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,timeout=20000,args=['--disable-gpu'])
    context=browser.new_context(viewport={'width':390,'height':844})
    def safe_route(r):
        target=urlparse(r.request.url)
        if target.hostname=='shop.invalid':route(r)
        elif target.hostname=='127.0.0.1' and target.port==server.server_port:r.continue_()
        else:r.abort('blockedbyclient')
    context.route('**/*',safe_route)
    context.add_init_script("""localStorage.setItem('street-ceo-api-config',JSON.stringify({baseUrl:'http://shop.invalid',shopId:'00000000-0000-0000-0000-000000000001'}));
    window.__listeners={};window.__prompts=[];
    window.__emit=(name,data={})=>{for(const fn of [...(window.__listeners[name]||[])])fn(data)};
    const plugin={async addListener(name,fn){(window.__listeners[name]??=new Set()).add(fn);return{async remove(){window.__listeners[name].delete(fn)}}},async start(){setTimeout(()=>window.__emit('speechReady'),10)},async stop(){},async speak({text}){window.__prompts.push(text);await new Promise(resolve=>setTimeout(resolve,25))},async stopSpeaking(){}};
    window.Capacitor={getPlatform:()=> 'android',registerPlugin:()=>plugin};""")
    page=context.new_page();page.set_default_timeout(10000)
    page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='domcontentloaded')
    def say(text):
        page.wait_for_function("document.querySelector('.hands-free .voice-live-state strong')?.textContent !== 'Microphone starting'")
        # The modal readiness event is the authoritative gate after each TTS turn.
        if page.get_by_role('dialog').count():expect(page.locator('[role=dialog] [data-listening-state]')).to_have_attribute('data-listening-state','listening')
        else:page.wait_for_function("document.querySelector('.hands-free .voice-live-state strong')?.textContent.includes('Ready')")
        page.evaluate("text=>window.__emit('speech',{text,final:true})",text)
    say('End my day')
    dialog=page.get_by_role('dialog',name='End my day cash check');expect(dialog).to_be_visible();expect(dialog.locator('.close-question')).to_contain_text('cash do you have')
    say('one dollar');expect(dialog.locator('.close-question')).to_contain_text('start of this business day')
    assert not state['posts']
    say('zero');expect(dialog.locator('.close-question')).to_contain_text('Record opening cash 0.00')
    assert not state['posts']
    say('Yes');expect(dialog.locator('.close-question')).to_contain_text('Short 0.50');assert len(state['posts'])==1
    say('Yes');expect(dialog).to_contain_text('Outcome unconfirmed')
    say('Cancel');expect(dialog).to_be_visible();assert sum(1 for p in state['posts'] if p[0].endswith('/cash-close'))==1
    say('Retry');expect(dialog).to_contain_text('Cash close saved');expect(dialog).to_contain_text('Not counted / unknown')
    close_posts=[p for p in state['posts'] if p[0].endswith('/cash-close')];assert len(close_posts)==2 and close_posts[0]==close_posts[1]
    assert state['voice_calls']==0
    say('Done');expect(dialog).not_to_be_visible()
    say('Apo one Coke Napo')
    sale_dialog=page.get_by_role('dialog',name='Apo sale basket');expect(sale_dialog).to_be_visible()
    expect(sale_dialog).to_contain_text('Cash or Bank?');assert state['voice_calls']==1
    say('Cancel');expect(sale_dialog).not_to_be_visible()
    page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Reports').click()
    expect(page.get_by_role('heading',name='Sales reports',exact=True)).to_be_visible();expect(page.get_by_role('heading',name='Monthly totals')).to_be_visible();expect(page.locator('.report-products')).to_contain_text('Revenue incomplete')
    for width in (390,320):
        page.set_viewport_size({'width':width,'height':844});dims=page.evaluate('({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})');assert dims['client']==dims['scroll'],dims
    page.get_by_role('button',name='Skip stock count',exact=True).click();expect(page.get_by_role('button',name='Open stock count',exact=True)).not_to_be_visible()
    page.get_by_role('button',name='Review month',exact=True).click()
    page.get_by_role('button',name='Open stock count',exact=True).click()
    expect(page.get_by_role('button',name='Stock take',exact=True)).to_have_attribute('aria-pressed','true')
    print('DOM PASS: simulated ASR bare End my day; cash first; explicit zero opening and Yes; short 0.50; final Yes; 503 same-key Retry; unknown Cancel blocked; bank unknown; Done and next Apo; monthly/product reports; 390/320 bounds; optional Skip and Stock take tab',flush=True)
    browser.close()
finally:
 server.shutdown();server.server_close()
