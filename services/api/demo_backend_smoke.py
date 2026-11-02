"""Live LAN regression smoke using a separate synthetic shop; never resets the demo."""
import json
import urllib.request
import urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import uuid4


def main():
    base = "http://192.168.10.213:8000"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    shop_id = None

    def call(path, payload=None, key=None, expected=200):
        headers = {"Content-Type": "application/json"}
        if shop_id:
            headers["X-Shop-ID"] = shop_id
        if key:
            headers["Idempotency-Key"] = key
        request = urllib.request.Request(base + path, data=None if payload is None else json.dumps(payload).encode(), headers=headers)
        try:
            with opener.open(request, timeout=10) as response:
                code, result = response.status, json.load(response)
        except urllib.error.HTTPError as error:
            code, result = error.code, json.load(error)
        assert code == expected, (path, code, result)
        return result

    assert call('/healthz')['status'] == 'ok'
    call('/readyz')
    shop_id = call('/shops', {'name': 'W6-DEMO-BACKEND-001 isolated smoke'}, expected=201)['id']
    root = f'/api/v1/shops/{shop_id}'
    product = call(f'/shops/{shop_id}/products', {'sku': 'COKE-300', 'name': 'Coca-Cola 300ml', 'unit_price_cents': 150, 'opening_stock_qty': 10}, expected=201)
    product_id = product['id']
    today = datetime.now(ZoneInfo('Africa/Harare')).date().isoformat()

    def product_now():
        return next(p for p in call(f'/shops/{shop_id}/products') if p['id'] == product_id)

    correction_root = root + f'/products/{product_id}/cost-corrections'
    draft = call(correction_root, {'unit_cost': '1.20', 'effective_date': today, 'reason': 'Synthetic smoke', 'source_ref': 'W6-DEMO-BACKEND-001', 'actor': 'hwaro-smoke'}, expected=201)
    assert product_now()['stock_qty'] == 10 and product_now()['unit_cost_micros'] is None
    call(correction_root + f"/{draft['id']}/confirm", {})
    assert product_now()['stock_qty'] == 10 and product_now()['unit_cost_micros'] == 1200000
    call(correction_root + f"/{draft['id']}/confirm", {}, expected=409)

    line = {'product_id': product_id, 'quantity': 1, 'purchase_unit_cost_micros': 1200000, 'line_total_micros': 1200000}
    bad_line = dict(line, product_id=str(uuid4()))
    purchase_body = {'kind': 'manual', 'reference': 'smoke-invalid', 'purchase_date': today, 'actor': 'hwaro-smoke', 'tender': 'cash', 'total_cost_micros': 2400000, 'lines': [line, bad_line]}
    bad = call(root + '/purchases', purchase_body, expected=201)
    call(root + f"/purchases/{bad['id']}/confirm", {}, expected=404)
    assert product_now()['stock_qty'] == 10
    purchase_body.update(reference='smoke-valid', total_cost_micros=1200000, lines=[line])
    purchase = call(root + '/purchases', purchase_body, expected=201)
    confirmed = call(root + f"/purchases/{purchase['id']}/confirm", {})
    assert call(root + f"/purchases/{purchase['id']}/confirm", {}) == confirmed
    assert product_now()['stock_qty'] == 11

    review = call(root + '/voice/transcript', {'transcript': '1 coke'}, 'smoke-review')
    assert review['status'] == 'needs_confirmation', review
    body = {'review_id': review['request_id'], 'lines': [{'product_id': product_id, 'quantity': 1}], 'tender': 'cash', 'amount_received_cents': 200}
    sale = call(root + '/voice/commit', body, 'smoke-sale')
    assert sale['change_cents'] == 50 and product_now()['stock_qty'] == 10
    assert call(root + '/voice/commit', body, 'smoke-sale')['id'] == sale['id']
    assert product_now()['stock_qty'] == 10
    call(root + '/voice/commit', body, 'smoke-sale-second-key', expected=409)
    assert product_now()['stock_qty'] == 10
    preview = call(root + '/day-close/preview?business_date=' + today)
    assert preview['calculation_basis'] == 'full_recorded_movements'
    assert preview['expected_cash_cents'] == 30, preview
    body = {'business_date': today, 'cash_counted_cents': 30, 'bank_card_counted_cents': 0, 'actor': 'hwaro-smoke', 'confirmed': True, 'notes': 'Isolated LAN regression'}
    close = call(root + '/day-close', body, 'smoke-close', expected=201)
    assert close['cash_variance_cents'] == close['bank_card_variance_cents'] == 0
    assert call(root + '/day-close', body, 'smoke-close', expected=201) == close
    assert call(root + '/day-close/' + today) == close
    call(root + '/day-close', body, 'smoke-close-duplicate', expected=409)
    print(json.dumps({'status': 'passed', 'shop_id': shop_id, 'sale_id': sale['id'], 'close_audit_id': close['audit_id'], 'purchase_id': purchase['id'], 'correction_id': draft['id'], 'stock_final': 10, 'expected_cash_cents': 30, 'demo_shop_reset': False}))


if __name__ == '__main__':
    main()
