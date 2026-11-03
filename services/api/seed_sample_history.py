"""Create a separate local shop with 120 days of sample sales."""
import argparse
from calendar import monthrange
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path
from uuid import UUID, uuid5
from zoneinfo import ZoneInfo

from services.api.app import InMemoryStore, SaleCreate, SaleLine

SAMPLE_SHOP_ID = UUID("00000000-0000-0000-0000-000000000120")


def sample_catalogue():
    fixture = InMemoryStore()
    starter_id = fixture.seed_demo_shop()
    record = fixture.shops[starter_id]
    record.shop = record.shop.model_copy(update={"id": SAMPLE_SHOP_ID, "name": "Street CEO Sample Shop"})
    product_ids = {key: uuid5(SAMPLE_SHOP_ID, str(key)) for key in record.products}
    record.products = {
        product_ids[key]: product.model_copy(update={
            "id": product_ids[key], "shop_id": SAMPLE_SHOP_ID, "stock_qty": 1600,
        })
        for key, product in record.products.items()
    }
    record.product_images = {
        key: image.model_copy(update={"shop_id": SAMPLE_SHOP_ID, "product_id": product_ids[image.product_id]})
        for key, image in record.product_images.items()
    }
    record.cost_audits.clear()
    return record


def sample_receipts(record):
    if record is None:
        return {}
    return {key: sale for key, (fingerprint, sale) in record.idempotent_sales.items()
            if key.startswith("sample-history-") and fingerprint in {key, key + "-historical"}}


def add_sample_receipts(store, record, start: date, end: date, *,
                        daily_target=None, monthly_target=None, receipt_target_cents=None,
                        daily_sales_cents=None, monthly_sales_cents=None):
    zone = ZoneInfo(record.shop.timezone)
    now = datetime.now(zone)
    product_ids = sorted(record.products)
    priced = [product_id for product_id in product_ids if record.products[product_id].unit_price_cents > 0]
    targets_sales = any(value is not None for value in (receipt_target_cents, daily_sales_cents, monthly_sales_cents))
    if not product_ids or (targets_sales and not priced):
        raise ValueError("The sample shop needs products with selling prices.")
    seeded_dates = {sale.created_at.astimezone(zone).date() for sale in sample_receipts(record).values()}
    added = 0
    added_sales = 0
    target_sales = 0
    for offset in range((end - start).days + 1):
        day = start + timedelta(days=offset)
        if day in record.cash_closes or day in record.day_closes:
            continue
        if day in seeded_dates:
            continue
        randomizer = random.Random(day.toordinal())
        if monthly_target is not None:
            month_days = monthrange(day.year, day.month)[1]
            count = (day.day * monthly_target // month_days) - ((day.day - 1) * monthly_target // month_days)
        elif daily_target is not None:
            count = daily_target
        else:
            count = randomizer.randint(1, 3)
        day_sales = daily_sales_cents
        if monthly_sales_cents is not None:
            month_days = monthrange(day.year, day.month)[1]
            day_sales = (day.day * monthly_sales_cents // month_days) - ((day.day - 1) * monthly_sales_cents // month_days)
        if day_sales is not None:
            minimum_price = min(record.products[item].unit_price_cents for item in priced)
            count = min(count, max(0, (target_sales + day_sales - added_sales + minimum_price // 2) // minimum_price))
        for index in range(count):
            if not targets_sales:
                items = randomizer.sample(product_ids, randomizer.randint(1, min(3, len(product_ids))))
                lines = [SaleLine(product_id=item, quantity=randomizer.randint(1, 2)) for item in items]
            else:
                # Correct cumulative rounding while using actual catalogue prices.
                if day_sales is None:
                    desired_total = (added + 1) * receipt_target_cents
                else:
                    desired_total = target_sales + (index + 1) * day_sales // count
                desired = max(1, desired_total - added_sales)
                candidates = list(priced)
                randomizer.shuffle(candidates)
                def basket(product_id):
                    price = record.products[product_id].unit_price_cents
                    quantity = max(1, (desired + price // 2) // price)
                    return abs(price * quantity - desired), quantity
                item = min(candidates, key=lambda product_id: basket(product_id)[0])
                items = [item]
                lines = [SaleLine(product_id=item, quantity=basket(item)[1])]
            request = SaleCreate(
                lines=lines,
                tender=randomizer.choice(["cash", "cash", "bank"]),
            )
            key = f"sample-history-{day}-{index}"
            # These receipts predate the current inventory snapshot.
            original_stock = {item: record.products[item].stock_qty for item in items}
            try:
                for line in request.lines:
                    record.products[line.product_id].stock_qty = max(original_stock[line.product_id], line.quantity)
                receipt = store.create_sale(record, request, key + "-historical", key)
                receipt.stock_after = {}
            finally:
                for item, quantity in original_stock.items():
                    record.products[item].stock_qty = quantity
            receipt.created_at = min(datetime.combine(day, time(8 + index // 2, 30 * (index % 2)), zone), now)
            added += 1
            added_sales += receipt.total_cents
        if day_sales is not None:
            target_sales += day_sales
    return added


def seed(database: Path) -> None:
    from services.api.sqlite_store import SQLiteStore
    if not database.is_file():
        raise ValueError("Start the demo API once before seeding its SQLite database.")
    record = sample_catalogue()
    today = datetime.now(ZoneInfo(record.shop.timezone)).date()
    add_sample_receipts(InMemoryStore(), record, today - timedelta(days=119), today)
    store = SQLiteStore(str(database))
    try:
        with store.transaction():
            if SAMPLE_SHOP_ID in store.shops:
                print(f"Sample shop already exists and was preserved: {SAMPLE_SHOP_ID}")
                return
            store.shops[SAMPLE_SHOP_ID] = record
    finally:
        store.close()
    print(f"Sample shop: {SAMPLE_SHOP_ID}. {len(record.idempotent_sales)} receipts, {today - timedelta(days=119)} through {today}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    seed(parser.parse_args().database)
