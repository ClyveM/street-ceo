# Basket corrections, paper summaries, report sharing and sale photos

Owner-approved additions, 2 November 2026. The Owner confirmed paper notes are a
combined list of everything sold that day, not separate customer receipts.

## Focused basket clarification

Keep understood products while asking about the unresolved item or quantity.
A reply corrects the active slot, not the whole basket. Show retained items and
remaining questions. Never silently omit an item or post the understood subset.
Allow deliberate removal, then require review of the complete resolved basket.
Persist server review context across reconnect/reload and keep idempotency and
stock guards. Bound requests reasonably for a 100-item basket; UI speech limits
must not force an entire long basket to be repeated.

## Handwritten daily sheet

Upload a photo into a review-only extraction workflow. Image/model output is
untrusted input and cannot record sales automatically. The seller reviews date,
catalogue matches, quantities, actual selling amounts and cash/bank allocation.
Treat this as a distinct daily sales summary, not invented customer receipts,
customer tender/change or a known customer transaction count.

Initial demo policy is today's still-open business day only. Block closed or
unsupported backdated days and conflicts with confirmed stock counts that may
already include these quantities. Require an explicit declaration that the sheet
contains only sales not already entered, and detect exact duplicate sources and
retries. Confirming a reviewed summary must atomically persist its audit, report
and cash totals and stock movements once. Missing historical costs remain
unknown unless supported by confirmed evidence. See the finance policy memo for
the authoritative accounting conditions.

All relevant totals must include an accepted sheet exactly once. Keep customer
sales counts separate from daily sheets. Cash-close must not default unknown
tender to cash. Failed extraction, uncertain confirmation and model unavailability
must leave clear recoverable states. Never claim OCR success from fake-provider
tests; real vision configuration and physical-photo acceptance are separate.

## Exports from Reports

CSV contains plain tabular data and cannot embed a logo. Brand its text headings
and provide a companion branded PDF with the bundled Street CEO logo. Export the
currently verified selected report period and currency. Preserve incomplete and
unknown values, losses, gross-profit-before-expenses labels and source coverage.
Escape CSV cells against spreadsheet formula execution and quote delimiters,
quotes and newlines correctly. Include exact values or disclosed rounding where
needed. Do not export a failed/loading report as an empty successful report.

On Android expose the system share sheet for the generated file through narrow
private-cache content URIs. Browser download/print/share fallback must describe
its actual capability. PDF pagination and logo/text layout require rendered
review; native compilation is not proof of physical phone sharing.

## Product images while selling

Show available product images from the existing product-image source in the sale
catalogue and basket where a verified product ID matches. Keep a clear fallback
for missing/failed images; distinguish a local preview from a stored image. Never
let image loading hide product names, quantities, prices or block a sale.
