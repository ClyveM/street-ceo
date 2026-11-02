from uuid import UUID
import pytest
from services.api.test_sqlite_store import SHOP, build, call
from services.api.test_paper_sales import setup, upload, review, confirm
BASE=f'/api/v1/shops/{SHOP}/daily-sales-batches'

def test_sqlite_failure_rolls_back_batch_stock_audit_and_retry(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    draft=upload(app); checked,_=review(app,draft)
    before={p.id:p.stock_qty for p in app.state.store.shops[UUID(SHOP)].products.values()}
    original=app.state.store._save
    def fail():
        app.state.store.connection.execute('DELETE FROM shop_state')
        raise RuntimeError('injected disk failure')
    with monkeypatch.context() as patch:
        patch.setattr(app.state.store,'_save',fail)
        assert confirm(app,checked).status_code==503
    record=app.state.store.shops[UUID(SHOP)]
    assert {p.id:p.stock_qty for p in record.products.values()}==before
    assert not record.daily_batch_stock_audits and not record.daily_batch_idempotency
    assert record.daily_sales_batches[UUID(draft['id'])].status=='reviewed'
    app.state.store.close();app=build(tmp_path/'shop.sqlite3')
    assert confirm(app,checked).status_code==200
    assert len(app.state.store.shops[UUID(SHOP)].daily_batch_stock_audits)==1
    app.state.store.close()

def test_canonical_duplicate_ignores_optional_unit_price_and_tender_reallocation(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    a=upload(app,b'A');ra,_=review(app,a,unit=150)
    assert confirm(app,ra).status_code==200
    b=upload(app,b'B');rb,_=review(app,b,cash=0,bank=300,unit=None)
    assert rb['canonical_sha256']==ra['canonical_sha256']
    response=confirm(app,rb,'different')
    assert response.status_code==409,response.text
    assert len(app.state.store.shops[UUID(SHOP)].daily_batch_stock_audits)==1
    app.state.store.close()

@pytest.mark.parametrize('change',['name','sku','quantity'])
def test_review_drift_requires_new_review_without_partial_stock(tmp_path,monkeypatch,change):
    app=setup(tmp_path,monkeypatch);draft=upload(app);checked,body=review(app,draft)
    product_id=UUID(body['lines'][0]['product_id'])
    with app.state.store.transaction():
        product=app.state.store.shops[UUID(SHOP)].products[product_id]
        if change=='quantity': product.stock_qty+=1
        elif change=='name':product.name='Renamed product'
        else:product.sku='NEW-SKU'
    assert confirm(app,checked).status_code==409
    assert not app.state.store.shops[UUID(SHOP)].daily_batch_stock_audits
    app.state.store.close()

