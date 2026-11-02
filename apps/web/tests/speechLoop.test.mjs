import assert from 'node:assert/strict'
import { test } from 'node:test'
import { startSpeechLoop } from '../src/speechLoop.ts'
import { openSpeech, speakPrompt } from '../src/speechRecognition.ts'

const tick = async () => { for(let i=0;i<20;i++) await Promise.resolve() }
function fixture() {
 const prior=globalThis.window, listeners=new Map(), calls=[], timers=[]
 let finishSpeech
 const plugin={async start(){calls.push('start')},async stop(){calls.push('stop')},speak(){calls.push('tts');return new Promise(resolve=>finishSpeech=resolve)},async addListener(name,fn){const entries=listeners.get(name)??new Set();entries.add(fn);listeners.set(name,entries);return{async remove(){entries.delete(fn)}}}}
 globalThis.window={Capacitor:{getPlatform:()=> 'android',registerPlugin:()=>plugin}}
 const emit=(name,data={})=>{for(const fn of [...listeners.get(name)??[]])fn(data)}
 const schedule=(fn)=>{const task={fn,cancelled:false};timers.push(task);return()=>task.cancelled=true}
 const flush=()=>{for(const task of timers.splice(0))if(!task.cancelled)task.fn()}
 return{emit,calls,schedule,flush,finishSpeech:()=>finishSpeech(),restore:()=>globalThis.window=prior}
}
test('final command → TTS pause → ready quantity reply sends bare one once, then Yes and Cash without Apo',async()=>{
 const f=fixture(), commands=[], states=[]
 let loop
 const create=()=>startSpeechLoop({open:openSpeech,schedule:f.schedule,state:value=>states.push(value),error:()=>assert.fail('no ASR error expected'),text:(text,final)=>{if(!final)return false;commands.push(text);return Promise.resolve(true)}})
 try{
  loop=create();await loop.ready
  assert.equal(states.at(-1),'starting')
  f.emit('speechReady');assert.equal(states.at(-1),'listening')
  f.emit('speech',{text:'Apo chips Napo',final:true});f.emit('speech',{text:'Apo chips Napo',final:true})
  assert.equal(commands.length,1)
  await loop.dispose();const spoken=speakPrompt('How many Potato chips? Say just the quantity.');await tick()
  f.emit('speech',{text:'one',final:true});assert.equal(commands.length,1,'TTS cannot leak a quantity into stopped turn')
  f.finishSpeech();await spoken
  for(const reply of ['one','Yes','Cash 5']){
   loop=create();await loop.ready;assert.equal(states.at(-1),'starting')
   f.emit('speechReady');assert.equal(states.at(-1),'listening')
   f.emit('speech',{text:reply,final:false});assert.equal(commands.at(-1)===reply,false)
   f.emit('speech',{text:reply,final:true});f.emit('speech',{text:reply,final:true})
   assert.equal(commands.filter(value=>value===reply).length,1)
   await loop.dispose()
  }
  assert.deepEqual(commands,['Apo chips Napo','one','Yes','Cash 5'])
 }finally{await loop?.dispose();f.restore()}
})
test('unchanged turn automatically rearms after async handler settles; duplicate finals remain suppressed while pending',async()=>{
 const f=fixture(), answers=[],states=[];let settle
 const loop=startSpeechLoop({open:openSpeech,schedule:f.schedule,state:s=>states.push(s),error:()=>{},text:(text,final)=>{if(!final)return false;answers.push(text);return new Promise(resolve=>settle=resolve)}})
 try{
  await loop.ready;f.emit('speechReady');f.emit('speech',{text:'1',final:true});f.emit('speech',{text:'1',final:true});f.emit('speechEnd')
  f.flush();await tick();assert.deepEqual(answers,['1']);assert.equal(f.calls.filter(x=>x==='start').length,1)
  settle(true);await tick();f.flush();await tick();assert.equal(f.calls.filter(x=>x==='start').length,2,'no prop/effect change is needed to recover a consumed turn')
  assert.equal(states.at(-1),'starting');f.emit('speechReady');assert.equal(states.at(-1),'listening')
  f.emit('speech',{text:'Cancel',final:true});assert.deepEqual(answers,['1','Cancel']);settle(true)
 }finally{await loop.dispose();f.restore()}
})
test('background, silence, fatal errors and disposal never report a ready microphone without the native ready callback',async()=>{
 const f=fixture(),states=[],errors=[]
 const loop=startSpeechLoop({open:openSpeech,schedule:f.schedule,state:s=>states.push(s),error:(message,fatal)=>errors.push([message,fatal]),text:()=>false})
 try{
  await loop.ready;assert.deepEqual(states,['starting'])
  f.emit('speechPaused');assert.equal(states.at(-1),'background')
  f.emit('speechReady');assert.equal(states.at(-1),'background')
  f.emit('speechResumed');f.flush();await tick();assert.equal(states.at(-1),'starting')
  f.emit('speechReady');assert.equal(states.at(-1),'listening')
  f.emit('speechError',{message:'silence',code:6});f.emit('speechEnd');f.flush();await tick();assert.equal(states.at(-1),'starting')
  f.emit('speechError',{message:'permission denied',code:9});assert.equal(states.at(-1),'error');f.flush();await tick()
  const length=states.length;await loop.dispose();f.emit('speechReady');f.emit('speechEnd');assert.equal(states.length,length)
  assert.deepEqual(errors,[['silence',false],['permission denied',true]])
 }finally{await loop.dispose();f.restore()}
})

test('pending answer learns background after its recognizer stopped and never restarts until foreground resumes',async()=>{
 const f=fixture(),states=[];let settle,visible=true
 const loop=startSpeechLoop({open:openSpeech,schedule:f.schedule,canStart:()=>visible,state:s=>states.push(s),error:()=>{},text:()=>new Promise(resolve=>settle=resolve)})
 try{
  await loop.ready;f.emit('speechReady');f.emit('speech',{text:'one',final:true});await tick()
  assert.equal(f.calls.at(-1),'stop')
  visible=false;f.emit('speechPaused');assert.equal(states.at(-1),'background')
  settle(true);await tick();f.flush();await tick()
  assert.equal(f.calls.filter(x=>x==='start').length,1,'settled handler cannot restart background microphone')
  visible=true;f.emit('speechResumed');f.flush();await tick()
  assert.equal(f.calls.filter(x=>x==='start').length,2)
  assert.equal(states.at(-1),'starting');f.emit('speechReady');assert.equal(states.at(-1),'listening')
 }finally{await loop.dispose();f.restore()}
})

test('document visibility guard prevents fallback restart even when a pause event is missed',async()=>{
 const f=fixture(),states=[];let settle,visible=true
 const loop=startSpeechLoop({open:openSpeech,schedule:f.schedule,canStart:()=>visible,state:value=>states.push(value),error:()=>{},text:()=>new Promise(resolve=>settle=resolve)})
 try{
  await loop.ready;visible=false
  const startingCount=states.length;f.emit('speechReady');assert.equal(states.length,startingCount,'late ready while hidden must not report listening')
  visible=true;f.emit('speech',{text:'one',final:true});visible=false;settle(true);await tick();f.flush();await tick()
  assert.equal(f.calls.filter(x=>x==='start').length,1)
  const before=states.length;f.emit('speechReady');assert.equal(states.length,before,'late ready while document hidden cannot claim listening')
 }finally{await loop.dispose();f.restore()}
})
