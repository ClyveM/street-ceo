"""Daily-sheet isolation, exact-once recording and integration without cloud calls."""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID
from zoneinfo import ZoneInfo

import httpx

from services.api.test_sqlite_store import SHOP, build, call


async def _request(app,method,path,**kwargs):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        return await client.request(method,path,headers={'X-Shop-ID':SHOP,**kwargs.pop('headers',{})},**kwargs)


def request(app,method,path,**kwargs):
    return asyncio.run(_request(app,method,path,**kwargs))


def setup(tmp_path,monkeypatch):
    monkeypatch.setenv('STREET_CEO_TRACE_DATABASE',str(tmp_path/'trace.sqlite3'))
    app=build(tmp_path/'shop.sqlite3')
    app.state.paper_extractor=lambda image,mime,cat: SimpleNamespace(status='unavailable',lines=(),warnings=('Synthetic OCR unavailable; edit manually.',))
    return app


def upload(app,contents=b'synthetic-source'):
    result=request(app,'POST',f'/api/v1/shops/{SHOP}/daily-sales-batches/extract',files={'image':('sheet.png',contents,'image/png')})
    assert result.status_code==201,result.text
    return result.json()


def review(app,draft,cash=200,bank=100,quantity=2,unit=None,total=300):
    product=next(iter(app.state.store.shops[UUID(SHOP)].products.values()))
    body={'business_date':draft['business_date'],'actor':'owner','source_ref':'daily sheet A','notes':'reviewed actual total','lines':[{'product_id':str(product.id),'quantity':quantity,'unit_price_cents':unit,'line_total_cents':total}],'cash_cents':cash,'bank_cents':bank}
    result=call(app,'POST',f"/api/v1/shops/{SHOP}/daily-sales-batches/{draft['id']}/review",body=body)
    assert result.status_code==200,result.text
    return result.json(),body


def confirm(app,reviewed,key='sheet-confirm',**changes):
    body={'reviewed_version':reviewed['reviewed_version'],'confirmed':True,'only_unrecorded':True,'prices_reviewed':True,'stock_not_reflected':True,**changes}
    return call(app,'POST',f"/api/v1/shops/{SHOP}/daily-sales-batches/{reviewed['id']}/confirm",key,body)


def test_sheet_is_distinct_atomic_once_and_integrated_everywhere(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    product=next(iter(app.state.store.shops[UUID(SHOP)].products.values()))
    opening=product.stock_qty
    draft=upload(app)
    assert draft['ocr_lines']==[] and draft['extraction_status']=='unavailable'
    assert app.state.store.shops[UUID(SHOP)].products[product.id].stock_qty==opening
    checked,body=review(app,draft)
    assert checked['status']=='reviewed' and checked['total_cents']==300
    assert confirm(app,checked,only_unrecorded=False).status_code==409
    posted=confirm(app,checked)
    assert posted.status_code==200,posted.text
    assert posted.json()['record_type']=='daily_sales_batch'
    assert confirm(app,checked).json()==posted.json()
    assert confirm(app,checked,prices_reviewed=False).status_code==409
    record=app.state.store.shops[UUID(SHOP)]
    assert record.products[product.id].stock_qty==opening-2
    assert len(record.idempotent_sales)==0 and len(record.daily_batch_stock_audits)==1
    report=call(app,'GET',f'/api/v1/shops/{SHOP}/reports/sales?preset=last1').json()
    assert report['summary']['sales_total_cents']==300
    assert report['summary']['transaction_count']==0 and report['summary']['daily_summary_count']==1
    assert report['summary']['cogs_micros'] is None and report['summary']['gross_profit_micros'] is None
    assert report['summary']['missing_cogs_sale_count']==0 and report['summary']['missing_cogs_daily_summary_count']==1
    assert report['products'][0]['quantity_sold']==2 and report['products'][0]['revenue_cents']==300
    assert report['products'][0]['cogs_micros'] is None and report['products'][0]['label_source']=='daily_summary_snapshot'
    assert report['daily'][0]['daily_summary_count']==1 and report['monthly'][0]['daily_summary_count']==1
    summary=call(app,'GET',f'/shops/{SHOP}/summary').json()
    assert summary['sales_total_cents']==300 and summary['transaction_count']==0 and summary['daily_summary_count']==1
    preview=call(app,'GET',f'/api/v1/shops/{SHOP}/cash-close/preview').json()
    assert preview['sales_cash_cents']==200 and posted.json()['id'] in preview['source_ids']
    insight=call(app,'POST',f'/api/v1/shops/{SHOP}/muse',body={'question':'What are my total sales today?'}).json()
    assert 'USD 3.00' in insight['answer'] and '1 daily sales sheet' in insight['answer']
    profit=call(app,'POST',f'/api/v1/shops/{SHOP}/muse',body={'question':'What profit did I make this month?'}).json()
    assert profit['status']=='needs_data' and 'unknown historical COGS' in profit['answer']
    assert call(app,'GET',f'/shops/{SHOP}/sales').json()==[]
    app.state.store.close()
    app=build(tmp_path/'shop.sqlite3')
    assert confirm(app,checked).json()==posted.json()
    assert call(app,'GET',f"/api/v1/shops/{SHOP}/daily-sales-batches/{draft['id']}").json()==posted.json()
    image=request(app,'GET',f"/api/v1/shops/{SHOP}/daily-sales-batches/{draft['id']}/image")
    assert image.content==b'synthetic-source'
    assert len(app.state.store.shops[UUID(SHOP)].daily_batch_stock_audits)==1
    assert app.state.store.shops[UUID(SHOP)].products[product.id].stock_qty==opening-2
    app.state.store.close()


def test_duplicate_source_canonical_and_stale_baseline(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    first=upload(app,b'source-A')
    reviewed,_=review(app,first)
    second=upload(app,b'recropped-source-B')
    review2,body=review(app,second)
    assert confirm(app,reviewed).status_code==200
    assert confirm(app,review2,'other-key').status_code==409 # day/stock baseline stale
    result=call(app,'POST',f"/api/v1/shops/{SHOP}/daily-sales-batches/{second['id']}/review",body=body)
    assert result.status_code==200
    assert confirm(app,result.json(),'other-key').status_code==409 # canonical duplicate
    duplicate=request(app,'POST',f'/api/v1/shops/{SHOP}/daily-sales-batches/extract',files={'image':('same.png',b'source-A','image/png')})
    assert duplicate.status_code==409
    assert len(app.state.store.shops[UUID(SHOP)].daily_batch_stock_audits)==1
    app.state.store.close()


def test_invalid_amounts_closed_backdated_count_and_all_line_prevalidation(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    draft=upload(app)
    checked,body=review(app,draft,quantity=3,total=100,cash=100,bank=0) # exact mixed-price 3 units/100 cents
    route=f"/api/v1/shops/{SHOP}/daily-sales-batches/{draft['id']}/review"
    assert call(app,'POST',route,body={**body,'cash_cents':101}).status_code==422
    assert call(app,'POST',route,body={**body,'lines':[{**body['lines'][0],'unit_price_cents':33}]}).status_code==422
    assert call(app,'POST',route,body={**body,'business_date':(datetime.fromisoformat(body['business_date'])-timedelta(days=1)).date().isoformat()}).status_code==409
    product=next(iter(app.state.store.shops[UUID(SHOP)].products.values()))
    stock=product.stock_qty
    with app.state.store.transaction():
        app.state.store.shops[UUID(SHOP)].products[product.id].stock_qty-=1
    assert confirm(app,checked).status_code==409
    result=call(app,'POST',route,body=body)
    assert result.status_code==200
    count=call(app,'POST',f'/api/v1/shops/{SHOP}/stock-takes',body={'mode':'on_demand','actor':'owner','count_date':body['business_date'],'lines':[{'product_id':str(product.id),'counted_qty':stock-1}]}).json()
    assert call(app,'POST',f"/api/v1/shops/{SHOP}/stock-takes/{count['id']}/confirm").status_code==200
    assert confirm(app,result.json()).status_code==409
    assert app.state.store.shops[UUID(SHOP)].daily_batch_stock_audits==[]
    app.state.store.close()


def test_scoped_history_and_images_do_not_leak_other_shop(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    draft=upload(app)
    other=call(app,'POST','/shops',body={'name':'Other'}).json()['id']
    assert call(app,'GET',f'/api/v1/shops/{other}/daily-sales-batches',shop_header=other).json()==[]
    assert call(app,'GET',f"/api/v1/shops/{other}/daily-sales-batches/{draft['id']}",shop_header=other).status_code==404
    assert call(app,'GET',f"/api/v1/shops/{other}/daily-sales-batches/{draft['id']}/image",shop_header=other).status_code==404
    assert call(app,'GET',f'/api/v1/shops/{SHOP}/daily-sales-batches',shop_header=other).status_code==403
    app.state.store.close()


def test_all_line_validation_and_closed_day_block_before_mutation(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    draft=upload(app)
    checked,body=review(app,draft)
    products=list(app.state.store.shops[UUID(SHOP)].products.values())
    body['lines'].append({'product_id':str(products[1].id),'quantity':999,'unit_price_cents':None,'line_total_cents':100})
    body['cash_cents']+=100
    invalid=call(app,'POST',f"/api/v1/shops/{SHOP}/daily-sales-batches/{draft['id']}/review",body=body)
    assert invalid.status_code==409
    assert app.state.store.shops[UUID(SHOP)].products[products[0].id].stock_qty==products[0].stock_qty
    day=checked['business_date']
    opening=call(app,'POST',f'/api/v1/shops/{SHOP}/cash-close/opening','opening',{'business_date':day,'opening_cash_cents':0,'actor':'owner','reason':'explicit zero','confirmed':True})
    assert opening.status_code==201,opening.text
    preview=call(app,'GET',f'/api/v1/shops/{SHOP}/cash-close/preview').json()
    closed=call(app,'POST',f'/api/v1/shops/{SHOP}/cash-close','close',{'business_date':day,'cash_counted_cents':0,'actor':'owner','confirmed':True,'preview_version':preview['preview_version']})
    assert closed.status_code==201,closed.text
    assert confirm(app,checked).status_code==409
    assert app.state.store.shops[UUID(SHOP)].daily_batch_stock_audits==[]
    app.state.store.close()


def test_stored_product_photos_index_content_and_restart_scope(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    product=next(iter(app.state.store.shops[UUID(SHOP)].products.values()))
    root=f'/api/v1/shops/{SHOP}'
    uploaded=request(app,'POST',f'{root}/products/{product.id}/image',files={'image':('product.png',b'first-image','image/png')})
    assert uploaded.status_code==201,uploaded.text
    latest=request(app,'POST',f'{root}/products/{product.id}/image',files={'image':('product2.png',b'latest-image','image/png')}).json()
    assert call(app,'GET',root+'/product-images').json()==[latest]
    content=request(app,'GET',f'{root}/products/{product.id}/image/content')
    assert content.content==b'latest-image' and content.headers['content-type']=='image/png'
    assert content.headers['etag']=='"'+latest['sha256']+'"'
    assert content.headers['x-product-image-id']==latest['id']
    assert call(app,'GET',f'{root}/products/{product.id}/image').json()==latest
    other=call(app,'POST','/shops',body={'name':'Other'}).json()['id']
    assert call(app,'GET',f'/api/v1/shops/{other}/product-images',shop_header=other).json()==[]
    assert call(app,'GET',f'/api/v1/shops/{other}/products/{product.id}/image/content',shop_header=other).status_code==404
    app.state.store.close()
    app=build(tmp_path/'shop.sqlite3')
    assert call(app,'GET',root+'/product-images').json()==[latest]
    assert request(app,'GET',f'{root}/products/{product.id}/image/content').content==b'latest-image'
    app.state.store.close()


def test_stale_review_code_is_specific_nonmutating_and_exact_replay_still_wins(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    draft=upload(app)
    checked,body=review(app,draft)
    stock_before={key:product.stock_qty for key,product in app.state.store.shops[UUID(SHOP)].products.items()}
    stale=confirm(app,checked,reviewed_version='outdated-version')
    assert stale.status_code==409 and stale.json()['detail']['code']=='paper_review_stale'
    assert isinstance(stale.json()['detail']['message'],str)
    record=app.state.store.shops[UUID(SHOP)]
    assert {key:product.stock_qty for key,product in record.products.items()}==stock_before
    assert record.daily_batch_stock_audits==[] and record.daily_batch_idempotency=={}
    with app.state.store.transaction():
        first=next(iter(app.state.store.shops[UUID(SHOP)].products.values()))
        first.stock_qty-=1
    baseline_stale=confirm(app,checked)
    assert baseline_stale.status_code==409 and baseline_stale.json()['detail']['code']=='paper_review_stale'
    assert app.state.store.shops[UUID(SHOP)].daily_batch_stock_audits==[]
    fresh=call(app,'GET',f"/api/v1/shops/{SHOP}/daily-sales-batches/{draft['id']}")
    assert fresh.json()['status']=='reviewed'
    updated=call(app,'POST',f"/api/v1/shops/{SHOP}/daily-sales-batches/{draft['id']}/review",body=body).json()
    posted=confirm(app,updated,'fresh-confirm')
    assert posted.status_code==200,posted.text
    assert confirm(app,updated,'fresh-confirm').json()==posted.json() # retry after own stock deduction is original success
    assert isinstance(confirm(app,updated,'fresh-confirm',prices_reviewed=False).json()['detail'],str)
    assert isinstance(confirm(app,updated,'new-key').json()['detail'],str) # already confirmed is not a stale review
    assert len(app.state.store.shops[UUID(SHOP)].daily_batch_stock_audits)==1
    app.state.store.close()
