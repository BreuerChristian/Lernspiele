const CACHE = 'tier-geraeusche-v6';
const CORE_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon.svg',
  './icon-maskable.svg'
];
// Sound-Dateien werden best-effort gecacht (fehlen ist okay - dann greift der
// Speech-Synthesis-Fallback im Spiel). Mischformat OGG/OPUS/MP3, je Quelle.
// Maus hat keine Datei - reiner Speech-Fallback.
const SOUND_ASSETS = [
  './sounds/kuh.ogg',
  './sounds/hund.ogg',
  './sounds/katze.ogg',
  './sounds/hahn.ogg',
  './sounds/schaf.ogg',
  './sounds/schwein.ogg',
  './sounds/pferd.ogg',
  './sounds/ente.mp3',
  './sounds/frosch.ogg',
  './sounds/eule.mp3',
  './sounds/biene.opus',
  './sounds/loewe.ogg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) =>
      cache.addAll(CORE_ASSETS).then(() =>
        Promise.all(SOUND_ASSETS.map((url) => cache.add(url).catch(() => null)))
      )
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE && key.startsWith('tier-geraeusche-'))
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  // Sounds: network-first mit Cache-Fallback. So werden nachtraeglich
  // hinzugefuegte/geaenderte Tier-Aufnahmen sofort erkannt, und der Cache
  // dient nur als Offline-Sicherung.
  if (url.pathname.includes('/sounds/')) {
    event.respondWith(
      fetch(event.request).then((res) => {
        if (res && res.ok) {
          const clone = res.clone();
          caches.open(CACHE).then((c) => c.put(event.request, clone)).catch(() => {});
        }
        return res;
      }).catch(() => caches.match(event.request))
    );
    return;
  }
  // Alles andere: cache-first.
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
