const CACHE = 'lernspiele-landing-v17';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon.svg',
  './icon-maskable.svg',
  './_lib/audio.js'
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
  // Nur direkte Sammlung-Dateien behandeln. Alles in Unterordnern (z.B.
  // /Lernspiele/buchstaben/...) ueberlaesst der Sammlung-SW dem jeweiligen
  // Spiel-SW mit engerem Scope. Ausnahme: _lib/ wird von der Sammlung gecacht,
  // weil die Spiel-SWs Pfade ausserhalb ihres Scopes nicht abfangen koennen.
  const url = new URL(event.request.url);
  const swScope = new URL(self.registration.scope);
  if (!url.pathname.startsWith(swScope.pathname)) return;
  const rel = url.pathname.slice(swScope.pathname.length);
  if (rel.includes('/') && !rel.startsWith('_lib/')) return;
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
