# Stock count page

Owner-requested standalone workflow, 2 November 2026.

Open Stock count from Stock, or the optional stock-count action in Reports or
End my day. Show a prominent **Start stock count** action above actual saved
history. Creating a new count opens a separate form within this workflow; the
history page does not start an adjustment automatically.

History includes draft and confirmed counts with dates and status. Opening a
saved record shows the counted products, expected quantities captured when the
draft was saved, physical counts, differences, who counted and notes. Confirmed
records are read-only. Saved drafts can return to the existing review step.
History comes from the shop's API, not from fabricated sample records or a
browser-only memory of this session.

Existing stock-control rules remain: blanks mean uncounted, not zero; saving a
draft does not change stock; explicit reviewed confirmation adjusts stock; a
changed baseline requires reloading/recounting; uncertain confirmation outcomes
must be checked before another attempt. Counting does not create a cash or bank
correction. This page does not require an accounting-period lock.

The history endpoint is GET `/api/v1/shops/{shop_id}/stock-takes`, returning saved
`StockTakeRecord` entries, newest first, under the same shop-scope checks as the
individual-record endpoint. Verify history after SQLite reopen and on a fresh
page load. Loading, empty and unavailable history must be distinct states.

Check mobile 320px/390px layout, history/detail navigation, new draft creation,
confirmation and recovery against isolated fixtures. Do not adjust live shop
stock merely to demonstrate the page.
