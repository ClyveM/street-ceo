from uuid import UUID
import pytest
from services.api.test_sqlite_store import SHOP, build, call
from services.api.test_retained_basket import resolver

BASE = f'/api/v1/shops/{SHOP}/voice'

@pytest.fixture
def shop(tmp_path, monkeypatch):
    monkeypatch.setenv('STREET_CEO_TRACE_DATABASE', str(tmp_path/'trace.sqlite3'))
    app = build(tmp_path/'shop.sqlite3', resolver)
    yield app
    app.state.store.close()

def initial(app, text='one coke, two mystery'):
    response=call(app,'POST',BASE+'/transcript','initial',{'transcript':text})
    assert response.status_code==200,response.text
    data=response.json()
    assert data['status']=='needs_clarification' and not data['lines']
    return data

def reply(app, previous, text, key='reply'):
    return call(app,'POST',BASE+'/transcript',key,{'transcript':text,'clarification_of':previous['request_id']})

def no_sale(app):
    assert not app.state.store.shops[UUID(SHOP)].idempotent_sales

@pytest.mark.parametrize('kind',['deleted','out_of_stock'])
def test_retained_product_invalidated_before_focused_answer_never_commits(shop,kind):
    first=initial(shop)
    record=shop.state.store.shops[UUID(SHOP)]
    retained=UUID(first['retained_lines'][0]['product_id'])
    with shop.state.store.transaction():
        record=shop.state.store.shops[UUID(SHOP)]
        if kind=='deleted': del record.products[retained]
        else: record.products[retained].stock_qty=0
    response=reply(shop,first,'bread')
    assert response.status_code==409,response.text
    no_sale(shop)

def test_forged_missing_context_and_cross_shop_headers_never_resolve(shop):
    first=initial(shop)
    bad=reply(shop,{'request_id':'00000000-0000-0000-0000-000000009999'},'bread')
    assert bad.status_code==409
    foreign=call(shop,'POST',BASE+'/transcript','foreign',{'transcript':'bread','clarification_of':first['request_id']},shop_header='00000000-0000-0000-0000-000000000002')
    assert foreign.status_code in (403,404)
    no_sale(shop)

def test_explicit_remove_resolves_only_active_slot_and_requires_full_confirmation(shop):
    first=initial(shop,'one coke, two mystery, three mystery widget')
    removed=reply(shop,first,'remove this item').json()
    assert len(removed['retained_lines'])==1
    assert len(removed['pending_items'])==1
    assert removed['pending_items'][0]['quantity']==3
    final=reply(shop,removed,'bread','last').json()
    assert final['status']=='needs_match_confirmation'
    assert {r['product_name']:r['quantity'] for r in final['lines']}=={'Coca-Cola 300ml':1,'Bread loaf':3}
    no_sale(shop)

@pytest.mark.parametrize('answer',['one bread and','one bread, one coke','one bread and two mystery'])
def test_incomplete_or_multi_item_focused_answer_never_silently_drops_words(shop,answer):
    first=initial(shop)
    result=reply(shop,first,answer).json()
    assert result['status']=='needs_clarification',result
    assert not result['lines'] and len(result['pending_items'])==1
    assert result['retained_lines']==first['retained_lines']
    no_sale(shop)


def test_resolved_review_never_accepts_subset_and_commit_rechecks_stock(shop):
    first=initial(shop)
    final=reply(shop,first,'bread').json()
    assert final['status']=='needs_match_confirmation'
    lines=[{'product_id':r['product_id'],'quantity':r['quantity']} for r in final['lines']]
    body={'review_id':final['request_id'],'lines':lines,'tender':'bank','match_confirmed':True}
    assert call(shop,'POST',BASE+'/commit','partial',{**body,'lines':lines[:1]}).status_code==409
    with shop.state.store.transaction():
        shop.state.store.shops[UUID(SHOP)].products[UUID(lines[0]['product_id'])].stock_qty=0
    response=call(shop,'POST',BASE+'/commit','full',body)
    assert response.status_code==409,response.text
    no_sale(shop)

def test_remove_last_pending_keeps_full_review_and_consumes_parent_once(shop):
    first=initial(shop)
    result=reply(shop,first,'remove item','remove')
    assert result.status_code==200,result.text
    data=result.json()
    assert data['status']=='needs_match_confirmation'
    assert len(data['lines'])==1 and data['lines'][0]==first['retained_lines'][0]
    assert data['requires_match_confirmation'] is True
    assert reply(shop,first,'remove item','remove').json()==data
    assert reply(shop,first,'bread','fork').status_code==409
    no_sale(shop)
