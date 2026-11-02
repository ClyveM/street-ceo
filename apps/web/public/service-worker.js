const CACHE = 'street-ceo-shell-v4'
const SHELL = ['/', '/index.html', '/manifest.webmanifest', '/icon.svg', '/street-ceo-logo.png']

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return
  const url = new URL(event.request.url)
  // Demo API truth must come from the server. Never replace JSON with cached
  // state or the HTML shell, including when upgrading an already installed APK.
  if (event.request.cache === 'no-store' || url.origin !== self.location.origin ||
      /^\/(?:api(?:\/|$)|shops(?:\/|$)|readyz(?:\/|$)|healthz(?:\/|$))/.test(url.pathname)) return
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const copy = response.clone()
        void caches.open(CACHE).then((cache) => cache.put(event.request, copy))
        return response
      })
      .catch(() => caches.match(event.request).then((cached) => cached || caches.match('/index.html'))),
  )
})
