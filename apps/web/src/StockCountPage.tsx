import { useEffect, useRef, useState } from 'react'
import { retailApi, type Product } from './api'
import { type StockTakeRecord } from './retailContracts'
import { StockTake } from './StockTake'
import './costs.css'
import './stock-count.css'

export function StockCountPage({products,isDemo,onBack,onChanged,onBlockingChange}:{products:Product[];isDemo:boolean;onBack():void;onChanged():Promise<void>;onBlockingChange?(blocked:boolean):void}) {
 const [history,setHistory]=useState<StockTakeRecord[]|null>(null), [loading,setLoading]=useState(!isDemo), [error,setError]=useState(''), [refresh,setRefresh]=useState(0)
 const [editor,setEditor]=useState<{key:string;record?:StockTakeRecord}|null>(null), [opening,setOpening]=useState(''), [blocked,setBlocked]=useState(false)
 const editorRef=useRef<HTMLElement>(null)
 const generation=useRef(0), newCount=useRef(0)
 useEffect(()=>{const id=++generation.current;setError('');setHistory(null);if(isDemo){setLoading(false);return};setLoading(true);void retailApi.listStockTakes().then(records=>{if(id===generation.current)setHistory(records)}).catch(failure=>{if(id===generation.current)setError(failure instanceof Error?failure.message:'Stock count history unavailable.')}).finally(()=>{if(id===generation.current)setLoading(false)});return()=>{generation.current++}},[isDemo,refresh])
 useEffect(()=>{if(editor){editorRef.current?.focus({preventScroll:true});editorRef.current?.scrollIntoView({block:'start'})}},[editor?.key])
 const blocking = blocked || !!opening
 useEffect(()=>{onBlockingChange?.(blocking)},[blocking,onBlockingChange])
 const openRecord=async(id:string)=>{if(blocking||isDemo)return;setOpening(id);setError('');try{const record=await retailApi.getStockTake(id);setEditor({key:record.id,record})}catch(failure){setError(failure instanceof Error?failure.message:'Saved count could not be loaded.')}finally{setOpening('')}}
 const start=()=>{if(blocking||isDemo)return;newCount.current++;setEditor({key:`new-${newCount.current}`});setError('')}
 return <section className="stock-count-page costs-workspace">
  <header className="stock-count-heading"><div><p className="eyebrow">YOUR SHELVES, YOUR RECORDS</p><h2>Stock count</h2></div><button className="back-link" disabled={blocking} onClick={onBack}>← Back to Stock</button></header>
  <section className="stock-count-start"><div><span className="stock-count-mark" aria-hidden="true">▥</span><h3>Know what’s on your shelves.</h3><p>Count your products, review the differences, then confirm when you’re ready.</p></div><button className="primary-action" disabled={isDemo||blocking} onClick={start}>Start stock count</button></section>
  {isDemo&&<p className="cost-warning" role="status">Starter catalogue only. Connect to your shop to save counts and view actual saved history.</p>}
  {editor&&<section ref={editorRef} tabIndex={-1} className="stock-count-active" aria-label="Stock count workspace"><div className="stock-count-active-header"><span>{editor.record?'Saved record':'New count'}</span><button disabled={blocking} onClick={()=>setEditor(null)}>Close count</button></div><StockTake key={editor.key} products={products} disabled={isDemo} initialRecord={editor.record} onChanged={onChanged} onSaved={()=>setRefresh(value=>value+1)} onBlockingChange={setBlocked}/></section>}
  <section className="stock-count-history" aria-label="Stock count history"><div className="stock-count-history-heading"><div><p className="eyebrow">YOUR COUNTING RECORD</p><h3>Previous counts</h3></div><button disabled={loading||blocking||isDemo} onClick={()=>setRefresh(value=>value+1)} aria-label="Refresh stock count history">↻ Refresh</button></div>
   {loading&&<p className="stock-count-loading" role="status">Loading saved counts…</p>}{opening&&<p role="status">Opening saved count…</p>}
   {error&&<section className="stock-count-error" role="alert"><strong>Couldn’t load saved counts.</strong><p>{error}</p><button disabled={blocking||isDemo} onClick={()=>setRefresh(value=>value+1)}>Try again</button></section>}
   {!isDemo&&!loading&&history?.length===0&&<div className="stock-count-empty"><span aria-hidden="true">▥</span><h4>Your first count starts here.</h4><p>No saved stock counts yet. Start a count above to create your first record.</p></div>}
   {history&&history.length>0&&<ol className="stock-count-records">{history.map(record=>{const differences=record.lines.filter(line=>line.counted_qty!==record.expected_snapshot[line.product_id]).length;return <li key={record.id}><button disabled={blocking||isDemo} onClick={()=>{void openRecord(record.id)}} aria-label={`Open ${record.status} stock count ${record.count_date} by ${record.actor}`}><div className="stock-count-record-top"><strong>{record.count_date}</strong><span className={`stock-count-badge ${record.status}`}>{record.status==='confirmed'?'Confirmed':'Draft'}</span></div><p>{record.mode==='monthly'?'Monthly count':'On-demand count'} · {record.lines.length} {record.lines.length===1?'product':'products'}</p><p className="stock-count-record-differences">{differences===0?'All counted quantities match':`${differences} ${differences===1?'product differs':'products differ'}`}</p><div className="stock-count-record-bottom"><span>Counted by {record.actor}</span><span>{record.status==='draft'?'Review draft':'View details'} →</span></div></button></li>})}</ol>}
  </section>
 </section>
}
