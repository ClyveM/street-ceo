import type { MuseDocument } from './muse'
import type { PdfExport } from './reportShare'

const escapeHtml = (value: string) => value.replace(/[&<>"']/g, character => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[character] ?? character))

export function buildMusePdf(document: MuseDocument): PdfExport {
  const title = 'Business plan'
  const subtitle = document.title
  const rows: PdfExport['rows'] = []
  const sections = document.sections.map(section => {
    rows.push({ kind: 'heading', text: section.title })
    const paragraphs = section.body.split(/\n\s*\n/).map(paragraph => paragraph.trim()).filter(Boolean)
    // Keep normal paragraph breaks. Compact unusually fragmented text for the native row budget.
    const nativeParagraphs = paragraphs.length <= 100 ? paragraphs : [paragraphs.join(' ')]
    for (const paragraph of nativeParagraphs) {
      let remaining = paragraph
      while (remaining.length > 1800) {
        const space = remaining.lastIndexOf(' ', 1800)
        let end = space >= 900 ? space : 1800
        const lastCodeUnit = remaining.charCodeAt(end - 1)
        if (lastCodeUnit >= 0xd800 && lastCodeUnit <= 0xdbff) end--
        rows.push({ kind: 'text', text: remaining.slice(0, end) })
        remaining = remaining.slice(end).trimStart()
      }
      if (remaining) rows.push({ kind: 'text', text: remaining })
    }
    if (section.evidence_ids?.length) rows.push({ kind: 'text', text: 'Evidence: ' + section.evidence_ids.join(', ') })
    return `<section><h2>${escapeHtml(section.title)}</h2>${paragraphs.map(paragraph =>
      `<p>${escapeHtml(paragraph)}</p>`).join('')}${section.evidence_ids?.length
      ? `<aside>Evidence: ${escapeHtml(section.evidence_ids.join(', '))}</aside>` : ''}</section>`
  }).join('')
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>Street CEO · ${escapeHtml(subtitle)}</title><style>
    @page{size:A4;margin:16mm;@bottom-right{content:"Page " counter(page);font:9pt Arial;color:#526b63}}
    body{font:11pt/1.55 Arial,sans-serif;color:#19352c;print-color-adjust:exact;-webkit-print-color-adjust:exact;overflow-wrap:anywhere}
    header{display:flex;align-items:center;gap:18px;background:#084d39;color:#fff;padding:18px 24px;border-radius:10px;break-inside:avoid}
    img{width:62px;height:62px;object-fit:contain;background:#fff;border-radius:10px;padding:3px}
    header span{letter-spacing:.12em;text-transform:uppercase;font-size:9pt;font-weight:700}
    h1{margin:4px 0 0;font-size:22pt;line-height:1.2}
    h2{font-size:14pt;margin:18pt 0 7pt;color:#084d39;break-after:avoid}
    p{margin:0 0 8pt;white-space:pre-wrap;orphans:3;widows:3}
    aside{font-size:9pt;color:#526b63;border-top:1px solid #dce8e1;padding-top:4pt;break-inside:avoid}
    </style></head><body><header><img src="/street-ceo-logo.png" alt="Street CEO"><div><span>Street CEO · Business plan</span><h1>${escapeHtml(subtitle)}</h1></div></header>${sections}</body></html>`
  return { filename: 'street-ceo-business-plan', title, subtitle, rows, html }
}
