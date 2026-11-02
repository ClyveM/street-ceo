type WelcomeOptions = { locale?: string; timeZone?: string }

/** Browser defaults in production; explicit locale/timezone only when injected. */
export function formatShopWelcome(instant: number, options: WelcomeOptions = {}) {
  const zone = options.timeZone ? { timeZone: options.timeZone } : {}
  const dateFormat = new Intl.DateTimeFormat(options.locale, { ...zone, weekday: 'long', day: 'numeric', month: 'long' })
  const clockFormat = new Intl.DateTimeFormat('en-GB', { ...zone, calendar: 'gregory', numberingSystem: 'latn', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23' })
  const parts = clockFormat.formatToParts(instant)
  const part = (type: Intl.DateTimeFormatPartTypes) => parts.find((entry) => entry.type === type)!.value
  const hour = Number(part('hour'))
  return {
    date: dateFormat.format(instant),
    dateKey: `${part('year')}-${part('month')}-${part('day')}`,
    greeting: hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening',
    timeZone: dateFormat.resolvedOptions().timeZone,
  }
}

type ShopClock = { now: () => number; schedule: (callback: () => void, delay: number) => number; cancel: (timer: number) => void }

export function watchShopWelcome(onChange: (welcome: ReturnType<typeof formatShopWelcome>) => void, clock: ShopClock = { now: Date.now, schedule: (callback, delay) => window.setTimeout(callback, delay), cancel: (timer) => window.clearTimeout(timer) }, options: WelcomeOptions = {}) {
  let timer: number | undefined
  let stopped = false
  const refresh = () => {
    if (stopped) return
    if (timer !== undefined) clock.cancel(timer)
    onChange(formatShopWelcome(clock.now(), options))
    timer = clock.schedule(refresh, 60000 - clock.now() % 60000)
  }
  refresh()
  return { refresh, stop: () => { stopped = true; if (timer !== undefined) clock.cancel(timer) } }
}
