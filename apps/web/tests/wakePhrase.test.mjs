import assert from 'node:assert/strict'
import { test } from 'node:test'
import { WakeCommand, readPronunciation, validAlias, conflictingAliases } from '../src/wakePhrase.ts'
import { apoCommand } from '../src/quickSale.ts'
const canonical = { apo: 'apo', napo: 'napo' }
test('Apo wakes only on whole tokens and Napo ends once across sessions', () => {
 const m = new WakeCommand()
 assert.equal(m.accept('tomatoes and napoli', canonical), null)
 assert.equal(m.awake, false)
 assert.equal(m.accept('Apo', canonical, 1), null)
 assert.equal(m.awake, true)
 assert.equal(m.accept('1 Coke', canonical, 100), null)
 assert.equal(m.accept('Napo', canonical, 200), 'Apo 1 coke Napo')
 assert.equal(m.accept('Napo', canonical, 300), null)
})

test('after a completed command the same wake machine is ready for another sale and still ignores idle chatter', () => {
 const machine=new WakeCommand()
 assert.equal(machine.accept('Apo one Coke Napo',canonical),'Apo one coke Napo')
 assert.equal(machine.awake,false)
 assert.equal(machine.accept('one sugar',canonical),null)
 assert.equal(machine.accept('Apo two Bath soap Napo',canonical),'Apo two bath soap Napo')
})

test('segmented Apo flow preserves hyphenated catalogue names for the backend', () => {
 const m = new WakeCommand(), canonical = { apo: 'apo', napo: 'napo' }
 assert.equal(m.accept('Apo', canonical, 1), null)
 assert.equal(m.accept('1 sugar', canonical, 100), null)
 assert.equal(m.accept('1 Coca-Cola', canonical, 200), null)
 assert.equal(m.accept('Napo', canonical, 300), 'Apo 1 sugar 1 coca-cola Napo')
})
test('idle chatter never submits; empty, oversized and timed out commands fail closed', () => {
 const m = new WakeCommand()
 assert.equal(m.accept('1 coke Napo', canonical), null)
 assert.equal(m.accept('Apo Napo', canonical), null)
 assert.equal(m.accept('Apo 1 Coke', canonical, 0), null)
 assert.equal(m.accept('Napo', canonical, 21000), null)
 assert.equal(m.accept('Apo '+ 'coke '.repeat(4000)+'Napo', canonical), null)
})
test('confirmed pronunciation aliases are bounded phrases and preserve decimals', () => {
 const m = new WakeCommand(), aliases = { apo:'ah po', napo:'nah po' }
 assert.equal(m.accept('Ah po 1 Coke Cash 1.50 nah po.', aliases), 'Apo 1 coke cash 1.50 Napo')
 assert.equal(validAlias('a whole sale of products'), false)
 assert.equal(validAlias('ah po'), true)
 assert.equal(conflictingAliases({apo:'nah',napo:'nah po'}), true)
 assert.equal(conflictingAliases({apo:'napo please',napo:'nah po'}), true)
 assert.equal(conflictingAliases(aliases), false)
})
test('pronunciation storage failures and ambiguous saved aliases fall back safely', () => {
 assert.deepEqual(readPronunciation({getItem(){throw Error('blocked')}}), canonical)
 assert.deepEqual(readPronunciation({getItem(){return '{bad'}}), canonical)
 assert.deepEqual(readPronunciation({getItem(){return JSON.stringify({apo:'nah',napo:'nah po'})}}), canonical)
})
test('canonical Napo frame and legacy Apo frame both preserve reviewed sale eligibility', () => {
 assert.equal(apoCommand('Apo 1 Coke Cash 1.50 Napo').closed,true)
 assert.equal(apoCommand('Apo 1 Coke Cash 1.50 Napo').tender.amount_received_cents,150)
 assert.equal(apoCommand('Apo 1 Coke Apo').closed,true)
 assert.equal(apoCommand('1 Coke Napo').closed,false)
})

test('terminal nabo is a bounded ASR close alias and noisy ordinary words are preserved rather than silently removed',()=>{
 const m=new WakeCommand()
 assert.equal(m.accept('Apo 1 bread glove number nabo',canonical),'Apo 1 bread glove number Napo')
 assert.equal(apoCommand('Apo 1 bread glove number Nabo').heardBody,'1 bread glove number')
 assert.equal(m.accept('Apo 1 coca-cola nabo marble',canonical),null)
 assert.equal(m.accept('Napo',canonical),'Apo 1 coca-cola nabo marble Napo')
 assert.equal(m.accept('Apo bath soap nabo maple map',canonical),null)
 assert.equal(m.accept('Napo',canonical),'Apo bath soap nabo maple map Napo')
 assert.equal(m.accept('Apo 1 Coke Napo more items',canonical),null)
 m.reset();assert.equal(m.accept('nabo',canonical),null)
 assert.equal(conflictingAliases({apo:'nabo',napo:'napo'}),true)
})
