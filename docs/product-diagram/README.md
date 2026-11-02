# Street CEO product flow

Editable source: `street-ceo-product.svg`; standalone desktop/mobile reader: `index.html`.
This is a schematic of the connected demo, not evidence of physical-phone acceptance.

The customer flow is intentionally separate from the runtime architecture. Local proposals
and actual Muse calls both require explicit approval of suggested matches; provider provenance
stays distinct. Payment success requires a durable receipt. SQLite resides on the API host.

Typography stays as editable SVG text. Navy is neutral context, green indicates the main
flow, warm gold calls attention to confirmation/recovery safety. The numbered customer path
and text labels retain meaning without color. Dashed links are conditional helper/trace paths.
At 760px and below, HTML substitutes the same ordered content for the wide schematic so
small labels are not compressed. It needs no JavaScript, external fonts, network or API.

Preview generation: `python docs/product-diagram/render_preview.py` from the repo
root. Requires ReportLab, Windows Arial fonts and Poppler `pdftoppm`; it exports
a vector PDF and PNG directly from the current SVG primitives without a GPU.
The converter deliberately rejects unsupported SVG primitives rather than silently
omitting them. The SVG remains the editable source. `--browser` optionally checks
390px/320px HTML horizontal bounds with local Playwright and Microsoft Edge.
The default renderer does not claim HTML/browser visual verification.

PNG/PDF exports and the reduced inspection preview are ignored generated files.
Local copies are preserved, but a fresh clone uses the SVG/HTML directly. Run
the export command above when PNG/PDF files are needed for sharing.

Source of meaning: `docs/demo-mvp-acceptance.md`, `docs/fast-counter-acceptance.md`, and
current frontend/API contracts, 2026-11-02. Deferred: offline synchronization and PostgreSQL deployment.
