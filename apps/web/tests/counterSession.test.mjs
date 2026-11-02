import assert from 'node:assert/strict'
import {test} from 'node:test'
import {counterWakeTransition,HANDS_FREE_PREFERENCE,readHandsFreePreference,storeHandsFreePreference} from '../src/counterSession.ts'
import {WakeCommand} from '../src/wakePhrase.ts'
const pronunciation={apo:'apo',napo:'napo'},completed={phase:'success',open:true,enabled:true,hasReceipt:true,busy:false,blocked:false,uncertain:false,latestReceiptId:'saved-sale'}
test('bare Apo closes only the paid view and continues the same listening session into the next utterance',()=>{
 const machine=new WakeCommand(),wake=machine.acceptEvent('Apo',pronunciation)
 assert.deepEqual(wake,{woke:true,command:null})
 const next=counterWakeTransition(completed)
 assert.equal(next.phase,'idle');assert.equal(next.open,false);assert.equal(next.enabled,true);assert.equal(next.latestReceiptId,'saved-sale')
 assert.deepEqual(machine.acceptEvent('one Coke Napo',pronunciation),{woke:false,command:'Apo one coke Napo'})
})
test('Apo or Apple full utterance preserves next basket while advancing completed receipt',()=>{
 for(const phrase of ['Apo two sugar Napo','Apple two sugar Napo']){
  const event=new WakeCommand().acceptEvent(phrase,pronunciation)
  assert.deepEqual(event,{woke:true,command:'Apo two sugar Napo'})
  assert.equal(counterWakeTransition(completed).phase,'idle')
 }
 const machine=new WakeCommand()
 assert.equal(machine.acceptEvent('one apple',pronunciation).woke,false)
 assert.equal(machine.acceptEvent('pineapple',pronunciation).woke,false)
 assert.equal(machine.acceptEvent('Apo one apple Napo',pronunciation).command,'Apo one apple Napo')
 assert.equal(new WakeCommand().acceptEvent('Apple one apple Napo',{apo:'apple',napo:'napo'}).command,'Apo one apple Napo')
})
test('wake never clears payment, product confirmation, clarification, busy or uncertain request state',()=>{
 for(const phase of ['tender','match','clarification','review','error']){
  const pending={...completed,phase,pendingKey:'original-request'}
  assert.equal(counterWakeTransition(pending),pending)
 }
 for(const patch of [{uncertain:true},{busy:true},{blocked:true},{hasReceipt:false},{enabled:false}]){
  const state={...completed,...patch,pendingKey:'keep-original'}
  assert.equal(counterWakeTransition(state),state)
 }
})
test('explicit hands-free pause persists across close and remount; defaults native-on and browser-off',()=>{
 const values=new Map(),storage={getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value)}
 assert.equal(readHandsFreePreference(storage,true),true);assert.equal(readHandsFreePreference(storage,false),false)
 assert.equal(storeHandsFreePreference(storage,false),true);assert.equal(values.get(HANDS_FREE_PREFERENCE),'off')
 assert.equal(readHandsFreePreference(storage,true),false)
 assert.equal(counterWakeTransition({...completed,enabled:false}).enabled,false)
 storeHandsFreePreference(storage,true);assert.equal(readHandsFreePreference(storage,false),true)
 assert.equal(storeHandsFreePreference({setItem(){throw Error('blocked')}},false),false)
})
