# Clean source and setup verification — 2026-11-02

The current shop source was exported from the Git index to an isolated directory,
with its own index and without ignored local team code, credentials, databases,
dependencies or generated bundles. This tests delivery source rather than the
developer's existing installation.

Verified on Windows with Python3.13.6, Node22.18.0 and npm10.9.3:

- `python infra/dev.py setup`: fresh virtual environment, declared Python
  dependencies and locked npm installation succeeded.
- Full backend and independent SQLite/voice acceptance: **255 passed**.
- Dependency-light quality/security/bootstrap checks: **29 passed**.
- Shop frontend: **117 passed**, 65-module production build, only shop entry.
- Independent client acceptance: **21 passed**.
- Actual isolated Uvicorn startup: readiness passed, six products with costs,
  and no team/office routes in OpenAPI. Only the test process was stopped.
- Product diagram: SVG → vector PDF/PNG rendered and visually reviewed; HTML
  passed 390px and 320px horizontal-width checks with a mobile reading order.

Two old retail-test assertions were corrected to preserve six opening demo-cost
audits while checking purchase deltas and rollback. Initial export test-directory
setup and a probe missing the required shop header were corrected; neither was
a product failure. The final clean-source run passed.

## Contributor effort

With Python and Node installed, setup is one helper command; API and web run in
two terminals. SQLite requires no database server. Cloud Muse additionally needs
an account-enabled backend key/model. Android packaging additionally needs
Android Studio/SDK/Java and a reachable backend. Initial installs need internet.

This is not proof of every operating system or a new physical-phone rehearsal.
The helper is cross-platform and CI includes Ubuntu Python/web checks. Check the
actual GitHub Actions result after pushing; local passes are not remote CI proof.
The live phone demo was not restarted or repackaged for repository cleanup.

See root README for commands, `docs/repository-boundaries.md` for exclusions,
`docs/product-demo-builder.md` for the product, and `infra/repo-clean-qa-001.md`
for the independent gate.
