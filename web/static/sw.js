const CACHE_NAME = 'whispers-v2';
const STATIC_ASSETS = [
    '/',
    '/static/style.css',
    '/static/app.js',
    '/static/manifest.json',
    '/static/icon-192.png',
    '/static/icon-512.png'
];

const CDN_ASSETS = [
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
    'https://cdn.jsdelivr.net/npm/dexie@3/dist/dexie.min.js'
];

self.addEventListener('install', e => {
    e.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(STATIC_ASSETS).then(() => {
                return Promise.allSettled(
                    CDN_ASSETS.map(url => fetch(url).then(r => {
                        if (r.ok) return cache.put(url, r);
                    }).catch(() => {}))
                );
            });
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', e => {
    const url = new URL(e.request.url);

    if (url.pathname.startsWith('/api/')) {
        e.respondWith(
            fetch(e.request).then(response => {
                if (e.request.method === 'GET' && response.ok) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
                }
                return response;
            }).catch(() =>
                caches.match(e.request).then(r => r || new Response('{"error":"offline"}', {
                    headers: { 'Content-Type': 'application/json' }
                }))
            )
        );
        return;
    }

    e.respondWith(
        caches.match(e.request).then(cached => {
            if (cached) return cached;
            return fetch(e.request).then(response => {
                if (response && response.status === 200 && (url.hostname === location.hostname || url.hostname.includes('jsdelivr.net'))) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
                }
                return response;
            }).catch(() => {
                if (e.request.destination === 'document') {
                    return caches.match('/');
                }
            });
        })
    );
});
