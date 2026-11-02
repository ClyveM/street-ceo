import assert from 'node:assert/strict'
import {test} from 'node:test'
import {addNapoSamples,readPronunciation,WakeCommand,catalogueReplyEvent,conflictingAliases} from '../src/wakePhrase.ts'
import {spokenPaymentQuestion,SALE_SAVED_SPEECH} from '../src/voicePrompts.ts'
const old={apo:'apo',napo:'nah po'}
test('five samples retain legacy end and normalized distinct variations across storage',()=>{
 const trained=addNapoSamples(old,['Nepal','nepo','nopple','napple','nepal'])
 assert.deepEqual(trained.napoAliases,['nepal','nepo','nopple','napple'])
 assert.equal(trained.napo,'nah po')
 assert.deepEqual(readPronunciation({getItem:()=>JSON.stringify(trained)}),trained)
 assert.deepEqual(readPronunciation({getItem:()=>JSON.stringify(old)}),old)
 for(const end of ['nepal','nepo','nopple','napple','nah po','napo','nabo'])assert.equal(new WakeCommand().accept(`Apo one bath soap ${end}`,trained),'Apo one bath soap Napo')
})
test('duplicates count without duplicate aliases, and repeated setup preserves previous variations',()=>{
 const first=addNapoSamples(old,Array(5).fill('nepal'))
 assert.deepEqual(first.napoAliases,['nepal'])
 assert.deepEqual(addNapoSamples(first,Array(5).fill('nepo')).napoAliases,['nepal','nepo'])
 assert.throws(()=>addNapoSamples(old,['nepal']))
 assert.throws(()=>addNapoSamples(old,['nepal','nepo','nopple','napple','bad 123']))
})
test('reviewed variations are terminal only and split retries preserve product words',()=>{
 const trained=addNapoSamples(old,['nepal','nepo','nopple','napple','nepal'])
 const m=new WakeCommand()
 assert.equal(m.accept('nepal',trained),null)
 assert.equal(m.accept('Apo one nepal tea nepo more',trained),null)
 assert.equal(m.accept('nopple',trained),'Apo one nepal tea nepo more Napo')
 assert.equal(new WakeCommand().accept('Apo one apple nepal',trained),'Apo one apple Napo')
 assert.equal(new WakeCommand().accept('Apo one soap napoli',trained),null)
 const retry=new WakeCommand()
 assert.equal(catalogueReplyEvent(retry,'Apple',trained).command,null)
 assert.equal(catalogueReplyEvent(retry,'one bath soap',trained).command,null)
 assert.equal(catalogueReplyEvent(retry,'nepo',trained).command,'Apo one bath soap Napo')
})
test('learned variants participate in conflicts, bounded persistence and longest matching',()=>{
 assert.throws(()=>addNapoSamples(old,['nepal','nepo','apo please','nopple','napple']))
 assert.equal(conflictingAliases({...old,apo:'nepal',napoAliases:['nepal']}),true)
 assert.deepEqual(readPronunciation({getItem:()=>JSON.stringify({...old,napoAliases:['apo start']})}),{apo:'apo',napo:'napo'})
 assert.equal(new WakeCommand().accept('Apo one bread napple finish',addNapoSamples(old,Array(5).fill('napple finish'))),'Apo one bread Napo')
 assert.throws(()=>addNapoSamples({...old,napoAliases:['a','b','c','d','e','f','g','h','i','j']},Array(5).fill('nepal')))
})
test('short audio leaves complete visible question and cash amount clarification intact',()=>{
 const choice={question:'Should I record this sale as cash or bank?',missing:['tender']}
 assert.equal(spokenPaymentQuestion(choice),'Cash or bank?')
 assert.equal(choice.question,'Should I record this sale as cash or bank?')
 const amount={question:'How much cash did you receive? Total 1.50.',missing:['amount_received_cents']}
 assert.equal(spokenPaymentQuestion(amount),amount.question)
 assert.equal(SALE_SAVED_SPEECH,'Sale saved')
})
