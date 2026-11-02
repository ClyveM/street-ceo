import assert from 'node:assert/strict'
import { test } from 'node:test'
import { clientId } from '../src/clientId.ts'

test('HTTP LAN request references work without secure-context randomUUID', () => {
  const reference = clientId({ getRandomValues(bytes) { bytes.fill(7); return bytes } })
  assert.equal(reference, '07070707-0707-4707-8707-070707070707')
  assert.match(clientId({}), /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/)
})

test('secure-context request references use the available native UUID generator', () => {
  assert.equal(clientId({ randomUUID: () => 'native-reference' }), 'native-reference')
})
