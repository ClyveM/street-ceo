// Independent saved recognition-phrase and short prompt acceptance.
import assert from 'node:assert/strict'
import {test} from 'node:test'
import {WakeCommand,readPronunciation,addNapoSamples,napoAliases,catalogueReplyEvent,conflictingAliases} from '../apps/web/src/wakePhrase.ts'
import {spokenPaymentQuestion,SALE_SAVED_SPEECH} from '../apps/web/src/voicePrompts.ts'
const defaults={apo:'apo',napo:'napo'}
const samples=['Nah po','napple finish','Napo finish','nah poh','nah po']

test('five reviewed samples retain all unique phrases and migrate old saved custom pronunciation',()=>{
 const legacy=readPronunciation({getItem:()=>JSON.stringify({apo:'ah po',napo:'nah boo'})})
 const next=addNapoSamples(legacy,samples)
 assert.equal(next.napo,'nah boo')
 assert.deepEqual(next.napoAliases,['nah po','napple finish','napo finish','nah poh'])
 const reopened=readPronunciation({getItem:()=>JSON.stringify(next)})
 for(const alias of ['nah boo',...samples,'napo','nabo','napple']){
  assert.equal(new WakeCommand().accept(`ah po one bread loaf ${alias}`,reopened),'Apo one bread loaf Napo')
 }
})

test('personal ends are terminal whole phrases and cannot drop interior product words or decimals',()=>{
 const trained=addNapoSamples(defaults,samples)
 const machine=new WakeCommand()
 assert.equal(machine.accept('Apo one nah poh soap',trained),null)
 assert.equal(machine.accept('cash 1.50 napple finish',trained),'Apo one nah poh soap cash 1.50 Napo')
 assert.equal(machine.accept('Apo one bread napple finishes',trained),null)
 assert.equal(machine.accept('nah po',trained),'Apo one bread napple finishes Napo')
 assert.equal(machine.accept('nah po',trained),null)
})

test('all trained variants close split catalogue retry exactly once while bare answers stay bare',()=>{
 const trained=addNapoSamples(defaults,samples)
 const machine=new WakeCommand()
 assert.deepEqual(catalogueReplyEvent(machine,'Apo',trained),{command:null,capturing:true})
 assert.deepEqual(catalogueReplyEvent(machine,'two milk',trained),{command:null,capturing:true})
 assert.deepEqual(catalogueReplyEvent(machine,'nah poh',trained),{command:'Apo two milk Napo',capturing:false})
 assert.deepEqual(catalogueReplyEvent(machine,'one',trained),{command:'one',capturing:false})
 assert.deepEqual(catalogueReplyEvent(machine,'Cancel',trained),{command:'Cancel',capturing:false})
})

test('five samples required and cross-boundary aliases rejected without modifying previous state',()=>{
 const original=JSON.stringify(defaults)
 assert.throws(()=>addNapoSamples(defaults,samples.slice(1)))
 assert.throws(()=>addNapoSamples(defaults,['nah po','nabo','nah poh','napo finish','apple']))
 assert.throws(()=>addNapoSamples(defaults,['nah po','nabo','nah poh','napo finish','one bread loaf cash']))
 assert.equal(JSON.stringify(defaults),original)
 assert.equal(conflictingAliases({...defaults,napoAliases:['apo finish']}),true)
})

test('invalid stored aliases cannot activate unsafe wake/end collisions; blocked storage defaults safely',()=>{
 const invalid=readPronunciation({getItem:()=>JSON.stringify({...defaults,napoAliases:['nah po','apple']})})
 assert.deepEqual(invalid,defaults)
 assert.deepEqual(readPronunciation({getItem(){throw Error('blocked')}}),defaults)
 assert.deepEqual(napoAliases(defaults),['napo','nabo','napple'])
})

test('only tender-choice speech is shortened; cash amount and outstanding questions remain exact',()=>{
 assert.equal(spokenPaymentQuestion({missing:['tender'],question:'Cash or bank? Total 100.00'}),'Cash or bank?')
 assert.equal(spokenPaymentQuestion({missing:['amount_received_cents'],question:'How much cash did you receive?'}),'How much cash did you receive?')
 assert.equal(spokenPaymentQuestion({missing:['cash_amount'],question:'Please repeat the amount.'}),'Please repeat the amount.')
 assert.equal(SALE_SAVED_SPEECH,'Sale saved')
})
