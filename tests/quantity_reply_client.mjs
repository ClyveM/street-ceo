// Independent real bridge/turn composition with a synthetic native plugin.
import assert from 'node:assert/strict'
import {test} from 'node:test'
import {openSpeech,speakPrompt} from '../apps/web/src/speechRecognition.ts'
import {startSpeechLoop} from '../apps/web/src/speechLoop.ts'

test('native final → paused prompt → ready reply accepts bare one once without Apo',async()=>{
 const listeners=new Map(), operations=[], answers=[], states=[]
 let finishPrompt
 const plugin={
  async addListener(name,callback){let callbacks=listeners.get(name);if(!callbacks)listeners.set(name,callbacks=new Set());callbacks.add(callback);return{async remove(){callbacks.delete(callback)}}},
  async start(){operations.push('start')},async stop(){operations.push('stop')},
  async speak(){operations.push('speak');await new Promise(resolve=>{finishPrompt=resolve})},async stopSpeaking(){},
 }
 const emit=(name,value={})=>{for(const callback of [...listeners.get(name)??[]])callback(value)}
 globalThis.window={Capacitor:{getPlatform:()=> 'android',Plugins:{ApoSpeech:plugin}}}
 const first=startSpeechLoop({open:openSpeech,text:(text,final)=>{if(final){answers.push(text);return true}return false},state:state=>states.push(state),error:()=>assert.fail('unexpected failure')})
 await first.ready
 assert.equal(states.at(-1),'starting') // start promise alone is not readiness.
 emit('speechReady');assert.equal(states.at(-1),'listening')
 emit('speech',{text:'potato chips',final:true});emit('speech',{text:'potato chips',final:true})
 assert.deepEqual(answers,['potato chips']);assert.equal(states.at(-1),'submitted')
 await first.dispose()
 const spoken=speakPrompt('How many Potato chips?')
 await new Promise(resolve=>setImmediate(resolve))
 assert.equal(operations.at(-1),'speak')
 emit('speech',{text:'How many Potato chips?',final:true})
 assert.deepEqual(answers,['potato chips'])
 finishPrompt();await spoken
 const reply=startSpeechLoop({open:openSpeech,text:(text,final)=>{if(final){answers.push(text);return true}return false},state:state=>states.push(state),error:()=>assert.fail('unexpected failure')})
 await reply.ready
 assert.equal(states.at(-1),'starting')
 emit('speechReady');assert.equal(states.at(-1),'listening')
 emit('speech',{text:'one',final:true});emit('speech',{text:'one',final:true});emit('speechEnd')
 assert.deepEqual(answers,['potato chips','one']);assert.equal(states.at(-1),'submitted')
 await reply.dispose()
 assert.deepEqual(operations,['start','stop','speak','start','stop'])
})

test('silent end restarts, background and disposal cancel restart without fake Listening',async()=>{
 let callbacks, pending, starts=0, disposals=0
 const states=[]
 const loop=startSpeechLoop({
  async open(value){callbacks=value;return{async start(){starts++},async stop(){},async dispose(){disposals++}}},
  text:()=>false,state:value=>states.push(value),error:()=>assert.fail('unexpected failure'),
  schedule(action){pending=()=>{pending=undefined;action()};return()=>{pending=undefined}},
 })
 await loop.ready
 callbacks.end();assert.equal(states.at(-1),'waiting');assert.ok(pending)
 pending();await Promise.resolve();assert.equal(starts,2);assert.equal(states.at(-1),'starting')
 callbacks.active(false);assert.equal(states.at(-1),'background');assert.equal(pending,undefined)
 callbacks.ready();assert.equal(states.at(-1),'background')
 callbacks.active(true);assert.ok(pending)
 await loop.dispose();assert.equal(pending,undefined);assert.equal(disposals,1)
 const before=[...states];callbacks.ready();callbacks.end();callbacks.text('one',true)
 assert.deepEqual(states,before)
})

test('background during pending answer cannot rearm when that answer settles',async()=>{
 let callbacks,pending,settle,starts=0
 const states=[]
 const loop=startSpeechLoop({
  async open(value){callbacks=value;return{async start(){starts++},async stop(){},async dispose(){}}},
  text:()=>new Promise(resolve=>{settle=resolve}),state:value=>states.push(value),error:()=>{},
  schedule(action){pending=()=>{pending=undefined;action()};return()=>{pending=undefined}},
 })
 await loop.ready
 callbacks.ready();callbacks.text('one',true);callbacks.text('one',true)
 callbacks.active(false)
 settle(true);for(let index=0;index<10;index++)await Promise.resolve()
 assert.equal(pending,undefined,'submitted turn must remember suspension while its handler completes')
 assert.equal(starts,1)
 callbacks.active(true);assert.ok(pending)
 pending();await Promise.resolve();assert.equal(starts,2)
 await loop.dispose()
})

test('hidden document rejects late readiness even when native pause was missed',async()=>{
 let callbacks,visible=true
 const states=[]
 const loop=startSpeechLoop({async open(value){callbacks=value;return{async start(){},async stop(){},async dispose(){}}},canStart:()=>visible,text:()=>false,state:value=>states.push(value),error:()=>{}})
 await loop.ready
 visible=false
 callbacks.ready()
 assert.equal(states.includes('listening'),false)
 await loop.dispose()
})
