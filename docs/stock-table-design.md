# Mobile stock table

Owner-requested Stock page presentation change, 2 November 2026.

Use a compact, accessible product table instead of expanded controls for every
catalogue item. Columns are product (with SKU), on-hand quantity and selling
price. Show the shop-currency context without inventing a currency. Product names
and large amounts must fit 320px/390px screens without losing information.
Search filters the loaded catalogue by name or SKU; an empty match is distinct
from an empty catalogue. Low stock remains visible.

Opening a row is read-only navigation to product details. Keep a keyboard-
accessible product button and a clear close/back action with sensible focus.
Details contain existing saved-cost information, purchase/cost-correction and
photo controls. Keep stock counts and retail control available from the page.
The table does not save a sale, change quantities or correct costs by tapping.

Preserve existing mutation/recovery guards and demo-disabled actions. Show
updated product data after a confirmed change rather than keeping stale selected
records. Do not change backend contracts, inventory calculations, financial
reporting or native microphone behaviour for this visual change.

Review real built-page screenshots at phone widths and test row navigation,
search, long names/amounts, keyboard access and existing actions with isolated
fixtures. Independently verify the packaged APK and served download. Physical
phone appearance remains a separate acceptance check.
