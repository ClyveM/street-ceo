import { useEffect, useRef, useState } from 'react'
import { getApiConfig } from './api'
import { clientId } from './clientId'
import { spokenCashCents } from './quickSale'
import { CloseRequestError, closeMoney, createReportsCloseClient, type CashClosePreview, type CashCloseRecord, type CloseInput, type OpeningInput } from './reportsClose'
import './reports-close.css'
type Pending={kind:'opening';input:OpeningInput;key:string}|{kind:'close';input:CloseInput;key:string}
export function useEndDay(prompt:(text:string)=>void){
 const config=useRef(getApiConfig()),client=useRef(createReportsCloseClient(()=>config.current)).current
 const [active,setActive]=useState(false),[stage,setStage]=useState<'cash'|'opening'|'opening_confirm'|'review'|'saved'>('cash'),[busy,setBusy]=useState(false),[uncertain,setUncertain]=useState(false),[error,setError]=useState(''),[answer,setAnswer]=useState('')
 const [preview,setPreview]=useState<CashClosePreview|null>(null),[counted,setCounted]=useState<number|null>(null),[opening,setOpening]=useState<number|null>(null),[receipt,setReceipt]=useState<CashCloseRecord|null>(null)
 const pending=useRef<Pending|null>(null),openingSaved=useRef(false),locked=useRef(false),alive=useRef(true)
 useEffect(()=>{alive.current=true;return()=>{alive.current=false}},[])
 const question=stage==='cash'?'How much cash do you have on hand?':stage==='opening'?'How much cash did you have at the start of this business day?':stage==='opening_confirm'?`Record opening cash ${closeMoney(opening??0)}? Say Yes, No, or Cancel.`:stage==='review'&&preview?.expected_cash_cents!=null&&counted!==null?`Expected cash ${closeMoney(preview.expected_cash_cents)}. Counted ${closeMoney(counted)}. ${counted<preview.expected_cash_cents?'Short':counted>preview.expected_cash_cents?'Over':'Difference'} ${closeMoney(Math.abs(counted-preview.expected_cash_cents))}. Save this cash close? Say Yes, No, or Cancel.`:'Cash check saved.'
 const perform=async(action:()=>Promise<void>)=>{
  if(locked.current)return;locked.current=true;setBusy(true);setError('')
  try{await action()}catch(e){if(!alive.current)return;const unknown=e instanceof CloseRequestError&&e.uncertain;setUncertain(old=>old||unknown);const message=e instanceof Error?e.message:'Cash check unavailable.';setError(message);prompt(unknown||uncertain?'The cash check outcome is unconfirmed. Say Retry to recover the same request. Do not start another close.':message)}finally{locked.current=false;if(alive.current)setBusy(false)}
 }
 const reviewCount=(value:CashClosePreview,cash:number)=>{
  setPreview(value)
  if(value.requires_payment_review||value.expected_cash_cents===null&&!value.requires_opening){setError('Recorded cash payments need review before an expected balance can be verified. Record missing cash-in/out separately; do not invent a balancing adjustment.');prompt('Recorded payments need review. No cash close can be confirmed yet. You can cancel this check.');return}
  if(value.requires_opening){setStage('opening');prompt('What cash did you have at the start of this business day? Say the amount, including zero if there was none.');return}
  setStage('review');const diff=cash-value.expected_cash_cents!;prompt(`Expected cash ${closeMoney(value.expected_cash_cents!)}. Counted ${closeMoney(cash)}. ${diff<0?'Short':diff>0?'Over':'Difference'} ${closeMoney(Math.abs(diff))}. Check any unrecorded cash in or out. Save this cash close? Say Yes, No, or Cancel.`)
 }
 const afterOpening=async()=>{const latest=await client.preview(preview!.business_date);if(latest.requires_opening)throw new Error('The opening record is not yet visible. Keep the original opening request and retry.');pending.current=null;setUncertain(false);reviewCount(latest,counted!)}
 const recover=()=>perform(async()=>{
  const original=pending.current;if(!original)throw new Error('No pending cash request to recover.')
  if(original.kind==='opening'){await client.opening(original.input,original.key);openingSaved.current=true;await afterOpening()}
  else{const saved=await client.confirm(original.input,original.key);setReceipt(saved);setStage('saved');setUncertain(false);pending.current=null;prompt(`Cash close saved. Counted ${closeMoney(saved.cash_counted_cents)}. Bank was not counted.`)}
 })
 const start=()=>perform(async()=>{config.current=getApiConfig();openingSaved.current=false;setActive(true);setStage('cash');setCounted(null);setOpening(null);setReceipt(null);setUncertain(false);pending.current=null;const value=await client.preview();setPreview(value);if(value.saved_close){setReceipt(value.saved_close);setStage('saved');prompt('This business date already has a saved cash close. Review its recorded count and any warnings.');return}prompt('How much cash do you have on hand? Say the amount. You can also type it.')})
 const handle=(raw:string)=>{
  const text=raw.trim().replace(/[.!?]+$/,'').toLowerCase()
  if(pending.current&&/^(retry|recover|try again)$/.test(text))return recover()
  if(openingSaved.current&&pending.current?.kind==='opening'&&!/^(cancel|cancel close|cancel check)$/.test(text)){if(/^(yes|retry|recover|try again)$/.test(text))return recover();prompt('Opening cash is already saved. Say Retry to continue the cash comparison, or Cancel.');return Promise.resolve()}
  if(uncertain){if(/^(retry|recover|try again)$/.test(text))return recover();prompt('Keep this original cash request. Say Retry to recover it.');return Promise.resolve()}
  return perform(async()=>{
   if(/^(cancel|cancel close|cancel check)$/.test(text)){setActive(false);pending.current=null;prompt('Cash check cancelled. Any confirmed opening record stays saved. Say Apo for a sale.');return}
   if(stage==='saved'){if(/^(done|skip|skip stock count|finish|no)$/.test(text)){setActive(false);return}prompt('Cash close is saved. Say Done to return to selling. Stock count is optional.');return}
   if(!preview)throw new Error('Load the cash check before answering. Cancel and start End my day again.')
   if(stage==='cash'||stage==='opening'){
    const amount=spokenCashCents(text.replace(/^(cash|opening|i have|i started with)\s+/,''));if(amount===null)throw new Error('Say a clear cash amount, for example ten dollars or 10.50. Nothing has been guessed.')
    setAnswer('')
    if(stage==='cash'){setCounted(amount);reviewCount(preview,amount)}else{setOpening(amount);setStage('opening_confirm');prompt(`You started with ${closeMoney(amount)}. Record that opening cash? Say Yes, No, or Cancel.`)}
    return
   }
   if(text==='no'){pending.current=null;setStage(stage==='opening_confirm'?'opening':'cash');prompt(stage==='opening_confirm'?'Say the opening cash amount again.':'How much cash do you have on hand?');return}
   if(!/^(yes|yes please|confirm)$/.test(text))throw new Error('Say Yes to confirm, No to change the amount, or Cancel.')
   if(stage==='opening_confirm'&&opening!==null){
    const input:OpeningInput={business_date:preview.business_date,opening_cash_cents:opening,actor:'Shop operator',reason:'Explicit opening cash confirmed during End my day',confirmed:true};const original=pending.current?.kind==='opening'?pending.current:null;const key=original?.key??`web-opening-${clientId()}`;const frozen=original?.input??input;pending.current={kind:'opening',input:frozen,key};await client.opening(frozen,key);openingSaved.current=true;await afterOpening();return
   }
   if(stage==='review'&&counted!==null&&!preview.requires_payment_review&&preview.expected_cash_cents!==null){
    const fresh=await client.preview(preview.business_date)
    if(fresh.saved_close){setReceipt(fresh.saved_close);setStage('saved');prompt('This date already has a saved cash close. No second close was posted.');return}
    if(fresh.preview_version!==preview.preview_version){reviewCount(fresh,counted);setError('Recorded activity changed. Review the updated expected cash before saying Yes again.');return}
    const input:CloseInput={business_date:preview.business_date,cash_counted_cents:counted,actor:'Shop operator',notes:'Cash-only close confirmed; bank not counted',confirmed:true,preview_version:preview.preview_version};const key=`web-cash-close-${clientId()}`;pending.current={kind:'close',input,key};const saved=await client.confirm(input,key);pending.current=null;setReceipt(saved);setStage('saved');prompt(`Cash close saved. Counted ${closeMoney(saved.cash_counted_cents)}. Bank was not counted. Stock count is optional. Say Done to return to selling.`)
   }
  })
 }
 return{active,stage,busy,uncertain,error,answer,setAnswer,preview,counted,opening,receipt,question,start,handle,recover,done:()=>{if(!busy&&!uncertain)setActive(false)},pending,dispose:()=>{alive.current=false}}
}
export type EndDayFlow=ReturnType<typeof useEndDay>
export function EndDayContent({flow,onCount}:{flow:EndDayFlow;onCount?():void}){
 const value=flow.receipt??flow.preview
 const warnings=[...new Set([...(flow.receipt?.warnings??[]),...(flow.preview?.warnings??[])])]
 return <section className="end-day-sheet"><p className="eyebrow">CASH CHECK · BANK NOT COUNTED</p><h2>{flow.receipt?'Cash close saved':'End my day'}</h2><p>{value?.business_date??'Loading business date…'} · {flow.preview?.shop_timezone}</p>
 {flow.receipt?<><dl><dt>Expected cash</dt><dd>{closeMoney(flow.receipt.expected_cash_cents)}</dd><dt>Cash on hand</dt><dd>{closeMoney(flow.receipt.cash_counted_cents)}</dd><dt>Difference</dt><dd className="close-difference">{closeMoney(flow.receipt.cash_variance_cents)}</dd><dt>Bank count / difference</dt><dd>Not counted / unknown</dd></dl><p>Cash close saved. No variance correction or transfer was posted.</p><p>Stock count is optional. You can skip it and keep selling.</p>{onCount&&<button disabled={flow.busy} onClick={onCount}>Open stock count</button>}<button onClick={flow.done}>Skip stock count · Done</button></>:<><p className="close-question">{flow.uncertain?'Outcome unconfirmed — say Retry':flow.question}</p><p>Just answer. No need to say Apo again.</p><details><summary>Type instead</summary><label>Your answer<input value={flow.answer} disabled={flow.busy} onChange={e=>flow.setAnswer(e.target.value)} placeholder="10.50, Yes, No or Cancel"/></label><button disabled={flow.busy||!flow.answer.trim()} onClick={()=>{void flow.handle(flow.answer)}}>Send answer</button>{!flow.uncertain&&<button disabled={flow.busy} onClick={()=>{void flow.handle('Cancel')}}>Cancel check</button>}</details></>}
 {flow.error&&<p role="alert" className="cost-error">{flow.error}</p>}{flow.busy&&<p role="status">Checking with your shop…</p>}{(flow.uncertain||flow.error&&flow.pending.current)&&<button disabled={flow.busy} onClick={()=>{void flow.recover()}}>Recover original cash request</button>}
 <details><summary>Recorded movements & help</summary>{flow.preview&&<dl><dt>Opening ({flow.preview.opening_source})</dt><dd>{flow.preview.opening_cash_cents===null?'Needs your opening':closeMoney(flow.preview.opening_cash_cents)}</dd><dt>Cash sale totals</dt><dd>{closeMoney(flow.preview.sales_cash_cents)}</dd><dt>Paid expenses / purchases</dt><dd>{closeMoney(flow.preview.paid_expenses_cash_cents)} / {flow.preview.paid_purchases_cash_cents===null?'Unknown / needs review':closeMoney(flow.preview.paid_purchases_cash_cents)}</dd><dt>Explicit refunds / adjustments</dt><dd>{closeMoney(flow.preview.refunds_cash_cents)} / {closeMoney(flow.preview.adjustments_cash_cents)}</dd></dl>}<p>Expected cash uses recorded movements. Record missing cash in/out separately; never invent an adjustment to erase a difference. Bank is unknown, not zero.</p><ul>{warnings.map((v,i)=><li key={i}>{v}</li>)}</ul>{flow.receipt&&<p>Receipt {flow.receipt.id} · {flow.receipt.confirmed_at}</p>}{flow.pending.current&&<p>Original retry key: {flow.pending.current.key}</p>}</details>
 </section>
}
