/* ═══════════════════════════════════════════════════
   VIAJANDO COM A BABI — script.js
   Vanilla JS · Sem dependências externas
═══════════════════════════════════════════════════ */

'use strict';

/* ──────────────────────────────────────────────────
   NAVBAR: scroll shadow + hamburger menu
────────────────────────────────────────────────── */
(function initNavbar() {
  const navbar     = document.getElementById('navbar');
  const hamburger  = document.getElementById('hamburger');
  const navLinks   = document.getElementById('navLinks');

  if (!navbar || !hamburger || !navLinks) return;

  // Add shadow on scroll
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 20);
  }, { passive: true });

  // Toggle mobile menu
  hamburger.addEventListener('click', () => {
    const isOpen = navLinks.classList.toggle('open');
    hamburger.classList.toggle('open', isOpen);
    hamburger.setAttribute('aria-expanded', String(isOpen));
    document.body.style.overflow = isOpen ? 'hidden' : '';
  });

  // Close menu when a link is clicked
  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('open');
      hamburger.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    });
  });

  // Close menu on outside click
  document.addEventListener('click', (e) => {
    if (!navbar.contains(e.target) && navLinks.classList.contains('open')) {
      navLinks.classList.remove('open');
      hamburger.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }
  });
})();

/* ──────────────────────────────────────────────────
   SCROLL REVEAL — IntersectionObserver
────────────────────────────────────────────────── */
(function initScrollReveal() {
  const revealEls = document.querySelectorAll('.reveal');

  if (!revealEls.length) return;

  // Respect prefers-reduced-motion
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReduced) {
    revealEls.forEach(el => el.classList.add('visible'));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
  );

  revealEls.forEach(el => observer.observe(el));
})();

/* ──────────────────────────────────────────────────
   SMOOTH SCROLL para âncoras internos
────────────────────────────────────────────────── */
(function initSmoothScroll() {
  const navbarH = parseInt(
    getComputedStyle(document.documentElement).getPropertyValue('--navbar-h'),
    10
  ) || 70;

  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;

      const target = document.querySelector(targetId);
      if (!target) return;

      e.preventDefault();

      const top = target.getBoundingClientRect().top + window.scrollY - navbarH;
      window.scrollTo({ top, behavior: 'smooth' });
    });
  });
})();

/* ──────────────────────────────────────────────────
   COPYRIGHT YEAR AUTOMÁTICO
────────────────────────────────────────────────── */
(function setYear() {
  const el = document.getElementById('year');
  if (el) el.textContent = new Date().getFullYear();
})();

/* ──────────────────────────────────────────────────
   MODAL CADASTUR
────────────────────────────────────────────────── */
(function initCadasturModal() {
  const modal      = document.getElementById('modalCadastur');
  const closeBtn   = document.getElementById('modalClose');
  const triggerIds = ['btnCadasturNav', 'btnCadasturLink', 'btnCadasturFooter'];

  if (!modal) return;

  const modalImg = modal.querySelector('.modal__img');

  function resolveModalImgSrc(img) {
    if (!img) return '';
    const picture = img.closest('picture');
    if (picture) {
      const webp = picture.querySelector('source[type="image/webp"]');
      if (webp && webp.srcset) return webp.srcset;
    }
    return img.getAttribute('data-src') || '';
  }

  function openModal() {
    if (modalImg && !modalImg.getAttribute('src')) {
      const src = resolveModalImgSrc(modalImg);
      if (src) modalImg.src = src;
    }
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';

    // Close mobile nav if open
    const navLinks  = document.getElementById('navLinks');
    const hamburger = document.getElementById('hamburger');
    if (navLinks && navLinks.classList.contains('open')) {
      navLinks.classList.remove('open');
      hamburger && hamburger.classList.remove('open');
      hamburger && hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }
  }

  function closeModal() {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }

  triggerIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('click', openModal);
  });

  closeBtn && closeBtn.addEventListener('click', closeModal);

  // Close on overlay click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('open')) closeModal();
  });
})();

/* ──────────────────────────────────────────────────
   LIGHTBOX — visualização de imagens dos cards
────────────────────────────────────────────────── */
(function initLightbox() {
  const overlay  = document.getElementById('lightbox');
  const closeBtn = document.getElementById('lightboxClose');
  const img      = document.getElementById('lightboxImg');
  const triggers = document.querySelectorAll('.card__img-wrap img[data-lightbox]');

  if (!overlay || !img) return;

  function openLightbox(src, alt) {
    img.src = src;
    img.alt = alt || '';
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    overlay.classList.remove('open');
    document.body.style.overflow = '';
    img.src = '';
  }

  triggers.forEach(t => {
    t.addEventListener('click', () => openLightbox(t.src, t.alt));
  });

  closeBtn && closeBtn.addEventListener('click', closeLightbox);

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeLightbox();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('open')) closeLightbox();
  });
})();

/* ──────────────────────────────────────────────────
   MODAL FORMULÁRIO DE VIAGEM
────────────────────────────────────────────────── */
(function initFormularioModal() {
  const modal    = document.getElementById('modalFormulario');
  const closeBtn = document.getElementById('modalFormClose');
  const form     = document.getElementById('formViagem');
  const trigger  = document.getElementById('btnFormularioLink');

  if (!modal) return;

  function openModal() {
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }

  trigger && trigger.addEventListener('click', () => {
    if (window.VCBAnalytics) window.VCBAnalytics.trackFormOpen();
    openModal();
  });
  closeBtn && closeBtn.addEventListener('click', closeModal);

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('open')) closeModal();
  });

  form && form.addEventListener('submit', (e) => {
    e.preventDefault();
    const destino   = document.getElementById('fDestino').value.trim();
    const datas     = document.getElementById('fDatas').value.trim();
    const adultos   = document.getElementById('fAdultos').value.trim();
    const criancas  = document.getElementById('fCriancas').value.trim() || 'Sem crianças';
    const saida     = document.getElementById('fSaida').value.trim();
    const orcamento = document.getElementById('fOrcamento').value.trim();

    const msg =
      `Olá Babi! Quero planejar minha viagem. Aqui estão meus dados:\n\n` +
      `✈️ Destino: ${destino}\n` +
      `📅 Datas: ${datas}\n` +
      `👥 Adultos: ${adultos}\n` +
      `👶 Crianças: ${criancas}\n` +
      `🏙️ Saída de: ${saida}\n` +
      `💰 Orçamento: ${orcamento}`;

    const waUrl = 'https://wa.me/5521920064617?text=' + encodeURIComponent(msg);

    if (window.VCBAnalytics) {
      window.VCBAnalytics.trackFormLead();
    }

    if (typeof window.gtag_report_conversion === 'function') {
      window.gtag_report_conversion(waUrl, {
        transaction_id: 'form_' + Date.now()
      });
    } else {
      window.open(waUrl, '_blank', 'noopener,noreferrer');
    }
    closeModal();
  });
})();

/* ──────────────────────────────────────────────────
   ACTIVE NAV LINK on scroll (highlight)
────────────────────────────────────────────────── */
(function initActiveNav() {
  const sections = document.querySelectorAll('section[id], footer[id]');
  const navLinks = document.querySelectorAll('.navbar__links a');

  if (!sections.length || !navLinks.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          navLinks.forEach(link => {
            link.style.color = '';
            if (link.getAttribute('href') === '#' + entry.target.id) {
              link.style.color = 'var(--clr-primary)';
            }
          });
        }
      });
    },
    { threshold: 0.35 }
  );

  sections.forEach(s => observer.observe(s));
})();

/* ──────────────────────────────────────────────────
   AVATAR FALLBACK — iniciais quando imagem ausente
────────────────────────────────────────────────── */
(function initAvatarFallback() {
  document.querySelectorAll('.depoimento__avatar img').forEach(img => {
    img.addEventListener('error', function () {
      const name = this.alt || '?';
      const initials = name.split(' ').filter(Boolean).map(w => w[0]).slice(0, 2).join('').toUpperCase();
      const wrap = this.parentElement;
      if (!wrap || wrap.querySelector('.depoimento__initials')) return;
      this.style.display = 'none';
      const span = document.createElement('span');
      span.className = 'depoimento__initials';
      span.textContent = initials;
      span.setAttribute('aria-hidden', 'true');
      wrap.appendChild(span);
    });
  });
})();

/* ──────────────────────────────────────────────────
   PACOTES: rótulos únicos nos CTAs (acessibilidade)
────────────────────────────────────────────────── */
(function initPackageButtonLabels() {
  document.querySelectorAll('.card[data-destino] .btn--whatsapp.btn--full').forEach(btn => {
    const destino = btn.closest('.card')?.dataset.destino;
    if (destino) btn.setAttribute('aria-label', `Quero esse pacote: ${destino}`);
  });
})();

/* ──────────────────────────────────────────────────
   CATÁLOGO: filtros, ordenação e mostrar mais
────────────────────────────────────────────────── */
(function initCatalog() {
  const root = document.querySelector('[data-catalog-root]');
  if (!root) return;

  const bar = root.querySelector('[data-catalog]');
  const list = root.querySelector('[data-catalog-list]');
  if (!bar || !list) return;

  const kind = bar.getAttribute('data-catalog') || 'pacotes';
  const pageSize = parseInt(bar.getAttribute('data-page-size') || '24', 10) || 24;
  const items = Array.from(list.querySelectorAll('.catalog-item'));
  const emptyEl = root.querySelector('[data-catalog-empty]');
  const moreBtn = root.querySelector('[data-catalog-more]');
  const countEl = bar.querySelector('[data-catalog-count]');
  const sortEl = bar.querySelector('[data-catalog-sort]');
  const modal = document.getElementById('modalCatalogFilter');
  const openBtn = bar.querySelector('[data-catalog-open-filter]');
  const originSelects = document.querySelectorAll('[data-catalog-root] [data-catalog-origin], #modalCatalogFilter [data-catalog-origin]');
  const destSelects = document.querySelectorAll('[data-catalog-root] [data-catalog-dest], #modalCatalogFilter [data-catalog-dest]');
  const destSearch = document.querySelector('[data-catalog-root] [data-catalog-dest-search], #modalCatalogFilter [data-catalog-dest-search]');
  const priceInputs = document.querySelectorAll('[data-catalog-root] [data-catalog-price], #modalCatalogFilter [data-catalog-price]');
  const priceLabels = document.querySelectorAll('[data-catalog-root] [data-catalog-price-label], #modalCatalogFilter [data-catalog-price-label]');
  const fromInputs = document.querySelectorAll('[data-catalog-root] [data-catalog-from], #modalCatalogFilter [data-catalog-from]');
  const toInputs = document.querySelectorAll('[data-catalog-root] [data-catalog-to], #modalCatalogFilter [data-catalog-to]');
  const tipoSelect = modal && modal.querySelector('[data-catalog-tipo]');
  const destTypeSelects = document.querySelectorAll('[data-catalog-root] [data-catalog-dest-type], #modalCatalogFilter [data-catalog-dest-type]');

  let shown = pageSize;
  let lastFocus = null;

  function track(name, params) {
    if (window.VCBAnalytics && typeof window.VCBAnalytics.trackEvent === 'function') {
      window.VCBAnalytics.trackEvent(name, params || {});
    }
  }

  function moneyLabel(value) {
    return 'R$ ' + Math.round(value).toLocaleString('pt-BR');
  }

  function itemDates(el) {
    return (el.getAttribute('data-dates') || '')
      .split(',')
      .map(v => v.trim())
      .filter(Boolean);
  }

  function itemDate(el) {
    return el.getAttribute('data-sort-date') || '9999-12-31';
  }

  function itemPrice(el) {
    const raw = el.getAttribute('data-sort-price');
    if (raw === null || raw === '') return null;
    const n = parseFloat(raw);
    return Number.isFinite(n) && n > 0 ? n : null;
  }

  function originKey(el) {
    const bucket = el.getAttribute('data-origem') || '';
    if (kind === 'voos') return bucket;
    const iata = el.getAttribute('data-origem-iata') || '';
    return iata ? bucket + ':' + iata : bucket;
  }

  function originLabel(el) {
    const bucket = el.getAttribute('data-origem') || '';
    const iata = el.getAttribute('data-origem-iata') || '';
    const names = { rio: 'Rio de Janeiro', sp: 'São Paulo', 'sem-aereo': 'Sem aéreo' };
    const base = names[bucket] || bucket;
    if (kind === 'voos') return base || 'Outras';
    if (iata) return base + ' (' + iata + ')';
    return base || 'Outras';
  }

  function fillSelects() {
    const origins = new Map();
    const dests = new Map();
    let maxPrice = 0;
    items.forEach(el => {
      const ok = originKey(el);
      if (ok) origins.set(ok, originLabel(el));
      const dk = el.getAttribute('data-destino-key') || '';
      const title = (el.querySelector('.card__title, .oferta-row__title') || {}).textContent || el.getAttribute('data-destino') || '';
      if (dk) dests.set(dk, title.replace(/\s+/g, ' ').trim().split('\n')[0]);
      const price = itemPrice(el);
      if (price != null) maxPrice = Math.max(maxPrice, price);
    });
    originSelects.forEach(sel => {
      const current = sel.value;
      sel.querySelectorAll('option:not([value=""])').forEach(o => o.remove());
      Array.from(origins.entries()).sort((a, b) => a[1].localeCompare(b[1], 'pt-BR')).forEach(([value, label]) => {
        const opt = document.createElement('option');
        opt.value = value;
        opt.textContent = label;
        sel.appendChild(opt);
      });
      sel.value = current;
    });
    destSelects.forEach(sel => {
      const current = sel.value;
      sel.querySelectorAll('option:not([value=""])').forEach(o => o.remove());
      Array.from(dests.entries()).sort((a, b) => a[1].localeCompare(b[1], 'pt-BR')).forEach(([value, label]) => {
        const opt = document.createElement('option');
        opt.value = value;
        opt.textContent = label;
        sel.appendChild(opt);
      });
      sel.value = current;
    });
    const calculatedCeiling = Math.ceil((maxPrice || 0) / 100) * 100;
    const ceiling = Math.max(10000, calculatedCeiling);
    priceInputs.forEach(input => {
      input.min = '0';
      input.max = String(ceiling);
      input.value = String(ceiling);
    });
    syncPriceLabels();
    if (tipoSelect) {
      const tipos = new Set(items.map(el => el.getAttribute('data-tipo')).filter(Boolean));
      tipoSelect.querySelectorAll('option').forEach(opt => {
        if (!opt.value) return;
        opt.hidden = !tipos.has(opt.value);
      });
    }
  }

  function syncPriceLabels() {
    const input = priceInputs[0];
    if (!input) return;
    const text = moneyLabel(Number(input.value || 0));
    priceLabels.forEach(el => { el.textContent = text; });
  }

  function currentFilters() {
    const origin = (originSelects[0] && originSelects[0].value) || '';
    const dest = (destSelects[0] && destSelects[0].value) || '';
    const from = (fromInputs[0] && fromInputs[0].value) || '';
    const to = (toInputs[0] && toInputs[0].value) || '';
    const priceInput = priceInputs[0];
    const max = priceInput ? Number(priceInput.max) : 0;
    const price = priceInput ? Number(priceInput.value) : max;
    const tipo = (tipoSelect && tipoSelect.value) || '';
    const destType = (destTypeSelects[0] && destTypeSelects[0].value) || '';
    return { origin, dest, from, to, price, max, tipo, destType };
  }

  function activeFilterCount(f) {
    let n = 0;
    if (f.origin) n += 1;
    if (f.dest) n += 1;
    if (f.from) n += 1;
    if (f.to) n += 1;
    if (f.tipo) n += 1;
    if (f.destType) n += 1;
    if (f.price && f.max && f.price < f.max) n += 1;
    return n;
  }

  function matches(el, f) {
    if (f.origin) {
      const key = originKey(el);
      const bucket = el.getAttribute('data-origem') || '';
      if (f.origin !== key && f.origin !== bucket) return false;
    }
    if (f.dest && el.getAttribute('data-destino-key') !== f.dest) return false;
    if (f.tipo && el.getAttribute('data-tipo') !== f.tipo) return false;
    if (f.destType && el.getAttribute('data-destino-tipo') !== f.destType) return false;
    const dateFilterOn = !!(f.from || f.to);
    const listed = itemDates(el);
    if (dateFilterOn) {
      if (!listed.length) return false;
      const inRange = listed.some(date => (!f.from || date >= f.from) && (!f.to || date <= f.to));
      if (!inRange) return false;
    }
    if (f.price && f.max && f.price < f.max) {
      const p = itemPrice(el);
      if (p == null || p > f.price) return false;
    }
    return true;
  }

  function itemTitle(el) {
    const node = el.querySelector('.card__title, .oferta-row__title');
    return ((node && node.textContent) || el.getAttribute('data-destino') || '').replace(/\s+/g, ' ').trim();
  }

  function tieBreak(a, b) {
    const da = itemDate(a);
    const db = itemDate(b);
    if (da !== db) return da.localeCompare(db);
    return itemTitle(a).localeCompare(itemTitle(b), 'pt-BR');
  }

  function sortItems(arr) {
    const mode = (sortEl && sortEl.value) || 'date';
    return arr.slice().sort((a, b) => {
      const pa = itemPrice(a);
      const pb = itemPrice(b);
      if (mode === 'price' || mode === 'price-desc') {
        if (pa == null && pb == null) return tieBreak(a, b);
        if (pa == null) return 1;
        if (pb == null) return -1;
        const diff = mode === 'price-desc' ? pb - pa : pa - pb;
        return diff || tieBreak(a, b);
      }
      return tieBreak(a, b) || (pa == null ? 1e12 : pa) - (pb == null ? 1e12 : pb);
    });
  }

  function apply() {
    const f = currentFilters();
    const filtered = sortItems(items.filter(el => matches(el, f)));
    const unmatched = items.filter(el => !filtered.includes(el));
    const frag = document.createDocumentFragment();
    filtered.forEach(el => frag.appendChild(el));
    unmatched.forEach(el => frag.appendChild(el));
    list.appendChild(frag);

    filtered.forEach((el, i) => {
      el.hidden = false;
      el.classList.toggle('is-paged-out', i >= shown);
    });
    unmatched.forEach(el => {
      el.hidden = true;
      el.classList.remove('is-paged-out');
    });

    const total = filtered.length;
    const noun = total === 1
      ? (kind === 'voos' ? 'promoção encontrada' : kind === 'campanhas' ? 'campanha encontrada' : 'pacote encontrado')
      : (kind === 'voos' ? 'promoções encontradas' : kind === 'campanhas' ? 'campanhas encontradas' : 'pacotes encontrados');
    if (countEl) countEl.textContent = total + ' ' + noun;

    if (emptyEl) emptyEl.hidden = total !== 0;
    if (moreBtn) {
      moreBtn.hidden = shown >= total || total === 0;
      moreBtn.parentElement.hidden = moreBtn.hidden;
    }

    const active = activeFilterCount(f);
    root.querySelectorAll('[data-catalog-clear]').forEach(btn => {
      if (btn.closest('.catalog-empty')) return;
      btn.hidden = active === 0;
    });
    if (openBtn) {
      openBtn.setAttribute('data-active', active ? 'true' : 'false');
      openBtn.innerHTML = active
        ? '<i class="fas fa-sliders-h" aria-hidden="true"></i> Filtrar pacotes (' + active + ')'
        : '<i class="fas fa-sliders-h" aria-hidden="true"></i> Filtrar pacotes';
    }
  }

  function clearFilters() {
    originSelects.forEach(sel => { sel.value = ''; });
    destSelects.forEach(sel => { sel.value = ''; });
    destTypeSelects.forEach(sel => { sel.value = ''; });
    fromInputs.forEach(el => { el.value = ''; });
    toInputs.forEach(el => { el.value = ''; });
    if (tipoSelect) tipoSelect.value = '';
    if (destSearch) destSearch.value = '';
    priceInputs.forEach(input => { input.value = input.max; });
    shown = pageSize;
    syncPriceLabels();
    apply();
    track(kind === 'pacotes' ? 'filter_packages_clear' : 'filter_packages_clear', { catalog_type: kind });
  }

  function openModal() {
    if (!modal) return;
    lastFocus = document.activeElement;
    modal.hidden = false;
    modal.classList.add('open');
    document.body.classList.add('catalog-modal-open');
    const first = modal.querySelector('select, input, button');
    first && first.focus();
    track('filter_packages_open');
  }

  function closeModal() {
    if (!modal) return;
    modal.classList.remove('open');
    modal.hidden = true;
    document.body.classList.remove('catalog-modal-open');
    lastFocus && lastFocus.focus();
  }

  fillSelects();
  apply();

  sortEl && sortEl.addEventListener('change', () => {
    shown = pageSize;
    apply();
    track(kind === 'voos' ? 'sort_flights' : 'sort_packages', { sort_by: sortEl.value, catalog_type: kind });
  });

  moreBtn && moreBtn.addEventListener('click', () => {
    shown += pageSize;
    apply();
  });

  root.querySelectorAll('[data-catalog-clear]').forEach(btn => {
    btn.addEventListener('click', clearFilters);
  });
  modal && modal.querySelectorAll('[data-catalog-clear]').forEach(btn => {
    btn.addEventListener('click', () => { clearFilters(); closeModal(); });
  });

  openBtn && openBtn.addEventListener('click', openModal);
  modal && modal.querySelector('[data-catalog-close-filter]') && modal.querySelector('[data-catalog-close-filter]').addEventListener('click', closeModal);
  modal && modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal && modal.classList.contains('open')) closeModal();
  });

  const form = modal && modal.querySelector('[data-catalog-form]');
  form && form.addEventListener('submit', (e) => {
    e.preventDefault();
    shown = pageSize;
    apply();
    closeModal();
    track('filter_packages_apply', { filter_count: activeFilterCount(currentFilters()), catalog_type: kind });
  });

  const inline = bar.querySelector('[data-catalog-inline]');
  inline && inline.addEventListener('submit', (e) => {
    e.preventDefault();
    shown = pageSize;
    apply();
    track('filter_packages_apply', { filter_count: activeFilterCount(currentFilters()), catalog_type: kind });
  });

  priceInputs.forEach(input => input.addEventListener('input', syncPriceLabels));

  if (kind === 'voos') {
    const liveApply = () => { shown = pageSize; apply(); };
    originSelects.forEach(el => el.addEventListener('change', liveApply));
    destSelects.forEach(el => el.addEventListener('change', liveApply));
    destTypeSelects.forEach(el => el.addEventListener('change', liveApply));
    fromInputs.forEach(el => el.addEventListener('change', liveApply));
    toInputs.forEach(el => el.addEventListener('change', liveApply));
    let priceFrame = 0;
    priceInputs.forEach(el => el.addEventListener('input', () => {
      if (priceFrame) cancelAnimationFrame(priceFrame);
      priceFrame = requestAnimationFrame(() => {
        priceFrame = 0;
        apply();
      });
    }));
  }

  if (destSearch && destSelects[0]) {
    destSearch.addEventListener('input', () => {
      const q = destSearch.value.toLowerCase();
      destSelects[0].querySelectorAll('option').forEach(opt => {
        if (!opt.value) return;
        opt.hidden = q ? opt.textContent.toLowerCase().indexOf(q) === -1 : false;
      });
    });
  }
})();
