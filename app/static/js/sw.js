// fit-link service worker — offline caching for the reference UI only.
//
// Bump CACHE_NAME on any deploy that changes precached assets meaningfully;
// activate() drops every cache that doesn't match the current name.
const CACHE_NAME = "fitlink-v1";
const OFFLINE_URL = "/offline";

const PRECACHE_URLS = [
  "/manifest.json",
  "/static/css/style.css",
  "/static/js/htmx.min.js",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/icons/apple-touch-icon.png",
  "/static/icons/icon-maskable-512.png",
  OFFLINE_URL,
];

// Requests under these prefixes are the JWT-authenticated workout logger,
// a separate app sharing this origin. The reference UI never calls them —
// leave them alone rather than caching authenticated responses.
const UNCACHED_PREFIXES = ["/auth", "/workouts"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
      )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (UNCACHED_PREFIXES.some((prefix) => url.pathname.startsWith(prefix))) return;

  const isStaticAsset = url.pathname.startsWith("/static/") || url.pathname === "/manifest.json";
  event.respondWith(isStaticAsset ? cacheFirst(request) : networkFirst(request));
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  const response = await fetch(request);
  const cache = await caches.open(CACHE_NAME);
  cache.put(request, response.clone());
  return response;
}

// Pages and HTMX fragments: always prefer a live response (content changes
// as content/*.md and *.yaml get edited and reloaded), but fall back to
// whatever was last cached — or the offline page for a full navigation —
// when the gym's signal doesn't cooperate.
async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) return cached;
    if (request.mode === "navigate") {
      return cache.match(OFFLINE_URL);
    }
    throw err;
  }
}
