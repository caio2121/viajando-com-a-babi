/* ═══════════════════════════════════════════════════
   VIAJANDO COM A BABI — analytics.js
   GA4 otimizado para catálogo de pacotes e leads
   Sem dados pessoais (LGPD)
═══════════════════════════════════════════════════ */

'use strict';

(function initAnalytics() {
  const WA_NUMBER = '5521920064617';
  const viewedPackages = new Set();
  const viewedCategories = new Set();
  const viewedSections = new Set();
  const PACKAGE_CARD_SELECTOR = '#pacotes .card[data-destino], .pacotes-page .card[data-destino], .ofertas-page .card[data-destino], .oferta-row[data-destino], .dest-option[data-destino]';
  const CONTATO_DEBOUNCE_MS = 3000;
  const recentContatoKeys = new Map();
  let packageObserver = null;

  /** Debounce Contato Ads + purchase intent (same key within window = skip). */
  function claimContatoFire(key) {
    const now = Date.now();
    const prev = recentContatoKeys.get(key) || 0;
    if (now - prev < CONTATO_DEBOUNCE_MS) return false;
    recentContatoKeys.set(key, now);
    return true;
  }

  function isHighIntentWaCta(wa, card) {
    if (!card || !wa) return false;
    return !!(
      wa.closest('.card__footer .btn--whatsapp') ||
      wa.closest('.dest-option__cta') ||
      wa.closest('.oferta-row__price .btn--whatsapp')
    );
  }

  /* ── Helpers ─────────────────────────────────────── */

  const VCB_CONSENT_KEY = 'vcb_consent_analytics';

  function canTrack() {
    return typeof gtag === 'function';
  }

  /** Espelha gtag_report_conversion em ga4.html — só mede leads/purchase com consent. */
  function canTrackAds() {
    try {
      return localStorage.getItem(VCB_CONSENT_KEY) === 'granted';
    } catch (e) {
      return false;
    }
  }

  function pageMeta() {
    return {
      page_location: window.location.href,
      page_title: document.title
    };
  }

  function trackEvent(name, params) {
    if (!canTrack()) return;
    gtag('event', name, Object.assign({}, pageMeta(), params || {}));
  }

  function slugify(text) {
    return (text || '')
      .toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_|_$/g, '');
  }

  function inferRegion(destino) {
    const d = (destino || '').toLowerCase();
    if (/gramado|bonito|bento|maria fuma[cç]a|serra gaucha/.test(d)) return 'brasil_sul';
    if (/rio quente|caldas novas/.test(d)) return 'brasil_centro';
    if (/chapada|salvador|bahia|aracaju|fortaleza|jo[aã]o pessoa|porto seguro|macei[oó]|recife|olinda|porto de galinhas|natal|ilheus|ilh[eé]us/.test(d)) return 'brasil_nordeste';
    if (/jamaica|montego/.test(d)) return 'jamaica';
    if (/buenos aires|ushuaia|bariloche|patagonia|salta|cafayate|humahuaca|calafate|perito/.test(d)) return 'argentina';
    if (/santiago|atacama/.test(d)) return 'chile';
    if (/peru|vale sagrado|cusco/.test(d)) return 'peru';
    if (/dubai|turquia|istambul|capadocia|pamukkale/.test(d)) return 'oriente';
    if (/disney|california/.test(d)) return 'eua';
    if (/mexico|m[eé]xico|teotihuac/.test(d)) return 'mexico';
    if (/curacao|cura[cç]ao/.test(d)) return 'caribe';
    if (/uruguai|montevid/.test(d)) return 'uruguai';
    if (/canc[uú]n|playa mujeres|bahamas|san andres|caribe/.test(d)) return 'caribe';
    if (/navio|msc|cruzeiro|costa serena/.test(d)) return 'cruzeiro';
    return 'outros';
  }

  function getCategoryLabel(categoria) {
    const map = {
      'grupo-guia': 'grupos_com_guia',
      'completo': 'pacote_completo',
      'sem-aereo': 'cruzeiro',
      'promo-voo': 'promo_voo',
      'campanha': 'campanha'
    };
    return map[categoria] || categoria || 'outros';
  }

  function getPackageMeta(el) {
    const card = el && el.closest ? el.closest('.card[data-destino], .oferta-row[data-destino], .dest-option[data-destino]') : el;
    if (!card) return null;

    const destino = card.getAttribute('data-destino') || 'desconhecido';
    const categoria = card.getAttribute('data-categoria') || 'outros';
    const region = card.getAttribute('data-regiao') || inferRegion(destino);

    return {
      package_name: destino,
      package_slug: slugify(destino),
      package_category: getCategoryLabel(categoria),
      package_region: region,
      service_name: destino,
      service_category: categoria
    };
  }

  function packageItems(meta) {
    if (!meta) return [];
    return [{
      item_id: meta.package_slug,
      item_name: meta.package_name,
      item_category: meta.package_category,
      item_category2: meta.package_region
    }];
  }

  function packageItemsWithPrice(meta, price) {
    if (!meta) return [];
    return [{
      item_id: meta.package_slug,
      item_name: meta.package_name,
      item_category: meta.package_category,
      item_category2: meta.package_region,
      quantity: 1,
      price: price
    }];
  }

  function parseBrlAmount(text) {
    if (!text) return 0;
    const match = String(text).match(/R\$\s*([\d.]+)/);
    if (!match) return 0;
    const normalized = match[1].replace(/\./g, '');
    const val = parseFloat(normalized);
    return Number.isFinite(val) ? val : 0;
  }

  function parsePackageValue(card) {
    if (!card) return 0;

    const attrVal = card.getAttribute('data-valor-total');
    if (attrVal) {
      const parsed = parseFloat(attrVal.replace(/\./g, '').replace(',', '.'));
      if (Number.isFinite(parsed) && parsed > 0) return parsed;
    }

    const destTotal = card.querySelector('.dest-option__total');
    if (destTotal) {
      const fromDest = parseBrlAmount(destTotal.textContent);
      if (fromDest > 0) return fromDest;
    }

    const totalEl = card.querySelector('.card__total');
    if (totalEl) {
      const fromTotal = parseBrlAmount(totalEl.textContent);
      if (fromTotal > 0) return fromTotal;
    }

    const parcelaEl = card.querySelector('.card__parcela strong');
    if (parcelaEl) {
      const parcela = parseBrlAmount(parcelaEl.textContent);
      if (parcela > 0) return parcela * 12;
    }

    const rowVal = card.querySelector('.oferta-row__value, .oferta-row__price .oferta-row__value');
    if (rowVal) {
      const fromRow = parseBrlAmount(rowVal.textContent);
      if (fromRow > 0) return fromRow;
    }

    const sortPrice = parseFloat(card.getAttribute('data-sort-price') || '');
    if (Number.isFinite(sortPrice) && sortPrice > 0) return sortPrice;

    return 0;
  }

  function getCtaText(el) {
    return (el.getAttribute('aria-label') || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 100);
  }

  function getCtaLocation(el) {
    if (el.closest('.fab-whatsapp')) return 'floating_button';
    if (el.closest('.navbar__cta')) return 'navbar';
    if (el.closest('#hero')) return 'hero';
    if (el.closest('#sobre')) return 'about_section';
    if (el.closest('#como-funciona')) return 'how_it_works_section';
    if (el.closest('#pacotes') || el.closest('.pacotes-page')) return 'services_section';
    if (el.closest('#links')) return 'links_section';
    if (el.closest('#pagamento')) return 'payment_section';
    if (el.closest('#faq')) return 'faq_section';
    if (el.closest('#depoimentos')) return 'testimonials_section';
    if (el.closest('.depoimentos__cta')) return 'final_cta';
    if (el.closest('.pacotes__cta-extra')) return 'custom_itinerary_cta';
    if (el.closest('.footer')) return 'footer';
    if (el.closest('#modalFormulario')) return 'contact_form';
    return 'unknown';
  }

  function inferLeadType(href, el) {
    const text = decodeURIComponent((href || '').toLowerCase());
    if (text.includes('or%C3%A7amento') || text.includes('orçamento')) return 'quote_request';
    if (text.includes('roteiro') || text.includes('planejar')) return 'custom_itinerary_request';
    if (text.includes('pagamento')) return 'quote_request';
    if (el && el.closest('#pacotes .card')) return 'quote_request';
    return 'general_contact';
  }

  function inferServiceName(el, href) {
    const meta = getPackageMeta(el);
    if (meta) return meta.package_slug;
    const text = decodeURIComponent((href || '').toLowerCase());
    if (text.includes('roteiro') || text.includes('planejar')) return 'roteiro_personalizado';
    if (text.includes('or%C3%A7amento') || text.includes('orçamento')) return 'geral';
    return 'geral';
  }

  /* ── Eventos de pacote ─────────────────────────── */

  function trackPackageView(card) {
    const meta = getPackageMeta(card);
    if (!meta || viewedPackages.has(meta.package_slug)) return;
    viewedPackages.add(meta.package_slug);

    trackEvent('view_item', {
      currency: 'BRL',
      items: packageItems(meta),
      package_name: meta.package_name,
      package_slug: meta.package_slug,
      package_category: meta.package_category,
      package_region: meta.package_region
    });

    trackEvent('package_impression', {
      package_name: meta.package_name,
      package_slug: meta.package_slug,
      package_category: meta.package_category,
      package_region: meta.package_region,
      engagement_type: 'viewport'
    });
  }

  function trackPackageSelect(card, interactionType) {
    const meta = getPackageMeta(card);
    if (!meta) return;

    trackEvent('select_item', {
      items: packageItems(meta),
      package_name: meta.package_name,
      package_slug: meta.package_slug,
      package_category: meta.package_category,
      package_region: meta.package_region,
      interaction_type: interactionType
    });

    trackEvent('destination_interest', {
      destination_name: meta.package_name,
      destination_slug: meta.package_slug,
      destination_region: meta.package_region,
      package_category: meta.package_category,
      interaction_type: interactionType
    });
  }

  function trackPackagePurchaseIntent(card, transactionId) {
    const meta = getPackageMeta(card);
    if (!meta) return null;

    const value = parsePackageValue(card);
    const txId = transactionId || ('pkg_' + meta.package_slug + '_' + Date.now());

    if (!canTrackAds()) return txId;

    trackEvent('purchase', {
      transaction_id: txId,
      value: value,
      currency: 'BRL',
      items: packageItemsWithPrice(meta, value),
      purchase_type: 'whatsapp_intent',
      package_name: meta.package_name,
      package_slug: meta.package_slug,
      package_category: meta.package_category,
      package_region: meta.package_region
    });
    return txId;
  }

  function trackCategoryView(categoryEl) {
    const id = categoryEl.id;
    if (!id || viewedCategories.has(id)) return;
    viewedCategories.add(id);

    const heading = categoryEl.querySelector('.pacotes__subhead');
    const label = heading ? heading.textContent.replace(/\s+/g, ' ').trim() : id;

    trackEvent('package_category_view', {
      category_id: id,
      category_name: label
    });
  }

  function trackSectionView(section) {
    const id = section.id;
    if (!id || viewedSections.has(id)) return;
    viewedSections.add(id);

    trackEvent('section_view', {
      section_id: id,
      section_name: id.replace(/-/g, '_')
    });
  }

  /* ── Leads ─────────────────────────────────────── */

  function trackGenerateLead(el, overrides) {
    if (!canTrackAds()) return;

    const href = el.getAttribute('href') || '';
    const meta = getPackageMeta(el);
    const channel = href.startsWith('mailto:') ? 'email'
      : href.includes('wa.me') ? 'whatsapp'
      : 'cta';

    trackEvent('generate_lead', Object.assign({
      lead_source: 'website',
      lead_channel: channel,
      lead_type: inferLeadType(href, el),
      service_name: inferServiceName(el, href),
      cta_location: getCtaLocation(el),
      cta_text: getCtaText(el),
      package_name: meta ? meta.package_name : undefined,
      package_slug: meta ? meta.package_slug : undefined,
      package_category: meta ? meta.package_category : undefined,
      package_region: meta ? meta.package_region : undefined,
      interest_level: meta ? 'high' : 'medium'
    }, overrides || {}));

    if (meta) {
      trackEvent('package_lead', {
        package_name: meta.package_name,
        package_slug: meta.package_slug,
        package_category: meta.package_category,
        package_region: meta.package_region,
        lead_channel: channel,
        cta_location: getCtaLocation(el)
      });
    }
  }

  /* ── API pública (script.js) ───────────────────── */

  window.VCBAnalytics = {
    trackEvent,
    trackGenerateLead,
    trackPackageView,
    trackPackageSelect,
    trackPackagePurchaseIntent,
    observePackageCard: function (card) {
      if (packageObserver && card) packageObserver.observe(card);
    },

    trackFormOpen: function () {
      trackEvent('form_start', {
        form_name: 'viagem_personalizada',
        form_location: 'links_section'
      });
    },

    trackFormLead: function () {
      trackEvent('form_submit', {
        form_name: 'viagem_personalizada',
        form_location: 'contact_form'
      });
      if (!canTrackAds()) return;
      trackEvent('generate_lead', {
        lead_source: 'website',
        lead_channel: 'form',
        lead_type: 'custom_itinerary_request',
        service_name: 'roteiro_personalizado',
        package_category: 'roteiro_personalizado',
        cta_location: 'contact_form',
        cta_text: 'Enviar pelo WhatsApp',
        interest_level: 'high'
      });
    },

    claimContatoFire: claimContatoFire
  };

  /* ── Impressões de pacotes (viewport) ──────────── */

  function initPackageImpressions() {
    const cards = document.querySelectorAll(PACKAGE_CARD_SELECTOR);
    if (!cards.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.intersectionRatio >= 0.55) {
            trackPackageView(entry.target);
          }
        });
      },
      { threshold: [0.55, 0.75] }
    );

    packageObserver = observer;
    cards.forEach((card) => observer.observe(card));
  }

  /* ── Visualização de categorias e seções ───────── */

  function initSectionImpressions() {
    const categories = document.querySelectorAll('.pacotes__category[id]');
    const sections = document.querySelectorAll(
      '#como-funciona, #pacotes, #links, #pagamento, #faq, #depoimentos'
    );

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting || entry.intersectionRatio < 0.35) return;
          if (entry.target.classList.contains('pacotes__category')) {
            trackCategoryView(entry.target);
          } else {
            trackSectionView(entry.target);
          }
        });
      },
      { threshold: 0.35 }
    );

    categories.forEach((el) => observer.observe(el));
    sections.forEach((el) => observer.observe(el));
  }

  function scheduleIdleObservers() {
    if ('requestIdleCallback' in window) {
      requestIdleCallback(function () {
        initPackageImpressions();
        initSectionImpressions();
      }, { timeout: 4000 });
    } else {
      window.addEventListener('load', function () {
        initPackageImpressions();
        initSectionImpressions();
      });
    }
  }

  scheduleIdleObservers();

  /* ── Profundidade de scroll ────────────────────── */

  (function initScrollDepth() {
    const marks = [25, 50, 75, 90];
    const scrollMarks = new Set();
    let maxScroll = 0;
    let ticking = false;

    function recalcMaxScroll() {
      const doc = document.documentElement;
      maxScroll = doc.scrollHeight - doc.clientHeight;
    }

    function onScrollFrame() {
      ticking = false;
      if (maxScroll <= 0) return;

      const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
      const pct = Math.round((scrollTop / maxScroll) * 100);
      marks.forEach((mark) => {
        if (pct >= mark && !scrollMarks.has(mark)) {
          scrollMarks.add(mark);
          trackEvent('scroll_depth', {
            percent_scrolled: mark,
            page_type: 'catalog'
          });
        }
      });
    }

    function onScroll() {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(onScrollFrame);
      }
    }

    recalcMaxScroll();
    window.addEventListener('resize', recalcMaxScroll, { passive: true });
    window.addEventListener('scroll', onScroll, { passive: true });
  })();

  /* ── Cliques ───────────────────────────────────── */

  document.addEventListener('click', function (e) {
    const wa = e.target.closest('a[href*="wa.me/' + WA_NUMBER + '"]');
    if (wa) {
      e.preventDefault();
      const card = wa.closest('.card[data-destino], .oferta-row[data-destino], .dest-option[data-destino]');
      const highIntent = isHighIntentWaCta(wa, card);
      const pkgMeta = card ? getPackageMeta(card) : null;
      const debounceKey = highIntent
        ? ('wa:' + (pkgMeta ? pkgMeta.package_slug : 'offer') + ':' + (card && card.getAttribute('data-categoria') || ''))
        : ('wa:generic:' + getCtaLocation(wa));
      const allowContato = claimContatoFire(debounceKey);
      let txId = null;

      if (highIntent && allowContato && card) {
        txId = 'pkg_' + (pkgMeta ? pkgMeta.package_slug : 'intent') + '_' + Date.now();
        trackPackagePurchaseIntent(card, txId);
      }
      if (card && pkgMeta) {
        const categoria = card.getAttribute('data-categoria') || '';
        if (categoria === 'promo-voo') trackEvent('flight_whatsapp_click', { package_slug: pkgMeta.package_slug, package_category: pkgMeta.package_category });
        else if (categoria === 'campanha') trackEvent('campaign_whatsapp_click', { package_slug: pkgMeta.package_slug, package_category: pkgMeta.package_category });
        else trackEvent('package_whatsapp_click', { package_slug: pkgMeta.package_slug, package_category: pkgMeta.package_category });
        trackEvent('service_click', {
          service_name: pkgMeta.package_name,
          service_category: pkgMeta.package_category,
          package_region: pkgMeta.package_region,
          package_slug: pkgMeta.package_slug,
          cta_text: getCtaText(wa),
          interaction_type: 'whatsapp_cta'
        });
      }
      trackGenerateLead(wa);
      // Google Ads "Contato" = qualquer clique WA do site (FAB/nav/hero/footer/pacote/form).
      // Meta de negócio: pessoa falar no WhatsApp. purchase GA4 continua só em CTA comercial.
      const href = wa.getAttribute('href');
      if (allowContato && typeof window.gtag_report_conversion === 'function') {
        window.gtag_report_conversion(href, {
          transaction_id: txId || ('wa_' + getCtaLocation(wa) + '_' + Date.now())
        });
      } else {
        window.open(href, '_blank', 'noopener,noreferrer');
      }
      return;
    }

    const mail = e.target.closest('a[href^="mailto:"]');
    if (mail) {
      trackGenerateLead(mail, {
        lead_channel: 'email',
        lead_type: 'general_contact',
        service_name: 'geral'
      });
      return;
    }

    const ig = e.target.closest('a[href*="instagram.com"]');
    if (ig) {
      trackEvent('social_click', {
        social_network: 'instagram',
        cta_text: getCtaText(ig),
        cta_location: getCtaLocation(ig)
      });
      return;
    }

    const nav = e.target.closest('#navLinks a, .footer__links a');
    if (nav && nav.getAttribute('href') && nav.getAttribute('href').startsWith('#')) {
      trackEvent('navigation_click', {
        link_text: getCtaText(nav),
        link_url: nav.getAttribute('href')
      });
      return;
    }

    const pkgImg = e.target.closest('.card__img-wrap img[data-lightbox]');
    if (pkgImg) {
      const card = pkgImg.closest('.card');
      if (card) trackPackageSelect(card, 'image_click');
      return;
    }

    const cardBody = e.target.closest(PACKAGE_CARD_SELECTOR);
    if (cardBody && !e.target.closest('a')) {
      // catalog-dest-card: script.js openDestModal already fires destination_interest (open_options)
      if (!cardBody.classList.contains('catalog-dest-card')) {
        trackPackageSelect(cardBody, 'card_explore');
      }
      return;
    }

    const faqBtn = e.target.closest('.faq__question');
    if (faqBtn) {
      trackEvent('faq_click', {
        faq_question: faqBtn.textContent.replace(/\s+/g, ' ').trim()
      });
      return;
    }

    const customCta = e.target.closest('.pacotes__cta-extra a');
    if (customCta) {
      trackEvent('destination_interest', {
        destination_name: 'roteiro_personalizado',
        destination_slug: 'roteiro_personalizado',
        interaction_type: 'custom_itinerary_cta'
      });
      return;
    }

    const ctaLink = e.target.closest(
      '.faq__cta a, .btn--outline, .depoimentos__cta a, .como-funciona__cta a, ' +
      '.servicos-hub__grid a, .internal-nav a, .internal-page a.btn, .error-page a.btn, ' +
      '.servico-card a, .links__grid a'
    );
    if (ctaLink) {
      const href = ctaLink.getAttribute('href') || '';
      if (href && !href.startsWith('#') && !href.includes('wa.me') &&
          !href.startsWith('mailto:') && !href.includes('instagram.com')) {
        trackEvent('cta_click', {
          cta_text: getCtaText(ctaLink),
          cta_location: getCtaLocation(ctaLink),
          link_url: href
        });
      }
    }
  });
})();
