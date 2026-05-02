const CACHE = 'lernspiele-landing-v1';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon.svg',
  './icon-maskable.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE && key.startsWith('lernspiele-landing-')).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  // Nur Anfragen im eigenen Scope behandeln. Anfragen an Spiel-Unterordner
  // werden vom jeweiligen Spiel-SW (mit engerem Scope) bedient.
  const url = new URL(event.request.url);
  const swScope = new URL(self.registration.scope);
  if (!url.pathname.startsWith(swScope.pathname)) return;
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
