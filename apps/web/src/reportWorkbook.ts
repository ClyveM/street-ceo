type Cell = string | { number: string }

type WorkbookReport = {
  title: string
  subtitle: string
  summaryCells: Cell[][]
  productCells: Cell[][]
  notes: string[]
}

const xmlHeader = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
const sheetNamespace = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
const relationshipNamespace = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
const packageNamespace = 'http://schemas.openxmlformats.org/package/2006/relationships'
const marginLabel = 'Gross margin (%)'
const encoder = new TextEncoder()

function xml(value: string): string {
  return value.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\ufffe\uffff]/g, ' ')
    .replace(/_x[\da-f]{4}_/gi, token => '_x005F_' + token.slice(1))
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function cell(value: Cell, reference: string, style: number, percent: boolean): string {
  if (typeof value === 'string') {
    return '<c r="' + reference + '" s="' + style + '" t="inlineStr"><is><t xml:space="preserve">' + xml(value) + '</t></is></c>'
  }
  if (!/^-?\d+(?:\.\d+)?$/.test(value.number)) throw new Error('Invalid workbook number.')
  const format = percent ? style + 2 : value.number.includes('.') ? style + 1 : style
  const numeric = percent ? Number(value.number) / 100 : value.number
  return '<c r="' + reference + '" s="' + format + '"><v>' + numeric + '</v></c>'
}

function worksheet(model: WorkbookReport, detail: boolean): string {
  const grid = detail ? model.productCells : model.summaryCells
  const width = detail ? Math.max(1, grid[0]?.length ?? 0) : 2
  const lastColumn = String.fromCharCode(64 + width)
  const merges: string[] = []
  const rows: string[] = []
  const addBanner = (value: string, style: number, height: number) => {
    const row = rows.length + 1
    merges.push('A' + row + ':' + lastColumn + row)
    rows.push('<row r="' + row + '" ht="' + height + '" customHeight="1">' + cell(value, 'A' + row, style, false) + '</row>')
  }
  addBanner('STREET CEO  /  ' + (detail ? 'PRODUCT DETAIL' : 'SHOP REPORT'), 1, 23)
  addBanner(model.title, 2, 30)
  addBanner(model.subtitle, 3, 25)
  rows.push('<row r="4" ht="8" customHeight="1"/>')
  for (const [index, line] of grid.entries()) {
    const row = rows.length + 1
    const style = index === 0 ? 4 : index % 2 ? 5 : 8
    const cells = line.map((value, column) => {
      const isPercent = index > 0 && (detail ? grid[0][column] === marginLabel : line[0] === marginLabel)
      return cell(value, String.fromCharCode(65 + column) + row, style, isPercent)
    })
    rows.push('<row r="' + row + '" ht="' + (index === 0 ? 30 : 23) + '" customHeight="1">' + cells.join('') + '</row>')
  }
  const tableEnd = rows.length
  if (!detail && model.notes.length) {
    rows.push('<row r="' + (rows.length + 1) + '" ht="8" customHeight="1"/>')
    addBanner('COVERAGE & NOTES', 4, 24)
    for (const note of model.notes) addBanner(note, 3, Math.max(25, Math.ceil(note.length / 62) * 16))
  }
  const columnWidths = detail ? [36, 17, 19, 14, 19, 19, 26, 19, 19, 19] : [38, 30]
  const columns = columnWidths.slice(0, width).map((size, index) =>
    '<col min="' + (index + 1) + '" max="' + (index + 1) + '" width="' + size + '" customWidth="1"/>').join('')
  const freeze = detail ? '<pane ySplit="5" topLeftCell="A6" activePane="bottomLeft" state="frozen"/><selection pane="bottomLeft" activeCell="A6" sqref="A6"/>' : ''
  const filter = detail && tableEnd > 5 ? '<autoFilter ref="A5:' + lastColumn + tableEnd + '"/>' : ''
  return xmlHeader + '<worksheet xmlns="' + sheetNamespace + '"><sheetViews><sheetView workbookViewId="0" showGridLines="0">' + freeze +
    '</sheetView></sheetViews><sheetFormatPr defaultRowHeight="20"/><cols>' + columns + '</cols><sheetData>' + rows.join('') + '</sheetData>' +
    filter + '<mergeCells count="' + merges.length + '">' + merges.map(ref => '<mergeCell ref="' + ref + '"/>').join('') +
    '</mergeCells></worksheet>'
}

const styles = xmlHeader + '<styleSheet xmlns="' + sheetNamespace + '">' +
  '<numFmts count="1"><numFmt numFmtId="164" formatCode="#,##0.00####;[Red]-#,##0.00####;0.00"/></numFmts>' +
  '<fonts count="4"><font><sz val="11"/><color rgb="FF163E34"/><name val="Calibri"/></font>' +
  '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>' +
  '<font><b/><sz val="19"/><color rgb="FF104735"/><name val="Calibri"/></font>' +
  '<font><sz val="10"/><color rgb="FF49675D"/><name val="Calibri"/></font></fonts>' +
  '<fills count="5"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>' +
  '<fill><patternFill patternType="solid"><fgColor rgb="FF104735"/><bgColor indexed="64"/></patternFill></fill>' +
  '<fill><patternFill patternType="solid"><fgColor rgb="FFE6F2ED"/><bgColor indexed="64"/></patternFill></fill>' +
  '<fill><patternFill patternType="solid"><fgColor rgb="FFF0F7F4"/><bgColor indexed="64"/></patternFill></fill></fills>' +
  '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>' +
  '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>' +
  '<cellXfs count="11">' +
  [[0,0,0],[1,2,0],[2,3,0],[3,3,0],[1,2,0],[0,0,0],[0,0,164],[0,0,10],[0,4,0],[0,4,164],[0,4,10]]
    .map(([font,fill,format]) => '<xf numFmtId="' + format + '" fontId="' + font + '" fillId="' + fill +
      '" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>').join('') +
  '</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'

const crcTable = Uint32Array.from({length:256}, (_, value) => {
  for (let bit = 0; bit < 8; bit++) value = (value >>> 1) ^ (value & 1 ? 0xedb88320 : 0)
  return value >>> 0
})

function crc32(bytes: Uint8Array): number {
  let crc = 0xffffffff
  for (const byte of bytes) crc = (crc >>> 8) ^ crcTable[(crc ^ byte) & 255]
  return (crc ^ 0xffffffff) >>> 0
}

/** OOXML uses ZIP; small report parts are stored uncompressed for offline export. */
function zip(parts: Record<string,string>): Uint8Array {
  const files = Object.entries(parts).map(([name, text]) => ({name: encoder.encode(name), data: encoder.encode(text)}))
  const localSize = files.reduce((total, file) => total + 30 + file.name.length + file.data.length, 0)
  const directorySize = files.reduce((total, file) => total + 46 + file.name.length, 0)
  const bytes = new Uint8Array(localSize + directorySize + 22)
  const view = new DataView(bytes.buffer)
  const u16 = (offset: number, value: number) => view.setUint16(offset, value, true)
  const u32 = (offset: number, value: number) => view.setUint32(offset, value, true)
  let local = 0
  let directory = localSize
  for (const {name, data} of files) {
    const crc = crc32(data)
    u32(local, 0x04034b50)
    u16(local + 4, 20)
    u16(local + 12, 33) // 1980-01-01 DOS date
    u32(local + 14, crc)
    u32(local + 18, data.length)
    u32(local + 22, data.length)
    u16(local + 26, name.length)
    bytes.set(name, local + 30)
    bytes.set(data, local + 30 + name.length)
    u32(directory, 0x02014b50)
    u16(directory + 4, 20)
    u16(directory + 6, 20)
    u16(directory + 14, 33)
    u32(directory + 16, crc)
    u32(directory + 20, data.length)
    u32(directory + 24, data.length)
    u16(directory + 28, name.length)
    u32(directory + 42, local)
    bytes.set(name, directory + 46)
    local += 30 + name.length + data.length
    directory += 46 + name.length
  }
  u32(directory, 0x06054b50)
  u16(directory + 8, files.length)
  u16(directory + 10, files.length)
  u32(directory + 12, directorySize)
  u32(directory + 16, localSize)
  return bytes
}

export function buildReportWorkbook(model: WorkbookReport): Uint8Array {
  const workbookType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.'
  const overrides = [
    ['/xl/workbook.xml', 'sheet.main+xml'],
    ['/xl/worksheets/sheet1.xml', 'worksheet+xml'],
    ['/xl/worksheets/sheet2.xml', 'worksheet+xml'],
    ['/xl/styles.xml', 'styles+xml'],
  ].map(([name, kind]) => '<Override PartName="' + name + '" ContentType="' + workbookType + kind + '"/>').join('')
  const relationship = (id: string, type: string, target: string) =>
    '<Relationship Id="' + id + '" Type="' + relationshipNamespace + '/' + type + '" Target="' + target + '"/>'
  const relationships = (...items: string[]) =>
    xmlHeader + '<Relationships xmlns="' + packageNamespace + '">' + items.join('') + '</Relationships>'
  return zip({
    '[Content_Types].xml': xmlHeader + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' +
      '<Default Extension="xml" ContentType="application/xml"/>' + overrides + '</Types>',
    '_rels/.rels': relationships(relationship('rId1','officeDocument','xl/workbook.xml')),
    'xl/workbook.xml': xmlHeader + '<workbook xmlns="' + sheetNamespace + '" xmlns:r="' + relationshipNamespace +
      '"><bookViews><workbookView/></bookViews><sheets><sheet name="Summary" sheetId="1" r:id="rId1"/><sheet name="Products" sheetId="2" r:id="rId2"/></sheets></workbook>',
    'xl/_rels/workbook.xml.rels': relationships(
      relationship('rId1','worksheet','worksheets/sheet1.xml'),
      relationship('rId2','worksheet','worksheets/sheet2.xml'),
      relationship('rId3','styles','styles.xml')),
    'xl/styles.xml': styles,
    'xl/worksheets/sheet1.xml': worksheet(model,false),
    'xl/worksheets/sheet2.xml': worksheet(model,true),
  })
}
