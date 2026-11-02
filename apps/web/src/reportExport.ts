import type { SalesReport } from './reportsClose'
export type ExportRow = { kind: 'heading'|'text'; text: string }
export type ReportExport = { filename: string; title: string; subtitle: string; csv: string; rows: ExportRow[]; html: string }
type Numeric = { number: string }
type Cell = string | Numeric
const exact=(value:number|null|undefined,scale:bigint):string=>{if(typeof value!=='number')return 'Unknown';const n=BigInt(value),a=n<0n?-n:n;return `${n<0n?'-':''}${a/scale}.${String(a%scale).padStart(String(scale).length-1,'0')}`}
const margin=(bps:number|null|undefined,revenue:number|null,profit:number|null|undefined)=>typeof bps==='number'?exact(bps,100n):bps===null&&revenue===0&&typeof profit==='number'?'Not defined':'Unknown'
const number=(value:string):Cell=>/^-?\d+(?:\.\d+)?$/.test(value)?{number:value}:value
export function csvCell(value:Cell):string {
 let text=typeof value==='string'?value:value.number
 if(typeof value!=='string'&&!/^-?\d+(?:\.\d+)?$/.test(text))throw new Error('Unverified numeric export cell.')
 if(typeof value==='string'){text=text.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g,' ');if(/^[\s\ufeff]*[=+\-@]/.test(text))text=`'${text}`}
 return `"${text.replace(/"/g,'""')}"`
}
const escape=(value:string)=>value.replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]!))
export function buildReportExport(report:SalesReport,mode:'sales'|'profit',logoUrl='/street-ceo-logo.png'):ReportExport {
 const title=mode==='profit'?'Product gross profit report':'Sales report',subtitle=`${report.start_date} to ${report.end_date} · ${report.currency} · ${report.shop_timezone}`
 const csv:Cell[][]=[['Street CEO',title],['Period',report.start_date,report.end_date],['Currency',report.currency],['Shop timezone',report.shop_timezone],['Coverage',report.coverage,report.coverage_end_date],['As of',report.as_of],['Basis','Saved shop records; customer receipts and daily summaries are counted separately. Gross profit is before shop expenses. Stock-only Undo does not reverse sales or cash.'],[]]
 const rows:ExportRow[]=[{kind:'text',text:`Saved records as of ${report.as_of}`},{kind:'text',text:`Coverage: ${report.coverage} through ${report.coverage_end_date}`},{kind:'heading',text:'Summary'}]
 const summary:[string,string,'currency'|'percent'|'count'][]=[['Recorded sales',exact(report.summary.sales_total_cents,100n),'currency'],['Customer receipts',String(report.summary.transaction_count),'count']]
 if(typeof report.summary.daily_summary_count==='number')summary.push(['Daily summaries',String(report.summary.daily_summary_count),'count'])
 if(mode==='profit')summary.push(['Recorded COGS',exact(report.summary.cogs_micros,1000000n),'currency'],['Gross profit before expenses',exact(report.summary.gross_profit_micros,1000000n),'currency'],['Gross margin (%)',margin(report.summary.margin_bps,report.summary.sales_total_cents,report.summary.gross_profit_micros),'percent'])
 else summary.push(['Cash sales',exact(report.summary.cash_sales_cents,100n),'currency'],['Bank tender recorded',exact(report.summary.bank_sales_cents,100n),'currency'],['Other tender',exact(report.summary.other_tender_sales_cents,100n),'currency'])
 csv.push(['Metric','Recorded value']);for(const [label,value,unit]of summary){csv.push([label,number(value)]);rows.push({kind:'text',text:`${label}: ${value}${unit==='percent'?(/^-?\d/.test(value)?'%':''):unit==='count'?'':` ${report.currency}`}`})}
 csv.push([],mode==='profit'?['Product','SKU','Label source','Units sold','Saved sales','Recorded COGS','Gross profit before expenses','Gross margin (%)','Revenue status','Cost status']:['Product','SKU','Label source','Units sold','Saved sales','Revenue status'])
 rows.push({kind:'heading',text:mode==='profit'?'Profit by product':'Sales by product'})
 for(const p of report.products){const sales=exact(p.revenue_cents,100n),cost=exact(p.cogs_micros,1000000n),profit=exact(p.gross_profit_micros,1000000n),marginValue=margin(p.margin_bps,p.revenue_cents,p.gross_profit_micros)
  const base:Cell[]=[p.product_name,p.sku??'',p.label_source,number(String(p.quantity_sold)),number(sales)]
  csv.push(mode==='profit'?[...base,number(cost),number(profit),number(marginValue),p.revenue_cents===null?'Incomplete':'Complete',typeof p.cogs_micros==='number'?'Complete':'Incomplete']:[...base,p.revenue_cents===null?'Incomplete':'Complete'])
  rows.push({kind:'heading',text:`${p.product_name} · ${p.quantity_sold} units`},{kind:'text',text:`Saved sales: ${sales} ${report.currency}${mode==='profit'?` | COGS: ${cost} | Gross profit: ${profit} | Margin: ${marginValue}${/^-?\d/.test(marginValue)?'%':''}`:''}`})
 }
 if(!report.products.length)rows.push({kind:'text',text:'No saved product sales in this verified period.'})
 csv.push([],['Notes']);const notes=['Amounts use saved receipt evidence, never current catalogue prices or costs.','Unknown values are not zero. Margin is not defined on zero revenue.','Gross profit is before shop expenses; this is not net profit.','Starter product costs are illustrative, not supplier-verified.',...report.warnings]
 if((report.summary.missing_cogs_daily_summary_count??0)>0)notes.unshift(`${report.summary.missing_cogs_daily_summary_count} daily summaries have missing cost; profit is incomplete.`)
 if(report.summary.missing_cogs_sale_count>0)notes.unshift(`${report.summary.missing_cogs_sale_count} sale(s) have missing cost; profit is incomplete.`)
 for(const note of notes){csv.push([note]);rows.push({kind:'text',text:note})}
 const body=rows.map(row=>row.kind==='heading'?`<h2>${escape(row.text)}</h2>`:`<p>${escape(row.text)}</p>`).join('')
 const html=`<!doctype html><html><head><meta charset="utf-8"><title>Street CEO · ${escape(title)}</title><style>@page{size:A4;margin:18mm;@bottom-right{content:"Page " counter(page);font:9px Arial;color:#7a8c70}}body{font:12px Arial,sans-serif;color:#183e33;line-height:1.6}header{display:flex;align-items:center;gap:18px;border-bottom:3px solid #1c6b50;padding-bottom:18px;margin-bottom:20px}img{width:66px;height:66px;object-fit:contain}h1{font-size:24px;margin:0}header p{margin:4px 0 0;color:#6e8668}h2{font-size:15px;margin:20px 0 6px;break-after:avoid}p{margin:5px 0;overflow-wrap:anywhere}footer{font-size:10px;color:#7a8c70;margin-top:24px;border-top:1px solid #dfe8d5;padding-top:12px}</style></head><body><header><img src="${escape(logoUrl)}" alt="Street CEO"><div><h1>Street CEO</h1><strong>${escape(title)}</strong><p>${escape(subtitle)}</p></div></header>${body}<footer>Saved records as of ${escape(report.as_of)}. Coverage: ${escape(report.coverage)} through ${escape(report.coverage_end_date)}.</footer></body></html>`
 return {filename:`street-ceo-${mode}-${report.start_date}-to-${report.end_date}`,title,subtitle,csv:'\ufeff'+csv.map(row=>row.map(csvCell).join(',')).join('\r\n')+'\r\n',rows,html}
}
