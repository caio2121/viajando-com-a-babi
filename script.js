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

  function openModal() {
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';

    // Close mobile nav if open
    const navLinks  = document.getElementById('navLinks');
    const hamburger = document.getElementById('hamburger');
    if (navLinks && navLinks.classList.contains('open')) {
      navLinks.classList.remove('open');
      hamburger && hamburger.classList.remove('open');
      hamburger && hamburger.setAttribute('aria-expanded', 'false');
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

  trigger && trigger.addEventListener('click', openModal);
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

    window.open(
      'https://wa.me/5521920064617?text=' + encodeURIComponent(msg),
      '_blank',
      'noopener,noreferrer'
    );
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
