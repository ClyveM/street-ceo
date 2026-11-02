import assert from 'node:assert/strict'
import { test } from 'node:test'
import { normalizeApiBaseUrl, validateApiBaseUrl } from '../src/apiUrl.ts'
test('shop URL boundary preserves proxy roots and rejects credential or non-HTTP addresses', () => {
  assert.equal(normalizeApiBaseUrl(' https://shop.example/street/api/v1/// '), 'https://shop.example/street')
  assert.equal(validateApiBaseUrl(''), '')
  assert.equal(validateApiBaseUrl('https://shop.example/street'), 'https://shop.example/street')
  for (const value of ['ftp://shop.example','https://user:secret@shop.example','https://shop.example/?token=x','https://shop.example/#x','/api/v1']) assert.throws(() => validateApiBaseUrl(value), /backend root/)
})
