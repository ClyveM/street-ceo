"""Reviewed daily sales sheets, never invented customer receipts."""
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from typing import Literal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PaperModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class PaperOCRLine(PaperModel):
    raw_label: str = Field(max_length=500)
    product_id: UUID | None = None
    quantity: int | None = Field(default=None, gt=0, strict=True)
    unit_price_cents: int | None = Field(default=None, ge=0, strict=True)
    line_total_cents: int | None = Field(default=None, ge=0, strict=True)


class PaperLine(PaperModel):
    product_id: UUID
    quantity: int = Field(gt=0, strict=True)
    unit_price_cents: int | None = Field(default=None, ge=0, strict=True)
    line_total_cents: int = Field(ge=0, strict=True)

    @model_validator(mode='after')
    def price_consistent(self):
        if self.unit_price_cents is not None and self.quantity*self.unit_price_cents != self.line_total_cents:
            raise ValueError('Quantity times unit price must equal line amount, or clear unit price for mixed-price daily totals')
        return self


class PaperSavedLine(PaperLine):
    product_name: str
    sku: str


class PaperReview(PaperModel):
    business_date: date
    actor: str = Field(min_length=1, max_length=80)
    source_ref: str = Field(min_length=1, max_length=160)
    notes: str = Field(default='', max_length=500)
    lines: list[PaperLine] = Field(min_length=1, max_length=100)
    cash_cents: int = Field(ge=0, strict=True)
    bank_cents: int = Field(ge=0, strict=True)

    @field_validator('actor', 'source_ref', 'notes')
    @classmethod
    def strip_text(cls, value):
        value = value.strip()
        if not value:
            # Notes alone may be blank.
            return value
        return value

    @model_validator(mode='after')
    def validate_review(self):
        if not self.actor.strip() or not self.source_ref.strip():
            raise ValueError('Actor and source reference are required')
        if len({line.product_id for line in self.lines}) != len(self.lines):
            raise ValueError('A product may appear only once; combine its reviewed quantity and amount')
        if sum(line.line_total_cents for line in self.lines) != self.cash_cents+self.bank_cents:
            raise ValueError('Cash plus bank allocation must equal the reviewed line total')
        return self


class PaperConfirm(PaperModel):
    reviewed_version: str = Field(min_length=1, max_length=64)
    confirmed: bool = Field(strict=True)
    only_unrecorded: bool = Field(strict=True)
    prices_reviewed: bool = Field(strict=True)
    stock_not_reflected: bool = Field(strict=True)


class PaperSalesRecord(PaperModel):
    id: UUID
    shop_id: UUID
    record_type: Literal['daily_sales_batch'] = 'daily_sales_batch'
    status: Literal['draft', 'reviewed', 'confirmed'] = 'draft'
    business_date: date
    created_at: datetime
    confirmed_at: datetime | None = None
    filename: str
    content_type: str
    source_sha256: str
    source_ref: str
    ocr_lines: list[PaperOCRLine] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    extraction_status: str
    lines: list[PaperSavedLine] = Field(default_factory=list)
    cash_cents: int | None = None
    bank_cents: int | None = None
    total_cents: int | None = None
    actor: str = ''
    notes: str = ''
    reviewed_version: str | None = None
    canonical_sha256: str | None = None
    stock_baseline: dict[UUID, int] = Field(default_factory=dict)
    existing_sales_total_cents: int = 0
    existing_transaction_count: int = 0
    existing_daily_summary_count: int = 0


class PaperStockAudit(PaperModel):
    id: UUID
    batch_id: UUID
    shop_id: UUID
    product_id: UUID
    quantity_sold: int
    stock_before: int
    stock_after: int
    actor: str
    source_ref: str
    recorded_at: datetime


def confirmed_batches(record):
    return {item.id: item for item in record.daily_sales_batches.values() if item.status == 'confirmed' and item.shop_id == record.shop.id}.values()


def _digest(value):
    return sha256(json.dumps(value, default=str, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _open_day(record, business_date, product_ids=()):
    today = datetime.now(ZoneInfo(record.shop.timezone)).date()
    if business_date != today:
        raise HTTPException(409, 'Daily sheets support today in the shop timezone only; historical/future imports are not supported')
    if business_date in record.cash_closes or business_date in record.day_closes:
        raise HTTPException(409, 'This business day is closed; no sheet was recorded')
    wanted = set(product_ids)
    for count in record.stock_takes.values():
        if count.status == 'confirmed' and (count.count_date == business_date or count.confirmed_at and count.confirmed_at.astimezone(ZoneInfo(record.shop.timezone)).date() == business_date) and any(line.product_id in wanted for line in count.lines):
            raise HTTPException(409, 'A confirmed stock count may already include these sales; daily sheet recording is blocked for review')


def _baseline(record, item, lines):
    stock = {}
    for line in lines:
        product = record.products.get(line.product_id)
        if product is None:
            raise HTTPException(404, 'Reviewed product no longer exists in this shop')
        if line.quantity > product.stock_qty:
            raise HTTPException(409, 'Insufficient recorded stock; no sheet was recorded')
        stock[str(product.id)] = {'quantity': product.stock_qty, 'name': product.name, 'sku': product.sku}
    day = item.business_date
    zone = ZoneInfo(record.shop.timezone)
    sales = sorted({str(sale.id) for _, sale in record.idempotent_sales.values() if sale.created_at.astimezone(zone).date() == day})
    batches = sorted(str(batch.id) for batch in confirmed_batches(record) if batch.business_date == day)
    return _digest({'day': day, 'stock': stock, 'sales': sales, 'batches': batches,
                    'lines': [line.model_dump() for line in lines], 'cash': item.cash_cents, 'bank': item.bank_cents,
                    'actor': item.actor, 'source_ref': item.source_ref, 'notes': item.notes}), {UUID(key): value['quantity'] for key,value in stock.items()}


def _day_context(record, item):
    from .reports import sales_report
    report = sales_report(record, item.business_date, item.business_date)
    item.existing_sales_total_cents = report['summary']['sales_total_cents']
    item.existing_transaction_count = report['summary']['transaction_count']
    item.existing_daily_summary_count = report['summary'].get('daily_summary_count', 0)


def mount_paper_sales(app, shop_scope):
    from .social_data import validate_image_filename

    def get_item(record, batch_id):
        item = record.daily_sales_batches.get(batch_id)
        if item is None or item.shop_id != record.shop.id:
            raise HTTPException(404, 'Daily sheet not found in this shop')
        return item

    @app.post('/api/v1/shops/{shop_id}/daily-sales-batches/extract', response_model=PaperSalesRecord, status_code=201)
    def extract_sheet(record=Depends(shop_scope), image: UploadFile=File(...)):
        day = datetime.now(ZoneInfo(record.shop.timezone)).date()
        _open_day(record, day)
        try:
            filename = validate_image_filename(image.filename or '')
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        contents = image.file.read(5*1024*1024+1)
        if not contents or len(contents)>5*1024*1024:
            raise HTTPException(422, 'Upload a nonempty image no larger than 5 MiB')
        digest = sha256(contents).hexdigest()
        if any(batch.source_sha256 == digest for batch in confirmed_batches(record)):
            raise HTTPException(409, 'This source image was already recorded; open the original daily sheet')
        from services.ai.handwritten_sales import extract_handwritten_sales
        extractor = app.state.paper_extractor or extract_handwritten_sales
        catalogue = [{'product_id': str(product.id), 'name': product.name, 'sku': product.sku} for product in record.products.values()]
        try:
            result = extractor(contents, image.content_type or '', catalogue)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(503, 'Image extraction is unavailable; check server image dependencies/configuration') from exc
        from dataclasses import asdict
        now = datetime.now(timezone.utc)
        item = PaperSalesRecord(id=uuid4(), shop_id=record.shop.id, business_date=day, created_at=now,
                               filename=filename, content_type=image.content_type or '', source_sha256=digest,
                               source_ref=filename, ocr_lines=[PaperOCRLine(**asdict(line)) for line in result.lines],
                               warnings=list(result.warnings), extraction_status=result.status)
        _day_context(record,item)
        record.daily_sales_batches[item.id] = item
        record.daily_source_images[item.id] = contents
        return item

    @app.get('/api/v1/shops/{shop_id}/daily-sales-batches', response_model=list[PaperSalesRecord])
    def list_sheets(record=Depends(shop_scope)):
        return sorted((item for item in record.daily_sales_batches.values() if item.shop_id==record.shop.id), key=lambda item:(item.created_at,str(item.id)),reverse=True)

    @app.get('/api/v1/shops/{shop_id}/daily-sales-batches/{batch_id}', response_model=PaperSalesRecord)
    def read_sheet(batch_id:UUID, record=Depends(shop_scope)):
        return get_item(record,batch_id)

    @app.get('/api/v1/shops/{shop_id}/daily-sales-batches/{batch_id}/image')
    def read_sheet_image(batch_id:UUID, record=Depends(shop_scope)):
        item = get_item(record,batch_id)
        content = record.daily_source_images.get(item.id)
        if content is None:
            raise HTTPException(404,'Source image is unavailable')
        return Response(content,media_type=item.content_type,headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

    @app.post('/api/v1/shops/{shop_id}/daily-sales-batches/{batch_id}/review',response_model=PaperSalesRecord)
    def review_sheet(batch_id:UUID, request:PaperReview,record=Depends(shop_scope)):
        item = get_item(record,batch_id)
        if item.status=='confirmed':
            raise HTTPException(409,'Confirmed daily sheets cannot be edited')
        _open_day(record,request.business_date,[line.product_id for line in request.lines])
        candidate = item.model_copy(deep=True)
        candidate.business_date=request.business_date
        candidate.actor,candidate.source_ref,candidate.notes=request.actor,request.source_ref,request.notes
        candidate.cash_cents,candidate.bank_cents=request.cash_cents,request.bank_cents
        saved=[]
        for line in request.lines:
            product=record.products.get(line.product_id)
            if product is None:
                raise HTTPException(404,'Reviewed product not found in this shop')
            saved.append(PaperSavedLine(**line.model_dump(),product_name=product.name,sku=product.sku))
        candidate.lines=saved
        candidate.total_cents=sum(line.line_total_cents for line in saved)
        candidate.reviewed_version,candidate.stock_baseline=_baseline(record,candidate,saved)
        candidate.canonical_sha256=_digest({'day':candidate.business_date,'lines':sorted([
            {'product_id':line.product_id,'quantity':line.quantity,'line_total_cents':line.line_total_cents}
            for line in request.lines],key=lambda line:str(line['product_id']))})
        candidate.status='reviewed'
        _day_context(record,candidate)
        record.daily_sales_batches[candidate.id]=candidate
        return candidate

    @app.post('/api/v1/shops/{shop_id}/daily-sales-batches/{batch_id}/confirm',response_model=PaperSalesRecord)
    def confirm_sheet(batch_id:UUID,request:PaperConfirm,record=Depends(shop_scope),idempotency_key:str|None=Header(default=None,alias='Idempotency-Key')):
        if not idempotency_key or not idempotency_key.strip():
            raise HTTPException(400,'Idempotency-Key is required')
        key=idempotency_key.strip()
        fingerprint=_digest({'batch_id':batch_id,**request.model_dump()})
        old=record.daily_batch_idempotency.get(key)
        if old:
            if old[0]!=fingerprint:
                raise HTTPException(409,'Idempotency key payload mismatch')
            return old[1]
        item=get_item(record,batch_id)
        if not all((request.confirmed,request.only_unrecorded,request.prices_reviewed,request.stock_not_reflected)):
            raise HTTPException(409,'Explicitly confirm reviewed prices, only unrecorded sales and stock not already reflected')
        if item.status!='reviewed':
            raise HTTPException(409,'Open and review the latest daily sheet before confirming')
        if item.reviewed_version!=request.reviewed_version:
            raise HTTPException(409,{'code':'paper_review_stale','message':'The reviewed version changed; retrieve this daily sheet and explicitly review it again before confirming'})
        _open_day(record,item.business_date,[line.product_id for line in item.lines])
        version,_=_baseline(record,item,item.lines)
        if version!=request.reviewed_version:
            raise HTTPException(409,{'code':'paper_review_stale','message':'Stock or recorded day activity changed; retrieve this daily sheet and explicitly review it again before confirming'})
        if any(old.source_sha256==item.source_sha256 or old.canonical_sha256==item.canonical_sha256 for old in confirmed_batches(record)):
            raise HTTPException(409,'This source or reviewed daily sales content was already recorded; do not import it twice')
        # All validation above; only now construct and apply the complete mutation.
        now=datetime.now(timezone.utc)
        audits=[]
        for line in item.lines:
            product=record.products[line.product_id]
            audits.append(PaperStockAudit(id=uuid4(),batch_id=item.id,shop_id=record.shop.id,product_id=product.id,
                                         quantity_sold=line.quantity,stock_before=product.stock_qty,stock_after=product.stock_qty-line.quantity,
                                         actor=item.actor,source_ref=item.source_ref,recorded_at=now))
        for audit in audits:
            record.products[audit.product_id].stock_qty=audit.stock_after
        item.status,item.confirmed_at='confirmed',now
        item.warnings=list(item.warnings)+['Historical cost of these daily-sheet sales is unknown; current catalogue cost is not substituted.']
        record.daily_batch_stock_audits.extend(audits)
        record.daily_batch_idempotency[key]=(fingerprint,item)
        return item
