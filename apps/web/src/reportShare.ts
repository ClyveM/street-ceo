import type { ReportExport } from './reportExport'
type DownloadResult = { opened: boolean; savedToDownloads: boolean }
const XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
type ExportPlugin={
 downloadXlsx(options:{filename:string;content:string}):Promise<DownloadResult>;
downloadCsv(options:{filename:string;content:string}):Promise<DownloadResult>;downloadPdf(options:{filename:string;title:string;subtitle:string;rows:{kind:string;text:string}[];summary:string[][];columns:string[];products:string[][];notes:string[]}):Promise<DownloadResult>}
type ExportWindow=Window&{Capacitor?:{getPlatform?():string;registerPlugin?(name:string):ExportPlugin;Plugins?:{StreetReportExport?:ExportPlugin}}}
export async function deliverReport(model:ReportExport,format:'csv'|'pdf'|'xlsx'):Promise<string>{
 const workbook = format === 'xlsx'
  ? (await import('./reportWorkbook')).buildReportWorkbook(model)
  : null
 const cap=(window as ExportWindow).Capacitor
 if(cap?.getPlatform?.()==='android'){
  const plugin=cap.registerPlugin?.('StreetReportExport')??cap.Plugins?.StreetReportExport
  if(!plugin)throw new Error('Report downloads are unavailable in this APK. Install the updated build.')
  const result = format === 'csv'
   ? await plugin.downloadCsv({filename:model.filename,content:model.csv})
   : workbook
    ? await plugin.downloadXlsx({filename:model.filename,content:encodeBase64(workbook)})
    : await plugin.downloadPdf({
     filename:model.filename,title:model.title,subtitle:model.subtitle,rows:model.rows,
     summary:model.summary,columns:model.columns,products:model.products,notes:model.notes,
    })
  const location = result.savedToDownloads ? 'Downloads' : 'the selected location'
  return result.opened ? `Report saved to ${location} and opened.` : `Report saved to ${location}. Open it in Files with a compatible app.`
 }
 if(format==='pdf'){
  const popup=window.open('','_blank');if(!popup)throw new Error('Allow the report window, then try PDF again.')
  popup.opener=null
  try{
   const logo=await fetch(new URL('/street-ceo-logo.png',window.location.origin).href,{cache:'force-cache',signal:AbortSignal.timeout(15000)})
   if(!logo.ok)throw new Error('The bundled logo could not be loaded.')
   const bytes=new Uint8Array(await logo.arrayBuffer());if(bytes.length>2000000||![137,80,78,71,13,10,26,10].every((byte,index)=>bytes[index]===byte))throw new Error('The bundled logo could not be verified.')

   const html=model.html.replace(/<img src="[^"]*"/,`<img src="data:image/png;base64,${encodeBase64(bytes)}"`)
   popup.document.open();popup.document.write(html);popup.document.close()
   await Promise.all(Array.from(popup.document.images).map(image=>image.decode()))
   popup.focus();popup.print()
  }catch{popup.close();throw new Error('The branded PDF could not load its logo. No incomplete report was printed; try again.')}
  return 'Print window opened. Choose Save as PDF to save the branded report.'
 }
 const file=workbook?new File([new Uint8Array(workbook)],`${model.filename}.xlsx`,{type:XLSX_MIME}):new File([model.csv],`${model.filename}.csv`,{type:'text/csv;charset=utf-8'})
 const url=URL.createObjectURL(file),link=document.createElement('a');link.href=url;link.download=file.name;link.click();setTimeout(()=>URL.revokeObjectURL(url),30000)
 if (workbook) return 'Excel download started.'
 return 'CSV download started. CSV is a text spreadsheet format; the PDF includes the logo.'
}

function encodeBase64(bytes: Uint8Array): string {
 let binary = ''
 for (let start = 0; start < bytes.length; start += 8192) {
  binary += String.fromCharCode(...bytes.subarray(start, start + 8192))
 }
 return btoa(binary)
}
