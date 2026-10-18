// Caches the app so it opens without a connection. Sprite animations are cached as they're viewed.
const CACHE = "shiny-counter-v5";
const SPRITES = "shiny-counter-sprites"; // kept across app updates, since sprites never change
const FILES = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png", "shiny-gen2.png", "shiny-gen3.png", "anim/gen2.json"];
const WAIT_MS = 2500; // on a weak signal, use the saved copy after this long

self.addEventListener("install", (e) => { e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES))); self.skipWaiting(); });
self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    const sprites = await caches.open(SPRITES);
    for (const k of await caches.keys()) {
      if (k === CACHE || k === SPRITES) continue;
      // Carry viewed animations over from older versions before dropping them.
      const old = await caches.open(k);
      for (const req of await old.keys()) if (req.url.endsWith(".gif")) await sprites.put(req, await old.match(req));
      await caches.delete(k);
    }
    await self.clients.claim();
  })());
});

function save(cacheName, req, res) {
  if (res.ok || res.type === "opaque") { const copy = res.clone(); caches.open(cacheName).then((c) => c.put(req, copy)); }
  return res;
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  if (req.url.endsWith(".gif")) {
    // Sprites: saved copy first, network only for ones not seen yet.
    e.respondWith(caches.match(req).then((hit) => hit || fetch(req).then((r) => save(SPRITES, req, r))));
    return;
  }
  // Everything else: try the network for updates, but fall back to the saved copy
  // if the network fails or takes longer than WAIT_MS.
  e.respondWith((async () => {
    const network = fetch(req).then((r) => save(CACHE, req, r));
    const cached = await caches.match(req);
    if (!cached) return network;
    network.catch(() => {}); // a late failure after we've answered is fine
    const timeout = new Promise((resolve) => setTimeout(() => resolve(cached), WAIT_MS));
    return Promise.race([network.catch(() => cached), timeout]);
  })());
});
