/**
 * SGC - Sistema de Gestão de Condomínio
 * Service Worker Oficial (PWA Mobile)
 * Responsável por:
 *  - Cache offline de recursos estáticos (HTML, CSS, JS, Ícones)
 *  - Estratégia Stale-While-Revalidate para velocidade máxima
 *  - Suporte a instalação como aplicativo móvel (Android, iOS, Windows, macOS)
 */

const CACHE_NAME = 'sgc-condominio-v2.0.1';

// Arquivos essenciais pré-carregados no momento da instalação (PWA Offline)
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/style.css',
  '/app.js',
  '/manifest.json',
  '/components/topbar.html',
  '/components/sidebar.html',
  '/components/bottom_nav.html',
  '/modules/auth_login.html',
  '/modules/visao_geral.html',
  '/modules/unidades.html',
  '/modules/encomendas.html',
  '/modules/reservas.html',
  '/modules/mural_avisos.html',
  '/modules/auditoria.html',
  '/modules/ocorrencias.html',
  '/modules/portaria_visitantes.html',
  '/modules/configuracoes.html',
  '/modals/convidados_modal.html',
  '/modals/resposta_ocorrencia_modal.html',
  '/modals/confirm_dialog_modal.html',
  '/modals/troca_senha_modal.html',
  '/modals/suspensao_modal.html',
  '/modals/convite_morador_modal.html',
  '/modals/reservas_dia_modal.html',
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

  // Requisições para a API REST (/api/): Estratégia Network-First (sempre fresco, nunca stale)
  if (requestUrl.pathname.startsWith('/api/')) {
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

  // Requisições de navegação e arquivos de código (.js, .html, .css): Network-First para garantir frescor imediato
  const isCodeAsset = requestUrl.pathname.endsWith('.js') || requestUrl.pathname.endsWith('.html') || requestUrl.pathname.endsWith('.css');
  if (event.request.mode === 'navigate' || event.request.destination === 'document' || isCodeAsset) {
    event.respondWith(
      fetch(event.request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseToCache));
          }
          return networkResponse;
        })
        .catch(() => caches.match(event.request).then((cached) => cached || (event.request.mode === 'navigate' ? caches.match('/') : null)))
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
