"""Independent visual smoke of built screens using isolated canonical fixtures."""
import calendar
import hashlib
import json
from datetime import date,timedelta
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'apps/web/dist'
OUT=ROOT/'data/qa-emerald-ux'
OUT.mkdir(parents=True,exist_ok=True)
STARTER=json.loads((ROOT/'services/api/demo_catalogue.json').read_text())
SHOP=STARTER['shop']['id']
PRODUCTS=[dict(p,shop_id=SHOP) for p in STARTER['products']]
TODAY=date(2026,11,3)
POSTS=[]
ERRORS=[]
METADATA=[]
CONTENT={}
for i,p in enumerate(PRODUCTS):
    data=(ROOT/'services/api/demo_product_images'/f"{p['sku'].lower()}.png").read_bytes()
    item={'id':f'picture-{i}','shop_id':SHOP,'product_id':p['id'],'filename':f"{p['sku'].lower()}.png",'content_type':'image/png','size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'storage_backend':'memory','storage_ref':f'memory://product-images/picture-{i}','uploaded_at':'2026-11-03T10:00:00Z'}
    METADATA.append(item);CONTENT[p['id']]=data

def sales_report(query):
    preset=query.get('preset',['last1'])[0]
    end=TODAY
    if preset=='month':
        year,month=map(int,query['month'][0].split('-'));start=date(year,month,1);end=min(date(year,month,calendar.monthrange(year,month)[1]),TODAY)
    elif preset.startswith('last'):start=end-timedelta(days=int(preset[4:])-1)
    else:start=date.fromisoformat(query['start_date'][0]);end=date.fromisoformat(query['end_date'][0])
    return {'start_date':str(start),'end_date':str(end),'coverage_end_date':str(end),'coverage':'historical_or_selected_range','as_of':'2026-11-03T10:00:00+02:00','shop_timezone':'Africa/Harare','currency':'USD',
     'summary':{'sales_total_cents':460,'transaction_count':3,'daily_summary_count':0,'cash_sales_cents':310,'bank_sales_cents':150,'other_tender_sales_cents':0,'cogs_micros':3100000,'missing_cogs_sale_count':0},
     'monthly':[{'month':str(start)[:7],'sales_total_cents':460,'transaction_count':3}],
     'daily':[{'business_date':str(start),'sales_total_cents':460,'transaction_count':3}],
     'products':[{'product_id':p['id'],'product_name':p['name'],'sku':p['sku'],'label_source':'latest_receipt_snapshot','quantity_sold':1,'revenue_cents':p['unit_price_cents'],'known_revenue_cents':p['unit_price_cents'],'unknown_revenue_line_count':0} for p in (PRODUCTS[0],PRODUCTS[1],PRODUCTS[3])],
     'stock_reversal_count':0,'warnings':[]}

def route(r):
    req=r.request;u=urlparse(req.url);path=u.path
    if u.hostname=='visual.invalid':
        asset=(DIST/(path.lstrip('/') or 'index.html')).resolve()
        if asset.is_relative_to(DIST.resolve()) and asset.is_file():r.fulfill(path=str(asset))
        else:r.fulfill(status=404,body='Missing isolated web asset')
        return
    if u.scheme=='blob':r.continue_();return
    if u.hostname!='shop.invalid':r.abort('blockedbyclient');return
    h={'Access-Control-Allow-Origin':'*'}
    def reply(v,status=200):r.fulfill(status=status,content_type='application/json',headers=h,body=json.dumps(v))
    if req.method=='OPTIONS':r.fulfill(status=204,headers={**h,'Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'});return
    if req.method not in ('GET','HEAD'):POSTS.append((path,req.post_data));reply({'detail':'Read-only visual fixture'},409);return
    if path=='/readyz':reply({'status':'ready'});return
    if path==f'/shops/{SHOP}':reply({**STARTER['shop']});return
    if path.endswith('/products'):reply(PRODUCTS);return
    if path.endswith('/summary'):reply({'sales_total_cents':460,'transaction_count':3,'daily_summary_count':0,'low_stock_count':2,'sales_change_percent':None,'insight':'2 products are running low. Check sugar and bath soap before your next restock.'});return
    if path.endswith('/product-images'):reply(METADATA);return
    if path.endswith('/image/content'):
        product=path.split('/')[-3];item=next(x for x in METADATA if x['product_id']==product)
        r.fulfill(body=CONTENT[product],content_type='image/png',headers={**h,'ETag':'"'+item['sha256']+'"','X-Product-Image-ID':item['id'],'Access-Control-Expose-Headers':'ETag,X-Product-Image-ID'});return
    if path.endswith('/reports/sales'):reply(sales_report(parse_qs(u.query)));return
    reply([])

with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--disable-gpu'])
    context=browser.new_context(viewport={'width':390,'height':844},timezone_id='Africa/Harare',service_workers='block')
    context.route('**/*',route)
    context.add_init_script("""localStorage.setItem('street-ceo-api-config',JSON.stringify({baseUrl:'http://shop.invalid',shopId:'00000000-0000-0000-0000-000000000001'}));localStorage.setItem('street-ceo-hands-free-v1','off');""")
    page=context.new_page();page.set_default_timeout(10000);page.on('pageerror',lambda e:ERRORS.append(str(e)))
    page.goto('http://visual.invalid/',wait_until='load')
    expect(page.get_by_role('button',name='Shop connected',exact=False)).to_be_visible()
    for label in ('Today','Sell','Stock','Reports','Profile'):
        nav=page.locator('nav[aria-label="Main navigation"]')
        nav.get_by_role('button',name=label,exact=False).click()
        if label=='Stock':expect(page.locator('.stock-catalog-table tbody tr')).to_have_count(6)
        if label=='Reports':expect(page.locator('.report-products')).to_contain_text('Coca-Cola')
        if label=='Profile':expect(page.locator('.pronunciation-setup')).to_be_visible()
        if label=='Today':
            family=page.locator('.hero-amount').evaluate('el=>getComputedStyle(el).fontFamily')
            assert 'sans-serif' in family or 'Arial' in family,('Offline hero font fallback',family)
        for width in (360,390,1280):
            page.set_viewport_size({'width':width,'height':844})
            page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
            page.wait_for_timeout(100)
            dims=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
            assert dims['scroll']<=dims['width'],(label,width,dims)
            for button in nav.get_by_role('button').all():
                bounds=button.bounding_box();assert bounds and bounds['height']>=44 and bounds['width']>=44,(label,width,bounds)
            page.screenshot(path=str(OUT/f'{label.lower()}-{width}.png'),full_page=True)
            page.screenshot(path=str(OUT/f'{label.lower()}-top-{width}.png'))
        page.set_viewport_size({'width':390,'height':844})
    assert not POSTS,POSTS
    assert not ERRORS,ERRORS
    browser.close()
print('PASS five built screens, 360/390/1280 bounds, nav targets, actual bundled images, read-only fixture, no JS errors')
