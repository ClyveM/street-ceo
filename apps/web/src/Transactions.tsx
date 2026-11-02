import { useEffect, useRef, useState } from 'react'
import type { Product, Sale } from './api'
import { receiptMoney, receiptTender, savedReceiptLines, savedReceiptPayment, sortedSavedReceipts } from './receiptHistory'
import './sales-history.css'
const dateLabel=(stamp:string)=>new Date(stamp).toLocaleDateString(undefined,{day:'numeric',month:'short',year:'numeric'})
const timeLabel=(stamp:string)=>new Date(stamp).toLocaleTimeString(undefined,{hour:'2-digit',minute:'2-digit'})

function SavedReceipt({sale,products,currency}:{sale:Sale;products:Product[];currency?:string}) {
 let lines:ReturnType<typeof savedReceiptLines>|null=null
 try { lines=savedReceiptLines(sale,products) } catch { /* Saved totals remain visible; malformed item details are never invented. */ }
 const payment=savedReceiptPayment(sale),amount=(cents:number)=>`${currency?`${currency} `:''}${receiptMoney(cents)}${currency?'':' (shop currency)'}`
 return <>
  <div className="history-receipt-total"><span>Sale total</span><strong>{amount(sale.total_cents)}</strong><p>{receiptTender(sale.tender)} · {dateLabel(sale.created_at)} at {timeLabel(sale.created_at)}</p></div>
  <div className="history-payment"><div><span>Amount received</span><strong>{payment.received===null?'Not supplied':amount(payment.received)}</strong></div><div><span>Change</span><strong>{payment.change===null?'Not supplied':amount(payment.change)}</strong></div></div>
  {sale.tender==='cash'&&payment.received===null&&<p className="history-legacy-note">This older receipt did not save cash received. Exact payment and change are unknown.</p>}
  <section className="history-receipt-products"><h4>Products sold</h4>{lines?<ul>{lines.map((line,index)=><li key={`${line.productId}-${index}`}><div><strong>{line.label}</strong><small>{line.historicalName?'Saved product name':line.currentName?'Current catalogue name':'Product reference'}</small></div><span>× {line.quantity}</span></li>)}</ul>:<p className="history-error" role="alert">Saved product details could not be verified. No items have been guessed.</p>}</section>
  <details className="history-receipt-more"><summary>Receipt reference & stock snapshot</summary><dl><dt>Full receipt reference</dt><dd><code>{sale.id}</code></dd><dt>Recorded at</dt><dd><time dateTime={sale.created_at}>{new Date(sale.created_at).toLocaleString()}</time></dd></dl>{sale.tender==='bank'&&<p>Bank is recorded tender; settlement is not verified.</p>}{lines&&<ul>{lines.map((line,index)=><li key={`${line.productId}-${index}`}>{line.label}: stock after sale {line.stockAfter===null?'not saved':line.stockAfter} · product reference <code>{line.productId}</code></li>)}</ul>}<p>Quantities and stock snapshots come from the saved receipt. Stock may have changed since. No current price or cost is used to reconstruct this sale.</p></details>
 </>
}
export function Transactions({sales,products,error,onBack,currency,shopId,loading=false,onRefresh,onOpenDaily}:{sales:Sale[];products:Product[];error:string;onBack():void;currency?:string;shopId?:string;loading?:boolean;onRefresh?():Promise<unknown>;onOpenDaily?():void}) {
 const [selectedId,setSelectedId]=useState<string|null>(null),panel=useRef<HTMLElement>(null),buttons=useRef(new Map<string,HTMLButtonElement>()),back=useRef<HTMLButtonElement>(null)
 let rows:Sale[]|null=null,validationError=''
 try { rows=sortedSavedReceipts(sales,shopId) } catch(failure) { validationError=failure instanceof Error?failure.message:'Saved history could not be verified.' }
 const selected=rows?.find(sale=>sale.id===selectedId)
 useEffect(()=>{if(selectedId){panel.current?.focus({preventScroll:true});panel.current?.scrollIntoView({block:'start'})}},[selectedId])
 const open=(id:string)=>{setSelectedId(id);if(id===selectedId){panel.current?.focus({preventScroll:true});panel.current?.scrollIntoView({block:'start'})}}
 const close=()=>{const id=selectedId;setSelectedId(null);requestAnimationFrame(()=>{(id?buttons.current.get(id):null)?.focus();if(!id||!buttons.current.has(id))back.current?.focus()})}
 const failure=validationError||error
 return <section className="sales-history-page">
  <header className="history-heading"><div><p className="eyebrow">EVERY SALE, KEPT SAFE</p><h2>Sales history</h2></div><button ref={back} onClick={onBack}>← Back to Today</button></header>
  <div className="history-toolbar"><div><strong>Customer receipts</strong><p>Tap a sale to view its saved receipt. Daily sales summaries are kept separately.</p>{onOpenDaily&&<button onClick={onOpenDaily}>Daily sales summaries</button>}</div>{onRefresh&&<button disabled={loading} onClick={()=>{void onRefresh()}}>↻ Refresh</button>}</div>
  {loading&&<p className="history-loading" role="status">Loading saved receipts…</p>}
  {failure&&<section className="history-error" role="alert"><strong>History could not be fully loaded.</strong><p>{failure}</p>{!validationError&&rows&&rows.length>0&&<p>Previously loaded receipts are shown below.</p>}{onRefresh&&<button disabled={loading} onClick={()=>{void onRefresh()}}>Try again</button>}</section>}
  {rows&&rows.length>0&&<div className="history-table-wrap" role="region" aria-label="Sales history table, scroll horizontally for wide values" tabIndex={0}><table className="sales-history-table"><colgroup><col className="history-date-column"/><col className="history-payment-column"/><col className="history-total-column"/></colgroup><thead><tr><th scope="col">Date</th><th scope="col">Payment</th><th scope="col">Total<small>{currency??'Shop currency'}</small></th></tr></thead><tbody>{rows.map(sale=><tr key={sale.id} data-selected={sale.id===selectedId||undefined} onClick={()=>open(sale.id)}><td><button ref={node=>{if(node)buttons.current.set(sale.id,node);else buttons.current.delete(sale.id)}} onClick={event=>{event.stopPropagation();open(sale.id)}} aria-controls="history-selected-receipt" aria-expanded={sale.id===selectedId} aria-label={`Open receipt ${sale.id}`}><strong>{dateLabel(sale.created_at)}</strong><span>{timeLabel(sale.created_at)}</span></button></td><td><span className={`history-tender ${sale.tender==='cash'?'cash':'bank'}`}>{receiptTender(sale.tender)}</span></td><td className="history-total-value">{receiptMoney(sale.total_cents)}</td></tr>)}</tbody></table></div>}
  {!loading&&!failure&&rows?.length===0&&<div className="history-empty"><span aria-hidden="true">↗</span><h3>Customer receipts will appear here.</h3><p>No saved customer receipts yet. Complete a sale from Sell and find its receipt here.</p></div>}
  {selectedId&&<section ref={panel} tabIndex={-1} id="history-selected-receipt" className="history-selected-receipt" aria-label="Saved sale receipt" onKeyDown={event=>{if(event.key==='Escape'){event.preventDefault();close()}}}><header><div><p className="eyebrow">YOUR SAVED RECEIPT</p><h3>Sale details</h3></div><button onClick={close} aria-label="Close saved receipt">Close</button></header>{selected?<SavedReceipt sale={selected} products={products} currency={currency}/>:<p role="alert">This receipt is not in the latest verified history. Refresh to check it again.</p>}</section>}
 </section>
}
