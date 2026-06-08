/* ═══════════════════════════════════════════════════
   VIAJANDO COM A BABI — analytics.js
   GA4 · Eventos de conversão · Sem dados pessoais (LGPD)
═══════════════════════════════════════════════════ */

'use strict';

(function initAnalytics() {
  const WA_NUMBER = '5521920064617';

  function canTrack() {
    return typeof gtag === 'function';
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

  function getCtaText(el) {
    return (el.getAttribute('aria-label') || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 100);
  }

  function getCtaLocation(el) {
    if (el.closest('.fab-whatsapp')) return 'floating_button';
    if (el.closest('.navbar__cta')) return 'navbar';
    if (el.closest('#hero')) return 'hero';
    if (el.closest('#sobre')) return 'about_section';
    if (el.closest('#como-funciona')) return 'how_it_works_section';
    if (el.closest('#pacotes')) return 'services_section';
    if (el.closest('#links')) return 'links_section';
    if (el.closest('#pagamento')) return 'payment_section';
    if (el.closest('#faq')) return 'faq_section';
    if (el.closest('#depoimentos')) return 'testimonials_section';
    if (el.closest('.depoimentos__cta')) return 'final_cta';
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
    const card = el && el.closest('.card[data-destino]');
    if (card) return card.getAttribute('data-destino') || 'geral';
    const text = decodeURIComponent((href || '').toLowerCase());
    if (text.includes('roteiro') || text.includes('planejar')) return 'roteiro_personalizado';
    if (text.includes('or%C3%A7amento') || text.includes('orçamento')) return 'geral';
    return 'geral';
  }

  function trackGenerateLead(el, overrides) {
    const href = el.getAttribute('href') || '';
    const channel = href.startsWith('mailto:') ? 'email'
      : href.includes('wa.me') ? 'whatsapp'
      : 'cta';

    trackEvent('generate_lead', Object.assign({
      lead_source: 'website',
      lead_channel: channel,
      lead_type: inferLeadType(href, el),
      service_name: inferServiceName(el, href),
      cta_location: getCtaLocation(el),
      cta_text: getCtaText(el)
    }, overrides || {}));
  }

  window.VCBAnalytics = {
    trackEvent,
    trackGenerateLead,
    trackFormLead: function () {
      trackEvent('generate_lead', {
        lead_source: 'website',
        lead_channel: 'form',
        lead_type: 'custom_itinerary_request',
        service_name: 'roteiro_personalizado',
        cta_location: 'contact_form',
        cta_text: 'Enviar pelo WhatsApp'
      });
    }
  };

  document.addEventListener('click', function (e) {
    const wa = e.target.closest('a[href*="wa.me/' + WA_NUMBER + '"]');
    if (wa) {
      const card = wa.closest('.card[data-destino]');
      if (card) {
        trackEvent('service_click', {
          service_name: card.getAttribute('data-destino') || 'geral',
          service_category: card.getAttribute('data-categoria') || 'travel_planning',
          cta_text: getCtaText(wa)
        });
      }
      trackGenerateLead(wa);
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
      trackEvent('destination_interest', {
        destination_name: card ? card.getAttribute('data-destino') : 'unknown'
      });
      return;
    }

    const faqBtn = e.target.closest('.faq__question');
    if (faqBtn) {
      trackEvent('faq_click', {
        faq_question: faqBtn.textContent.replace(/\s+/g, ' ').trim()
      });
    }
  });
})();
