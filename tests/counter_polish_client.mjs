// Independent state/wake composition; no rendering, microphone, network or sale writes.
import assert from 'node:assert/strict'
import {test} from 'node:test'
import {counterWakeTransition,HANDS_FREE_PREFERENCE,readHandsFreePreference,storeHandsFreePreference} from '../apps/web/src/counterSession.ts'
import {WakeCommand} from '../apps/web/src/wakePhrase.ts'

const pronunciation={apo:'apo',napo:'napo'}
const complete=Object.freeze({phase:'success',open:true,enabled:true,hasReceipt:true,busy:false,blocked:false,uncertain:false,receiptId:'verified-receipt',total:150,change:350})

test('Apo or leading Apple dismisses only the completed receipt without changing money or preference',()=>{
 for(const phrase of ['Apo','Apple']) {
  const machine=new WakeCommand(),event=machine.acceptEvent(phrase,pronunciation,1000)
  assert.equal(event.woke,true)
  assert.equal(event.command,null)
  const next=counterWakeTransition(complete)
  assert.equal(next.open,false)
  assert.equal(next.phase,'idle')
  assert.equal(next.enabled,true)
  assert.equal(next.receiptId,complete.receiptId)
  assert.equal(next.total,complete.total)
  assert.equal(next.change,complete.change)
  assert.equal(complete.open,true)
  assert.equal(machine.awake,true)
 }
})

test('same-utterance wake and full next basket survives receipt dismissal intact',()=>{
 for(const phrase of ['Apo one Coke two sugar Napo','Apple one Coke two sugar Napo']) {
  const machine=new WakeCommand(),event=machine.acceptEvent(phrase,pronunciation,1000)
  const next=event.woke?counterWakeTransition(complete):complete
  assert.equal(next.open,false)
  assert.equal(event.command,'Apo one coke two sugar Napo')
  assert.equal(machine.awake,false)
 }
})

test('bare wake closes receipt while the next utterance continues the already-awake basket',()=>{
 const machine=new WakeCommand()
 const first=machine.acceptEvent('Apple',pronunciation,1000)
 assert.equal(first.woke,true)
 const next=counterWakeTransition(complete)
 assert.equal(next.phase,'idle')
 const second=machine.acceptEvent('one Coke Napo',pronunciation,2000)
 assert.equal(second.command,'Apo one coke Napo')
 assert.equal(second.woke,false)
 const partial=new WakeCommand()
 const opening=partial.acceptEvent('Apo one Coke',pronunciation,1000)
 assert.equal(opening.woke,true)
 assert.equal(opening.command,null)
 assert.equal(counterWakeTransition(complete).open,false)
 assert.equal(partial.acceptEvent('two sugar Napo',pronunciation,2000).command,'Apo one coke two sugar Napo')
})

test('pending and uncertain states are unchanged even when the same wake is heard',()=>{
 for(const phase of ['idle','review','match','clarification','tender','error','reversed']) {
  const pending=Object.freeze({...complete,phase,pendingKey:'original-paid-key'})
  assert.equal(counterWakeTransition(pending),pending)
 }
 for(const guard of [{busy:true},{blocked:true},{uncertain:true},{hasReceipt:false},{enabled:false}]) {
  const pending=Object.freeze({...complete,...guard,pendingKey:'original-paid-key'})
  assert.equal(counterWakeTransition(pending),pending)
  assert.equal(pending.pendingKey,'original-paid-key')
 }
})

test('explicit pause stays off despite a completed receipt and storage failure does not imply a saved preference',()=>{
 const storage={getItem(key){assert.equal(key,HANDS_FREE_PREFERENCE);return 'off'}}
 const enabled=readHandsFreePreference(storage,true)
 assert.equal(enabled,false)
 const paused={...complete,enabled}
 assert.equal(counterWakeTransition(paused),paused)
 const writes=[]
 assert.equal(storeHandsFreePreference({setItem:(key,value)=>writes.push([key,value])},false),true)
 assert.deepEqual(writes,[[HANDS_FREE_PREFERENCE,'off']])
 assert.equal(storeHandsFreePreference({setItem(){throw new Error('unavailable storage')}},false),false)
})

test('ordinary product words do not dismiss a receipt or lose internal apple tokens',()=>{
 for(const phrase of ['pineapple','applepie','I need apple'])assert.deepEqual(new WakeCommand().acceptEvent(phrase,pronunciation,1000),{woke:false,command:null})
 assert.equal(new WakeCommand().acceptEvent('Apo one apple juice Napo',pronunciation,1000).command,'Apo one apple juice Napo')
})
