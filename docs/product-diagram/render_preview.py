"""Export this diagram's supported SVG primitives to PDF/PNG, without browser/GPU.
Optional --browser checks real HTML widths and captures mobile through CDP.
Requires ReportLab, Poppler pdftoppm; optional Playwright + Microsoft Edge.
"""
from pathlib import Path
import base64
import re
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

out = Path(__file__).resolve().parent
root = ET.parse(out / 'street-ceo-product.svg').getroot()
width, height = (float(root.attrib[x]) for x in ('width', 'height'))
for name, filename in [('Arial', 'arial.ttf'), ('ArialBold', 'arialbd.ttf')]:
    font = Path('C:/Windows/Fonts') / filename
    pdfmetrics.registerFont(TTFont(name, str(font)))
styles = {}
for selector, declarations in re.findall(r'([^{}]+)\{([^{}]+)\}', root.find('{*}style').text):
    styles[selector.strip()] = dict(item.strip().split(':', 1) for item in declarations.split(';') if ':' in item)
pdf = canvas.Canvas(str(out / 'street-ceo-product.pdf'), pagesize=(width, height))
pdf.setTitle('Street CEO — from spoken basket to saved sale')
pdf.translate(0, height)
pdf.scale(1, -1)

def paint(node):
    tag = node.tag.rsplit('}', 1)[-1]
    if tag in ('defs', 'style', 'title', 'desc'):
        return
    if tag in ('svg', 'g'):
        for child in node:
            paint(child)
        return
    style = dict(styles.get('text', {}) if tag == 'text' else {})
    for cls in node.get('class', '').split():
        style.update(styles.get('.' + cls, {}))
    style.update(node.attrib)
    fill = style.get('fill', '#000000')
    if re.fullmatch(r'#[0-9a-fA-F]{3}', fill): fill = '#' + ''.join(c*2 for c in fill[1:])
    stroke = style.get('stroke', 'none')
    pdf.saveState()
    if fill != 'none': pdf.setFillColor(fill)
    if stroke != 'none': pdf.setStrokeColor(stroke)
    pdf.setLineWidth(float(style.get('stroke-width', 1)))
    pdf.setDash([float(x) for x in style.get('stroke-dasharray', '').split()])
    if tag == 'rect':
        x, y, w, h = [float(node.get(k, 0)) for k in ('x', 'y', 'width', 'height')]
        pdf.roundRect(x, y, w, h, float(node.get('rx', 0)), stroke=stroke != 'none', fill=fill != 'none')
    elif tag == 'text':
        size = float(style.get('font-size', '17px').replace('px', ''))
        pdf.translate(float(node.get('x', 0)), float(node.get('y', 0)))
        pdf.scale(1, -1)
        text = pdf.beginText(0, 0)
        text.setFont('ArialBold' if style.get('font-weight') == '700' else 'Arial', size)
        text.setCharSpace(float(style.get('letter-spacing', '0px').replace('px', '')))
        text.textOut(''.join(node.itertext()))
        pdf.drawText(text)
    elif tag == 'path':
        tokens = re.findall(r'[A-Za-z]|-?\d+(?:\.\d+)?', node.get('d', ''))
        path = pdf.beginPath(); i = 0; x = y = 0; before = (0, 0)
        while i < len(tokens):
            cmd = tokens[i]; i += 1; before = (x, y)
            if cmd in ('M', 'L'):
                x, y = float(tokens[i]), float(tokens[i+1]); i += 2
                (path.moveTo if cmd == 'M' else path.lineTo)(x, y)
            elif cmd == 'H': x = float(tokens[i]); i += 1; path.lineTo(x, y)
            elif cmd == 'V': y = float(tokens[i]); i += 1; path.lineTo(x, y)
            elif cmd in ('Z', 'z'): path.close()
            else: raise ValueError('Unsupported SVG path command ' + cmd)
        pdf.drawPath(path, stroke=stroke != 'none', fill=fill != 'none')
        if style.get('marker-end'):
            # Match SVG markerWidth=7, refX=9 with a compact filled arrowhead.
            dx, dy = x-before[0], y-before[1]
            length = max((dx*dx+dy*dy)**.5, 1); ux, uy = dx/length, dy/length
            arrow = pdf.beginPath(); arrow.moveTo(x+ux*1.5,y+uy*1.5)
            arrow.lineTo(x-ux*13-uy*6,y-uy*13+ux*6)
            arrow.lineTo(x-ux*13+uy*6,y-uy*13-ux*6); arrow.close()
            pdf.setFillColor(stroke); pdf.setDash([]); pdf.drawPath(arrow, stroke=0, fill=1)
    else:
        raise ValueError('Unsupported SVG primitive: ' + tag)
    pdf.restoreState()

paint(root)
pdf.showPage(); pdf.save()
converter = shutil.which('pdftoppm')
if not converter: raise SystemExit('PDF exported. Install Poppler pdftoppm to generate the PNG preview.')
subprocess.run([converter, '-png', '-singlefile', '-r', '96', str(out/'street-ceo-product.pdf'), str(out/'street-ceo-product')], check=True, timeout=30)
print('Vector PDF + rendered PNG exported from current SVG source.', flush=True)
if '--browser' in sys.argv:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True, timeout=20000, args=['--disable-gpu'])
        page = browser.new_page(viewport={'width': 390, 'height': 844})
        page.goto((out/'index.html').as_uri(), timeout=15000, wait_until='domcontentloaded')
        for w in (390, 320):
            page.set_viewport_size({'width':w,'height':844})
            dims=page.evaluate('({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})')
            assert dims['client']==dims['scroll'],dims
            assert page.locator('.mobile').is_visible()
            print(w,dims,flush=True)
        browser.close()
