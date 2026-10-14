/* Camada incremental: o HTML gerado continua sendo fallback quando a API local
   não está disponível (por exemplo, GitHub Pages ou abertura de arquivo). */
(function loadCatalogFromApi() {
  'use strict';

  function fetchOffers(kind, placement) {
    const query = new URLSearchParams({ kind: kind, placement: placement, limit: placement === 'home' ? '30' : '1000' });
    return fetch('/api/offers?' + query.toString(), { headers: { Accept: 'application/json' } })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('API indisponível')));
  }

  function sanitizeFragment(fragment) {
    const template = document.createElement('template');
    template.innerHTML = String(fragment || '');
    template.content.querySelectorAll('script, iframe, object, embed, link, meta, style').forEach((node) => node.remove());
    template.content.querySelectorAll('*').forEach((node) => {
      Array.from(node.attributes).forEach((attribute) => {
        const name = attribute.name.toLowerCase();
        const value = attribute.value.trim().toLowerCase();
        if (name.startsWith('on') || name === 'srcdoc' ||
            ((name === 'href' || name === 'src' || name === 'action' || name === 'formaction') &&
             (value.startsWith('javascript:') || value.startsWith('data:text/html')))) {
          node.removeAttribute(attribute.name);
        }
      });
    });
    return template.innerHTML;
  }

  function fragmentItems(items) {
    return items.map((item) => sanitizeFragment(item.html)).filter(Boolean).join('\n');
  }

  function replaceCatalog() {
    const root = document.querySelector('[data-catalog-root]');
    if (!root) return Promise.resolve();
    const kind = root.getAttribute('data-catalog-root');
    const apiKind = kind === 'pacotes' ? 'pacote' : kind === 'voos' ? 'promo-voo' : 'campanha';
    return fetchOffers(apiKind, 'catalog').then((payload) => {
      const list = root.querySelector('[data-catalog-list]');
      if (list && Array.isArray(payload.items) && payload.items.length) list.innerHTML = fragmentItems(payload.items);
    });
  }

  function replaceHome() {
    const home = document.querySelector('#pacotes .pacotes__category');
    if (!home) return Promise.resolve();
    return fetchOffers('pacote', 'home').then((payload) => {
      const groups = { complete: [], withoutFlight: [] };
      (payload.items || []).forEach((item) => {
        const template = document.createElement('template');
         template.innerHTML = sanitizeFragment(item.html);
        const article = template.content.firstElementChild;
        if (!article) return;
        const noFlight = article.getAttribute('data-categoria') === 'sem-aereo';
        groups[noFlight ? 'withoutFlight' : 'complete'].push(article.outerHTML);
      });
      document.querySelectorAll('#pacotes .pacotes__category').forEach((category) => {
        const isWithoutFlight = category.id === 'pacotes-sem-aereo';
        const cards = groups[isWithoutFlight ? 'withoutFlight' : 'complete'];
        const grid = category.querySelector('.pacotes__grid');
        if (grid && cards.length) grid.innerHTML = cards.join('\n');
      });
    });
  }

  window.VCBContentReady = Promise.all([replaceHome(), replaceCatalog()]).then(function () {
    document.dispatchEvent(new CustomEvent('vcb:content-updated'));
  }).catch(function () {
    // Fallback intencional: o HTML versionado permanece funcional sem backend.
  });
})();
