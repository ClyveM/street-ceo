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
out = root/'data/qa-reports-polish-20261102'
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
        dist=(root/'apps/web/dist').resolve();asset=(dist/(url.path.lstrip('/') or 'index.html')).resolve()
        if asset.is_relative_to(dist) and asset.is_file():r.fulfill(path=str(asset))
        else:r.fulfill(status=404,body='Missing isolated fixture asset')
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
        browser = p.chromium.launch(channel='msedge', headless=True, timeout=20000, args=['--disable-gpu'])
        context = browser.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Africa/Harare', service_workers='block')
        context.route('**/*', route)
        context.add_init_script("""localStorage.setItem('street-ceo-api-config',JSON.stringify({baseUrl:'http://shop.invalid',shopId:'00000000-0000-0000-0000-000000000001'}));localStorage.setItem('street-ceo-hands-free-v1','off');
        const plugin={async addListener(){return{async remove(){}}},async start(){},async stop(){},async speak(){},async stopSpeaking(){}};window.Capacitor={getPlatform:()=> 'android',registerPlugin:()=>plugin};""")
        page = context.new_page()
        page.set_default_timeout(10000)
        page.set_default_navigation_timeout(30000)
        page.goto(f'http://127.0.0.1:{server.server_port}', wait_until='domcontentloaded')
        page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Reports').click()
        reports = page.locator('.reports-page')
        expect(reports.get_by_role('heading', name='Reports', exact=True)).to_be_visible()
        expect(page.locator('.welcome')).not_to_be_visible()
        expect(reports.locator('.reports-brand img')).to_have_count(0)
        expect(reports).to_contain_text('USD 87.00')
        assert state['queries'][-1] == {'preset': ['last1']}
        expect(reports.get_by_role('button', name='Today', exact=True)).to_have_attribute('aria-pressed', 'true')
        expect(reports.locator('.report-products')).to_contain_text('Incomplete')
        expect(reports.locator('.report-cost-notice')).to_be_visible()
        for width in (390, 320, 1280):
            page.set_viewport_size({'width': width, 'height': 844})
            dimensions = page.evaluate('({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})')
            assert dimensions['client'] == dimensions['scroll'], dimensions
            page.screenshot(path=str(out/f'reports-{width}.png'), full_page=True)
            page.evaluate('window.scrollTo(0,document.documentElement.scrollHeight)')
            last = reports.locator('.report-more').last.bounding_box()
            nav = page.locator('nav[aria-label="Main navigation"]').bounding_box()
            assert last and nav and last['y']+last['height'] <= nav['y']+1, (last, nav)
            if width == 320:
                page.screenshot(path=str(out/'reports-bottom-320.png'))
        page.set_viewport_size({'width': 390, 'height': 844})
        for days in (1, 90, 20):
            name = 'Today' if days == 1 else f'{days} days'
            reports.get_by_role('button', name=name, exact=True).click()
            expect(reports).to_contain_text('USD 87.00')
            assert state['queries'][-1] == {'preset': [f'last{days}']}
            expect(reports.get_by_role('button', name=name, exact=True)).to_have_attribute('aria-pressed', 'true')
        # Date drafts must not silently relabel the loaded report.
        reports.locator('.report-custom summary').click()
        reports.get_by_label('From', exact=True).fill('2026-10-01')
        reports.get_by_label('Through', exact=True).fill('2026-10-10')
        before = len(state['queries'])
        assert state['queries'][-1] == {'preset': ['last20']}
        reports.get_by_role('button', name='Apply dates').click()
        expect(reports.locator('.report-period-label')).to_have_text('Custom dates')
        assert len(state['queries']) == before+1
        assert state['queries'][-1] == {'start_date': ['2026-10-01'], 'end_date': ['2026-10-10']}
        reports.get_by_label('From', exact=True).fill('2026-11-10')
        expect(reports.get_by_role('button', name='Apply dates')).to_be_disabled()
        reports.get_by_role('button', name='Month', exact=True).click()
        reports.get_by_label('Choose month', exact=True).fill('2026-10')
        reports.get_by_role('button', name='View month', exact=True).click()
        expect(reports.locator('.report-period-heading')).to_contain_text('31 Oct 2026')
        assert state['queries'][-1] == {'preset': ['month'], 'month': ['2026-10']}
        expect(reports.get_by_role('button', name='Open stock count', exact=True)).to_be_visible()
        reports.get_by_role('button', name='Skip stock count', exact=True).click()
        expect(reports.get_by_role('button', name='Open stock count', exact=True)).not_to_be_visible()
        state['mode'] = 'error'
        reports.get_by_role('button', name='Refresh sales report', exact=True).click()
        expect(reports.get_by_role('alert')).to_be_visible()
        expect(reports).not_to_contain_text('USD 87.00')
        page.screenshot(path=str(out/'reports-error-390.png'), full_page=True)
        state['mode'] = 'empty'
        reports.get_by_role('button', name='Try again', exact=True).click()
        expect(reports).to_contain_text('USD 0.00')
        expect(reports.get_by_role('alert')).not_to_be_visible()
        page.screenshot(path=str(out/'reports-empty-390.png'), full_page=True)
        page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Sell').click()
        page.get_by_role('button', name='End my day', exact=True).click()
        dialog = page.get_by_role('dialog', name='End my day cash check')
        expect(dialog.locator('.close-question')).to_contain_text('cash do you have')
        for width in (390, 320):
            page.set_viewport_size({'width': width, 'height': 844})
            box = dialog.bounding_box()
            assert box and box['x'] >= 0 and box['x']+box['width'] <= width+1, box
            assert dialog.locator('.close-question').evaluate("el=>getComputedStyle(el).fontSize") == '22px'
            page.screenshot(path=str(out/f'end-day-{width}.png'), full_page=True)
        dialog.get_by_role('button', name='Close', exact=True).click()
        page.locator('nav[aria-label="Main navigation"] button').filter(has_text='Today').click()
        expect(page.locator('.welcome')).to_be_visible()
        expect(page.locator('.welcome')).to_contain_text('Tendai')
        assert not state['posts'], state['posts']
        print('DOM PASS: reports390/320/1280 bounds; Reports greeting/duplicate logo removed, Today greeting retained, last row reachable above fixednav; presets1/20/90; inclusive custom and month queries; drafts; error hides oldtotals; emptyzero/recovery; optionalSkip; EndDay390/320bounds+original22pxquestion; no API posts', flush=True)
        print(str(out), flush=True)
        browser.close()
finally:
    server.shutdown()
    server.server_close()
