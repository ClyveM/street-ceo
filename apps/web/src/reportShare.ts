import type { ReportExport } from './reportExport'
type ExportPlugin={shareCsv(options:{filename:string;content:string}):Promise<unknown>;sharePdf(options:{filename:string;title:string;subtitle:string;rows:{kind:string;text:string}[]}):Promise<unknown>}
type ExportWindow=Window&{Capacitor?:{getPlatform?():string;registerPlugin?(name:string):ExportPlugin;Plugins?:{StreetReportExport?:ExportPlugin}}}
export async function deliverReport(model:ReportExport,format:'csv'|'pdf'):Promise<string>{
 const cap=(window as ExportWindow).Capacitor
 if(cap?.getPlatform?.()==='android'){
  const plugin=cap.registerPlugin?.('StreetReportExport')??cap.Plugins?.StreetReportExport
  if(!plugin)throw new Error('Report sharing is unavailable in this APK. Install the updated build.')
  if(format==='csv')await plugin.shareCsv({filename:model.filename,content:model.csv})
  else await plugin.sharePdf({filename:model.filename,title:model.title,subtitle:model.subtitle,rows:model.rows})
  return 'Share sheet opened. Choose where to send or save your report.'
 }
 if(format==='pdf'){
  const popup=window.open('','_blank');if(!popup)throw new Error('Allow the report window, then try PDF again.')
  popup.opener=null
  try{
   const logo=await fetch(new URL('/street-ceo-logo.png',window.location.origin).href,{cache:'force-cache',signal:AbortSignal.timeout(15000)})
   if(!logo.ok)throw new Error('The bundled logo could not be loaded.')
   const bytes=new Uint8Array(await logo.arrayBuffer());if(bytes.length>2000000||![137,80,78,71,13,10,26,10].every((byte,index)=>bytes[index]===byte))throw new Error('The bundled logo could not be verified.')
   let binary='';for(let start=0;start<bytes.length;start+=8192)binary+=String.fromCharCode(...bytes.subarray(start,start+8192))
   const html=model.html.replace(/<img src="[^"]*"/,`<img src="data:image/png;base64,${btoa(binary)}"`)
   popup.document.open();popup.document.write(html);popup.document.close()
   await Promise.all(Array.from(popup.document.images).map(image=>image.decode()))
   popup.focus();popup.print()
  }catch{popup.close();throw new Error('The branded PDF could not load its logo. No incomplete report was printed; try again.')}
  return 'Print window opened. Choose Save as PDF to save the branded report.'
 }
 const file=new File([model.csv],`${model.filename}.csv`,{type:'text/csv;charset=utf-8'})
 if(navigator.canShare?.({files:[file]})){await navigator.share({files:[file],title:`Street CEO · ${model.title}`});return 'Report share completed.'}
 const url=URL.createObjectURL(file),link=document.createElement('a');link.href=url;link.download=file.name;link.click();setTimeout(()=>URL.revokeObjectURL(url),30000)
 return 'CSV download started. CSV is a text spreadsheet format; the PDF includes the logo.'
}
