// Independent recognizer-frame examples; no API, payment, provider or microphone.
import assert from 'node:assert/strict'
import {test} from 'node:test'
import {WakeCommand,catalogueReplyEvent,conflictingAliases,readPronunciation} from '../apps/web/src/wakePhrase.ts'
import {apoCommand,paymentCommand,matchAnswer,tenderAnswer} from '../apps/web/src/quickSale.ts'
import {counterWakeTransition} from '../apps/web/src/counterSession.ts'
import {startSpeechLoop} from '../apps/web/src/speechLoop.ts'
const pronunciation={apo:'apo',napo:'napo'}

test('observed Apple bath-soap napple becomes one canonical closed frame',()=>{
 const machine=new WakeCommand()
 const command=machine.accept('apple one bath soap napple',pronunciation)
 assert.equal(command,'Apo one bath soap Napo')
 assert.equal(apoCommand(command).heardBody,'one bath soap')
 assert.equal(machine.awake,false)
 assert.equal(machine.accept('napple',pronunciation),null)
})

test('split recognizer finals preserve the whole retry and submit only at terminal napple',()=>{
 const machine=new WakeCommand()
 assert.equal(machine.accept('apple',pronunciation,1),null)
 assert.equal(machine.accept('one bath soap',pronunciation,2),null)
 assert.equal(machine.accept('napple',pronunciation,3),'Apo one bath soap Napo')
 assert.equal(machine.accept('napple',pronunciation,4),null)
})

test('internal or trailing apple and interior napple remain possible product words',()=>{
 const machine=new WakeCommand()
 assert.equal(machine.accept('Apo one apple soap napple',pronunciation),'Apo one apple soap Napo')
 assert.equal(machine.accept('Apo one bath soap apple',pronunciation),null)
 assert.equal(machine.accept('napple',pronunciation),'Apo one bath soap apple Napo')
 assert.equal(machine.accept('Apo one napple soap Napo',pronunciation),'Apo one napple soap Napo')
 assert.equal(machine.accept('Apo one pineapple Napo',pronunciation),'Apo one pineapple Napo')
 assert.equal(machine.accept('Apo one soap napples',pronunciation),null)
 assert.equal(machine.accept('Napo',pronunciation),'Apo one soap napples Napo')
})

test('typed/reply frames normalize boundaries but bare quantity Yes and payment remain bare',()=>{
 const frame=apoCommand('Apo one bath soap napple')
 assert.equal(frame.closed,true)
 assert.equal(frame.heardBody,'one bath soap')
 assert.equal(paymentCommand('one'),'one')
 assert.equal(paymentCommand('1'),'1')
 assert.equal(matchAnswer('Yes'),'yes')
 assert.equal(matchAnswer('Apo Yes napple'),'yes')
 assert.deepEqual(tenderAnswer(paymentCommand('Apo Cash five napple')),{tender:'cash',amount_received_cents:500})
 assert.equal(paymentCommand('one bath soap apple'),'one bath soap apple')
})

test('new framing cannot dismiss or replace pending and uncertain counter states',()=>{
 for(const phase of ['clarification','match','tender','error']){
  const state={phase,open:true,enabled:true,hasReceipt:false,busy:false,blocked:false,uncertain:phase==='error'}
  assert.equal(counterWakeTransition(state),state)
 }
 const unknown={phase:'success',open:true,enabled:true,hasReceipt:true,busy:false,blocked:false,uncertain:true}
 assert.equal(counterWakeTransition(unknown),unknown)
 assert.equal(conflictingAliases({apo:'napple',napo:'napo'}),true)
 assert.deepEqual(readPronunciation({getItem:()=>JSON.stringify({apo:'napple',napo:'napo'})}),pronunciation)
})

test('clarification reply holds split retry frames but forwards ordinary answers unchanged',()=>{
 const machine=new WakeCommand()
 for(const answer of ['one','1','Yes','Cash five','one apple','one bath soap apple'])assert.deepEqual(catalogueReplyEvent(machine,answer,pronunciation),{command:answer,capturing:false})
 assert.deepEqual(catalogueReplyEvent(machine,'apple',pronunciation,1),{command:null,capturing:true})
 assert.deepEqual(catalogueReplyEvent(machine,'one bath soap',pronunciation,2),{command:null,capturing:true})
 const result=catalogueReplyEvent(machine,'napple',pronunciation,3)
 assert.deepEqual(result,{command:'Apo one bath soap Napo',capturing:false})
 assert.equal(paymentCommand(result.command),'one bath soap')
 catalogueReplyEvent(machine,'apple one bath soap',pronunciation,4)
 assert.deepEqual(catalogueReplyEvent(machine,'Cancel',pronunciation,5),{command:'Cancel',capturing:false})
 assert.equal(machine.awake,false)
 assert.deepEqual(catalogueReplyEvent(machine,'Apo one bath soap Apo',pronunciation),{command:'Apo one bath soap Napo',capturing:false})
})

test('default token prefixes never shadow saved multiword boundaries or decimals',()=>{
 for(const end of ['napple finish','napo finish']){
  const custom={apo:'apo begin',napo:end},machine=new WakeCommand()
  assert.equal(machine.accept(`apo begin one bath soap cash 1.50 ${end}`,custom),'Apo one bath soap cash 1.50 Napo')
 }
})

test('clarification retry survives recognizer end/rearm between split finals and dispatches once',async()=>{
 let callbacks,restart,starts=0
 const machine=new WakeCommand(),sent=[]
 const loop=startSpeechLoop({
  async open(value){callbacks=value;return{async start(){starts++},async stop(){},async dispose(){}}},
  schedule(action){restart=()=>{restart=undefined;action()};return()=>{restart=undefined}},
  state:()=>{},error:()=>assert.fail('unexpected ASR error'),
  text(text,final){if(!final)return false;const result=catalogueReplyEvent(machine,text,pronunciation);if(result.command){sent.push(result.command);return true}return false},
 })
 await loop.ready
 callbacks.text('apple',true);callbacks.end();restart();await Promise.resolve()
 callbacks.text('one bath soap',true);callbacks.end();restart();await Promise.resolve()
 assert.equal(starts,3);assert.deepEqual(sent,[])
 callbacks.text('napple',true);callbacks.text('napple',true);callbacks.end()
 assert.deepEqual(sent,['Apo one bath soap Napo'])
 assert.equal(restart,undefined)
 await loop.dispose()
})
