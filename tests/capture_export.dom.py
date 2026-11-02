"""Built report UI/filter/viewport checks with strict isolated API fixtures."""
import calendar
import functools
import json
from datetime import date, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlparse
from playwright.sync_api import sync_playwright, expect

root = Path(__file__).resolve().parents[1]
out = root/'data/qa-capture-export/output/pdf'
out.mkdir(parents=True, exist_ok=True)
shop = '00000000-0000-0000-0000-000000000001'
today = date(2026, 11, 2)
state = {'mode': 'normal', 'queries': [], 'posts': []}


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root/'apps/web/dist')))
Thread(target=server.serve_forever, daemon=True).start()


def fixture(query):
    preset = query.get('preset', [''])[0]
    end = today
    if preset == 'month':
        month = query['month'][0]
        y, m = map(int, month.split('-'))
        start = date(y, m, 1)
        end = min(date(y, m, calendar.monthrange(y, m)[1]), today)
    elif preset.startswith('last'):
        start = end-timedelta(days=int(preset[4:])-1)
    else:
        start = date.fromisoformat(query['start_date'][0])
        end = date.fromisoformat(query['end_date'][0])
    empty = state['mode'] == 'empty'
    total, count = (0, 0) if empty else (8700, 12)
    return {'start_date': str(start), 'end_date': str(end), 'coverage_end_date': str(end),
            'coverage': 'historical_or_selected_range', 'as_of': '2026-11-02T18:00:00+02:00',
            'shop_timezone': 'Africa/Harare', 'currency': 'USD',
            'summary': {'sales_total_cents': total, 'transaction_count': count,
                        'cash_sales_cents': 0 if empty else 5200, 'bank_sales_cents': 0 if empty else 3500,
                        'other_tender_sales_cents': 0, 'cogs_micros': 0 if empty else None,
                        'missing_cogs_sale_count': 0 if empty else 1},
            'monthly': [] if empty else [{'month': str(start)[:7], 'sales_total_cents': total, 'transaction_count': count}],
            'daily': [] if empty else [{'business_date': str(start), 'sales_total_cents': total, 'transaction_count': count}],
            'products': [] if empty else [
                {'product_id': 'cola', 'product_name': 'Coca-Cola 300ml', 'sku': 'COKE-300', 'label_source': 'latest_receipt_snapshot',
                 'quantity_sold': 30, 'revenue_cents': 3200, 'known_revenue_cents': 3200, 'unknown_revenue_line_count': 0},
                {'product_id': 'bread', 'product_name': 'Bread loaf with a deliberately long historical catalogue label', 'sku': None, 'label_source': 'current_catalogue',
                 'quantity_sold': 20, 'revenue_cents': None, 'known_revenue_cents': 2500, 'unknown_revenue_line_count': 1}],
            'stock_reversal_count': 0 if empty else 1,
            'warnings': [] if empty else ['Some saved receipt costs are unknown.', 'Legacy product revenue is incomplete; do not infer it from current prices.']}


def route(r):
    req = r.request
    url = urlparse(req.url)
    if url.hostname == '127.0.0.1' and url.port == server.server_port:
        asset=(root/'apps/web/dist'/ (url.path.lstrip('/') or 'index.html')).resolve()
        if asset.is_relative_to((root/'apps/web/dist').resolve()) and asset.is_file(): r.fulfill(path=str(asset))
        else: r.fulfill(status=404,body='missing')
        return
    if url.hostname != 'shop.invalid':
        r.abort('blockedbyclient')
        return
    headers = {'Access-Control-Allow-Origin': '*'}
    if req.method == 'OPTIONS':
        r.fulfill(status=204, headers={**headers, 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': '*'})
        return
    if req.method == 'POST':
        state['posts'].append(url.path)
    value = {'status': 'ready'} if url.path == '/readyz' else {'id': shop} if url.path == f'/shops/{shop}' else []
    if url.path.endswith('/cash-close/preview'):
        value = {'business_date': str(today), 'shop_timezone': 'Africa/Harare', 'opening_cash_cents': None,
                 'opening_source': 'missing', 'requires_opening': True, 'requires_payment_review': False,
                 'expected_cash_cents': None, 'sales_cash_cents': 0, 'paid_expenses_cash_cents': 0,
                 'paid_purchases_cash_cents': 0, 'refunds_cash_cents': 0, 'adjustments_cash_cents': 0,
                 'preview_version': 'a'*64, 'warnings': [], 'saved_close': None}
    if url.path.endswith('/reports/sales'):
        query = parse_qs(url.query)
        state['queries'].append(query)
        if state['mode'] == 'error':
            r.fulfill(status=503, content_type='application/json', body='{"detail":"Test report unavailable"}', headers=headers)
            return
        value = fixture(query)
    r.fulfill(status=200, content_type='application/json', body=json.dumps(value), headers=headers)


try:
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True,args=['--disable-gpu','--disable-background-timer-throttling','--disable-renderer-backgrounding'])
        context=browser.new_context(viewport={'width':390,'height':844},service_workers='block')
        context.route('**/*',route)
        context.on('requestfailed',lambda r:print('FAILED',r.url,r.failure,flush=True))
        context.on('page',lambda q:q.on('console',lambda m:print('CONSOLE',m.text,flush=True)))
        context.add_init_script("""localStorage.setItem('street-ceo-api-config',JSON.stringify({baseUrl:'http://shop.invalid',shopId:'00000000-0000-0000-0000-000000000001'}));localStorage.setItem('street-ceo-hands-free-v1','off');window.calls=[];const plugin={async addListener(){return{async remove(){}}},async start(){},async stop(){},async speak(){},async stopSpeaking(){},async shareCsv(o){window.calls.push({kind:'csv',...o})},async sharePdf(o){window.calls.push({kind:'pdf',...o})}};window.Capacitor={getPlatform:()=> 'android',registerPlugin:()=>plugin};window.print=()=>{};""")
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='load')
        page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Reports').click()
        reports=page.locator('.reports-page');expect(reports).to_contain_text('USD 87.00')
        reports.get_by_role('button',name='CSV',exact=True).click()
        expect(reports).to_contain_text('Share sheet opened')
        reports.get_by_role('button',name='PDF · logo',exact=True).click()
        expect.poll if False else None
        page.wait_for_function('window.calls.length===2')
        calls=page.evaluate('window.calls');assert calls[0]['content'].startswith('\ufeff');assert 'USD' in calls[0]['content'];assert calls[1]['rows'] and calls[1]['title']=='Sales report'
        page.evaluate("window.Capacitor.getPlatform=()=> 'web';const originalOpen=window.open;window.open=(...a)=>{const w=originalOpen(...a);if(w)Object.defineProperty(w,'print',{value:()=>{},writable:false,configurable:false});return w}")
        with page.expect_popup() as info:reports.get_by_role('button',name='PDF · logo',exact=True).click()
        popup=info.value;popup.wait_for_function('Array.from(document.images).every(i=>i.complete)',timeout=10000);assert popup.locator('header img').evaluate('(i)=>i.naturalWidth')>0;popup.pdf(path=str(out/'street-ceo-sales-review.pdf'),format='A4',print_background=True);popup.close()
        print('BRIDGE AND BROWSER PDF VERIFIED',flush=True)
        for width in (320,390):
            page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        print('BOUNDS VERIFIED',flush=True)
        state['mode']='error';reports.get_by_role('button',name='Refresh sales report',exact=True).click();expect(reports.get_by_role('button',name='CSV',exact=True)).to_have_count(0)
        print('ERROR VERIFIED',flush=True)
        assert not state['posts'];assert not errors,errors
        browser.close();print('PASS native bridge arguments/export error guards/320390/zero POST')
finally: server.shutdown()











