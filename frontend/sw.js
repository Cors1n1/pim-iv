/**
 * SGC - Sistema de Gestão de Condomínio
 * Service Worker Oficial (PWA Mobile)
 * Responsável por:
 *  - Cache offline de recursos estáticos (HTML, CSS, JS, Ícones)
 *  - Estratégia Stale-While-Revalidate para velocidade máxima
 *  - Suporte a instalação como aplicativo móvel (Android, iOS, Windows, macOS)
 */

const CACHE_NAME = 'sgc-condominio-v1.0.3';

// Arquivos essenciais pré-carregados no momento da instalação
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/style.css',
  '/app.js',
  '/manifest.json',
  '/icons/condohub-icon.png',
  '/icons/icon.svg',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/apple-touch-icon.png'
];

// 1. Evento de Instalação: baixa e armazena os assets estáticos no cache local do aparelho
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Pré-carregando assets estáticos para modo offline...');
      return cache.addAll(PRECACHE_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// 2. Evento de Ativação: remove caches antigos de versões anteriores
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Removendo cache obsoleto:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// 3. Evento de Interceptação de Requisições (Fetch)
self.addEventListener('fetch', (event) => {
  const requestUrl = new URL(event.request.url);

  // Não intercepta chamadas não-GET nem endpoints de WebSocket/Docs
  if (event.request.method !== 'GET') {
    return;
  }

  // Requisições para a API REST (/api/v1/): Estratégia Network-First
  if (requestUrl.pathname.startsWith('/api/v1/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          return response;
        })
        .catch(() => {
          // Se estiver offline durante uma chamada de API, retorna resposta estruturada
          return new Response(
            JSON.stringify({
              offline: true,
              detail: 'Você está no modo offline. Conecte-se à internet para sincronizar dados em tempo real.'
            }),
            {
              headers: { 'Content-Type': 'application/json' },
              status: 503
            }
          );
        })
    );
    return;
  }

  // Requisições de navegação (HTML / Documentos): Network-First para exibir alterações imediatamente
  if (event.request.mode === 'navigate' || event.request.destination === 'document') {
    event.respondWith(
      fetch(event.request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseToCache));
          }
          return networkResponse;
        })
        .catch(() => caches.match(event.request).then((cached) => cached || caches.match('/')))
    );
    return;
  }

  // Recursos Estáticos (CSS, JS, Imagens, Fontes): Estratégia Stale-While-Revalidate
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseToCache);
            });
          }
          return networkResponse;
        })
        .catch((err) => {
          if (event.request.mode === 'navigate') {
            return caches.match('/');
          }
          throw err;
        });

      return cachedResponse || fetchPromise;
    })
  );
});
