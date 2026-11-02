# Bundled demo product illustrations

These six original code-native illustrations cover the canonical starter
catalogue in `../demo_catalogue.json`. SVG files are editable sources; matching
512 x 512 PNGs are the runtime assets. They are illustrations, not packaging
photographs. The cola drawing uses a generic label rather than imitating a
manufacturer's packaging.

Both formats belong in the repository. A fresh demo uses the PNGs directly:
there is no image download, image generation, external URL, provider key or
rendering dependency at startup. SQLite persists the metadata and bytes through
the same private product-image endpoints as uploaded photos.

Seeding only adds missing images on the exact default shop/product identities.
An existing uploaded image always wins. Renamed products, different SKUs,
different shops and non-demo catalogues do not receive inferred images. It does
not reset stock, prices, costs or receipts.

To regenerate a PNG during development, render its SVG in a browser with a
512 x 512 viewport, zero body margin, and device scale factor 1. The committed
PNGs were rendered with local Chromium; this tool is not needed to run the app.
