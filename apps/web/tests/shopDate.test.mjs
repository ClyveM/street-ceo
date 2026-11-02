import assert from 'node:assert/strict'
import { test } from 'node:test'
import { formatShopWelcome, watchShopWelcome } from '../src/shopDate.ts'

const zone = { locale: 'en-GB', timeZone: 'Africa/Johannesburg' }
const welcome = (iso, options = zone) => formatShopWelcome(Date.parse(iso), options)

test('production defaults use the device timezone and locale rather than a fixed date/zone', () => {
  const instant = Date.parse('2026-10-31T22:00:00Z')
  const result = formatShopWelcome(instant)
  assert.equal(result.timeZone, new Intl.DateTimeFormat().resolvedOptions().timeZone)
  assert.equal(result.date, new Intl.DateTimeFormat(undefined, { weekday: 'long', day: 'numeric', month: 'long' }).format(instant))
  const local = new Date(instant)
  assert.equal(result.dateKey, `${local.getFullYear()}-${String(local.getMonth() + 1).padStart(2, '0')}-${String(local.getDate()).padStart(2, '0')}`)
})

test('injected timezones and locales give the correct local day and greeting for the same instant', () => {
  assert.equal(welcome('2026-10-31T08:00:00Z').date, 'Saturday 31 October')
  assert.equal(welcome('2026-10-31T22:00:00Z').dateKey, '2026-11-01')
  assert.equal(welcome('2026-10-31T22:00:00Z', { locale: 'en-US', timeZone: 'America/Los_Angeles' }).date, 'Saturday, October 31')
  assert.equal(welcome('2026-10-31T22:00:00Z', { timeZone: 'America/Los_Angeles' }).greeting, 'Good afternoon')
  assert.equal(welcome('2026-10-31T22:00:00Z', { timeZone: 'Asia/Tokyo' }).greeting, 'Good morning')
})

test('local midnight, year boundary, noon and evening do not leave stale labels', () => {
  assert.equal(welcome('2026-10-31T21:59:59.999Z').dateKey, '2026-10-31')
  assert.equal(welcome('2026-10-31T22:00:00Z').dateKey, '2026-11-01')
  assert.equal(welcome('2026-12-31T22:00:00Z').dateKey, '2027-01-01')
  assert.equal(welcome('2026-11-04T09:59:59Z').greeting, 'Good morning')
  assert.equal(welcome('2026-11-04T10:00:00Z').greeting, 'Good afternoon')
  assert.equal(welcome('2026-11-04T15:59:59Z').greeting, 'Good afternoon')
  assert.equal(welcome('2026-11-04T16:00:00Z').greeting, 'Good evening')
})

test('mounted clock refreshes at midnight and after suspension; stop cancels future updates', () => {
  let now = Date.parse('2026-10-31T21:59:59Z'), id = 0
  const timers = new Map(), observed = []
  const clock = watchShopWelcome((value) => observed.push(value), { now: () => now, schedule: (callback, delay) => { timers.set(++id, { callback, delay }); return id }, cancel: (timer) => timers.delete(timer) }, zone)
  assert.equal(observed.at(-1).dateKey, '2026-10-31')
  assert.equal(timers.get(id).delay, 1000)
  now += 1000; timers.get(id).callback()
  assert.equal(observed.at(-1).dateKey, '2026-11-01')
  now = Date.parse('2026-11-04T16:00:00Z'); clock.refresh()
  assert.equal(observed.at(-1).date, 'Wednesday 4 November')
  assert.equal(observed.at(-1).greeting, 'Good evening')
  assert.equal(timers.size, 1)
  clock.stop(); assert.equal(timers.size, 0)
  const count = observed.length; clock.refresh(); assert.equal(observed.length, count)
})
