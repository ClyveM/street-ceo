# Mobile reports presentation

Owner-requested visual cleanup, 2 November 2026. The reporting API and its
accounting meaning remain unchanged.

The page should answer three questions at a glance: which period is selected,
how much was sold, and which products sold. Show one dominant sales total,
transaction count, simple cash/bank breakdown and readable product rows. Use
Street CEO's existing green, navy, warm accents and logo rather than adding
another visual system.

Keep period selection compact and clearly selected. Month and inclusive custom
dates must be easy to reach without crowding the first screen. Draft date edits
must not relabel an older loaded result. Loading, empty and failed reports need
distinct states; a failed request must never appear as zero sales.

Move daily/monthly detail, full coverage timestamps and accounting explanations
into secondary sections. Preserve a visible concise warning when costs or
product revenue are incomplete; unknown amounts cannot become zero. Sales remain
gross recorded sales, cash/bank are recorded tender, and stock-only reversals
remain separate. Optional month-end stock count stays secondary and skippable.

Verify the built page at 320px and 390px widths, including filters, long product
names, missing-cost states and errors. Preserve existing day-end and sale flows.
APK packaging, signature and served bytes are separate checks. Actual phone
layout and interaction still require physical-device verification.
