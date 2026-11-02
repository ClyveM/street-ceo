from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path.cwd();out=root/'data/qa-capture-export/output/pdf'
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page();page.set_content((out/'report-layout.html').read_text(encoding='utf-8'),wait_until='load')
    assert page.locator('header img').evaluate('(i)=>i.naturalWidth')>0
    page.pdf(path=str(out/'street-ceo-profit-100-products.pdf'),format='A4',print_background=True)
    browser.close()
print('PDF CREATED')
