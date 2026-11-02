import assert from 'node:assert/strict'
import { test } from 'node:test'
import { voiceErrorSummary } from '../src/voiceError.ts'

test('connection error headline gives a short next step while original URL remains available as detail',()=>{
 const detail='Could not reach or read the voice service at http://192.168.10.213:8000. Check Shop Connection, the API server and your network, then retry. No sale was submitted by this voice request.'
 const title=voiceErrorSummary(detail)
 assert.match(title,/Retry or check Shop Connection in Profile/)
 assert.doesNotMatch(title,/192\.168|http/)
 assert.ok(title.length<100)
 assert.match(detail,/No sale was submitted/)
})
test('unknown mutations direct recovery, while actionable validation errors remain intact',()=>{
 assert.match(voiceErrorSummary('network failure',true),/Recover the original request/)
 assert.match(voiceErrorSummary('network failure',true),/No sale receipt received/)
 const detail='Not enough stock for this product.'
 assert.equal(voiceErrorSummary(detail),detail)
})

test('missing catalogue item gives a short spoken response and makes no sale claim',()=>{
 assert.equal(voiceErrorSummary('Product not found or command is ambiguous. Use exact catalogue names.'),'Product not found. No sale recorded. Say Apo to try again.')
})
