import assert from 'node:assert/strict'
import { test } from 'node:test'
import { isNativeAndroid, openSpeech, speakPrompt, stopSpokenPrompt } from '../src/speechRecognition.ts'

test('native speech bridge starts, forwards finality/lifecycle/errors and removes all listeners', async () => {
 const events = new Map(), calls=[]
 const plugin = {async start(options){calls.push(['start',options])},async stop(){calls.push(['stop'])},async addListener(name,callback){events.set(name,callback); return {async remove(){events.delete(name)}}}}
 const prior=globalThis.window
 globalThis.window={Capacitor:{getPlatform:()=> 'android',registerPlugin(name){assert.equal(name,'ApoSpeech');return plugin}}}
 try {
  const output=[]
  const speech = await openSpeech({text:(text,final)=>output.push([text,final]),error:(message,fatal)=>output.push([message,fatal]),end:()=>output.push('end'),active:(value)=>output.push(value)})
  await speech.start()
  events.get('speech')({text:'Apo',final:false})
  events.get('speech')({text:'Apo 1 Coke Napo',final:true})
  events.get('speechPaused')({}); events.get('speechResumed')({})
  events.get('speechError')({message:'silence',code:6})
  events.get('speechError')({message:'permission',code:9})
  events.get('speechEnd')({})
  assert.deepEqual(output,[['Apo',false],['Apo 1 Coke Napo',true],false,true,['silence',false],['permission',true],'end'])
  assert.deepEqual(calls[0],['start',{language:'en-ZA'}])
  await speech.stop(); await speech.dispose()
  assert.equal(events.size,0)
  assert.equal(calls.filter(([name])=>name==='stop').length,1)
 } finally {globalThis.window=prior}
})

test('disposing an older native session cannot stop its replacement or forward stale events',async()=>{
 const prior=globalThis.window, events=new Map(), calls=[]
 const plugin={async start(){calls.push('start')},async stop(){calls.push('stop')},async addListener(name,callback){const set=events.get(name)??new Set();set.add(callback);events.set(name,set);return{async remove(){set.delete(callback)}}}}
 globalThis.window={Capacitor:{getPlatform:()=> 'android',registerPlugin:()=>plugin}}
 try{
  const output=[]
  const old=await openSpeech({text:()=>output.push('old'),error(){},end(){}})
  await old.start()
  const current=await openSpeech({text:()=>output.push('current'),error(){},end(){}})
  await current.start()
  await old.dispose()
  assert.deepEqual(calls,['start','stop','start'])
  for(const callback of events.get('speech'))callback({text:'Apo',final:true})
  assert.deepEqual(output,['current'])
  await current.dispose();assert.deepEqual(calls,['start','stop','start','stop'])
 }finally{globalThis.window=prior}
})

test('permission-pending native start, cleanup and replacement are serialized without a second permission request',async()=>{
 const prior=globalThis.window,calls=[]
 let permission
 const plugin={async start(){calls.push('start');if(calls.length===1)await new Promise(resolve=>permission=resolve)},async stop(){calls.push('stop')},async addListener(){return{async remove(){}}}}
 globalThis.window={Capacitor:{getPlatform:()=> 'android',registerPlugin:()=>plugin}}
 try{
  const old=await openSpeech({text(){},error(){},end(){}})
  const started=old.start();await Promise.resolve();await Promise.resolve()
  const cleanup=old.dispose()
  const current=await openSpeech({text(){},error(){},end(){}})
  const replacement=current.start()
  assert.deepEqual(calls,['start'])
  permission();await Promise.all([started,cleanup,replacement])
  assert.deepEqual(calls,['start','stop','start'])
  await current.start();assert.deepEqual(calls,['start','stop','start'])
  await current.dispose()
 }finally{globalThis.window=prior}
})

test('unsupported browser explicitly fails instead of claiming listening', async()=>{
 const prior=globalThis.window;globalThis.window={}
 try{await assert.rejects(openSpeech({text(){},error(){},end(){}}),/unavailable/)}finally{globalThis.window=prior}
})

test('APK spoken response awaits native completion and propagates failure instead of claiming playback', async()=>{
 const prior=globalThis.window, calls=[]
 let finish
 const plugin={speak(options){calls.push(options.text);return new Promise(resolve=>{finish=resolve})},async stopSpeaking(){calls.push('stop')}}
 globalThis.window={Capacitor:{getPlatform:()=> 'android',registerPlugin:()=>plugin}}
 try {
  assert.equal(isNativeAndroid(),true)
  let complete=false
  const pending=speakPrompt('Sale recorded. Total 1.50. Change 3.50.').then(()=>{complete=true})
  await Promise.resolve();assert.equal(complete,false)
  finish();await pending;assert.equal(complete,true)
  await stopSpokenPrompt();assert.deepEqual(calls,['Sale recorded. Total 1.50. Change 3.50.','stop'])
  plugin.speak=async()=>{throw Error('TTS unavailable')}
  await assert.rejects(speakPrompt('Cash or bank?'),/TTS unavailable/)
 } finally {globalThis.window=prior}
})
