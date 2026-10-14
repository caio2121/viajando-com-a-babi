(function () {
  'use strict';
  const state = { csrf: '', offers: [] };
  const $ = (id) => document.getElementById(id);
  const loginPanel = $('loginPanel');
  const appPanel = $('appPanel');

  function message(id, text, error) {
    const el = $(id);
    el.textContent = text || '';
    el.style.color = error ? '#a23b32' : '#238f8a';
  }

  async function request(path, options) {
    const headers = Object.assign({ 'Content-Type': 'application/json' }, (options && options.headers) || {});
    if (state.csrf) headers['X-CSRF-Token'] = state.csrf;
    const response = await fetch(path, Object.assign({}, options || {}, { headers }));
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error?.message || 'Falha na requisição');
    return payload;
  }

  function showApp() { loginPanel.hidden = true; appPanel.hidden = false; loadOffers(); loadAudit(); loadSyncRuns(); }

  async function login(event) {
    event.preventDefault();
    try {
      const result = await request('/api/admin/login', { method: 'POST', body: JSON.stringify({ username: $('username').value.trim(), password: $('password').value }) });
      state.csrf = result.csrf;
      $('password').value = '';
      showApp();
    } catch (error) { message('loginMessage', error.message, true); }
  }

  function resetForm() {
    $('offerId').value = '';
    $('formTitle').textContent = 'Novo pacote';
    $('offerForm').reset();
    $('imageUrl').value = 'assets/og-share.jpeg';
    $('status').value = 'draft';
  }

  function edit(offer) {
    const data = offer.data || {};
    $('offerId').value = offer.id;
    $('formTitle').textContent = 'Editar pacote';
    $('title').value = data.title || offer.title || '';
    $('destination').value = data.destination || offer.destination || '';
    $('originBucket').value = data.origin_bucket || offer.origin_bucket || 'sem-aereo';
    $('originAirport').value = data.origin_airport || offer.origin_airport || '';
    $('originCity').value = data.origin_city || offer.origin_city || '';
    $('dates').value = (data.dates || []).join(', ');
    $('price').value = data.price || offer.sort_price || '';
    $('imageUrl').value = data.image_url || 'assets/og-share.jpeg';
    $('features').value = (data.features || []).join('\n');
    $('status').value = offer.status || 'draft';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function renderOffers() {
    const root = $('offers');
    root.innerHTML = '';
    state.offers.forEach((offer) => {
      const item = document.createElement('article');
      item.className = 'offer';
      const info = document.createElement('div');
      const strong = document.createElement('strong'); strong.textContent = offer.title;
      const origin = offer.source === 'operator' ? 'Provider' : 'Manual';
      const stale = offer.sync_state === 'stale' ? ' · stale' : '';
      const small = document.createElement('small'); small.textContent = `${origin} · ${offer.status} · ${offer.provider}${stale}`;
      info.append(strong, small);
      const actions = document.createElement('div'); actions.className = 'offer-actions';
      if (offer.source === 'operator') {
        const highlightButton = document.createElement('button');
        highlightButton.textContent = offer.is_highlight ? 'Remover destaque' : 'Destacar';
        highlightButton.onclick = () => toggleProviderHighlight(offer);
        actions.appendChild(highlightButton);
        if ((offer.override_fields || []).includes('is_highlight')) {
          const removeOverrideButton = document.createElement('button');
          removeOverrideButton.className = 'secondary';
          removeOverrideButton.textContent = 'Voltar ao provider';
          removeOverrideButton.onclick = () => removeProviderHighlight(offer);
          actions.appendChild(removeOverrideButton);
        }
      } else {
        const editButton = document.createElement('button'); editButton.textContent = 'Editar'; editButton.onclick = () => edit(offer);
        const toggleButton = document.createElement('button'); toggleButton.className = 'secondary'; toggleButton.textContent = offer.status === 'published' ? 'Despublicar' : 'Publicar';
        toggleButton.onclick = () => updateStatus(offer, offer.status === 'published' ? 'draft' : 'published');
        const archiveButton = document.createElement('button'); archiveButton.className = 'secondary'; archiveButton.textContent = 'Desativar'; archiveButton.onclick = () => archive(offer);
        actions.append(editButton, toggleButton, archiveButton);
      }
      const historyButton = document.createElement('button');
      historyButton.className = 'secondary'; historyButton.textContent = 'Histórico';
      const history = document.createElement('div'); history.className = 'offer-history'; history.hidden = true;
      historyButton.onclick = async () => { history.hidden = !history.hidden; if (!history.hidden) await loadHistory(offer, history); };
      actions.appendChild(historyButton);
      item.append(info, actions, history); root.appendChild(item);
    });
  }

  async function loadOffers() {
    try { const result = await request('/api/admin/offers'); state.offers = result.items || []; renderOffers(); }
    catch (error) { message('appMessage', error.message, true); }
  }

  async function loadAudit() {
    try {
      const result = await request('/api/admin/audit?limit=50');
      const root = $('auditEvents');
      root.innerHTML = '';
      (result.items || []).forEach((event) => {
        const item = document.createElement('article');
        item.className = 'audit-event';
        const title = document.createElement('strong');
        title.textContent = `${event.created_at} · ${event.action}`;
        const detail = document.createElement('small');
        detail.textContent = `${event.resource_type} ${event.resource_id || ''} · origem ${event.ip_hash || 'n/a'}`;
        item.append(title, detail);
        root.appendChild(item);
      });
    } catch (error) { message('appMessage', error.message, true); }
  }

  async function loadSyncRuns() {
    try {
      const result = await request('/api/admin/sync-runs?limit=30');
      const root = $('syncRuns');
      root.innerHTML = '';
      (result.items || []).forEach((run) => {
        const item = document.createElement('article');
        item.className = 'audit-event';
        const title = document.createElement('strong');
        title.textContent = `${run.started_at} · ${run.provider} · ${run.status}`;
        const detail = document.createElement('small');
        const counts = Object.entries(run.item_counts || {}).map(([key, value]) => `${key}: ${value}`).join(' · ');
        detail.textContent = `${run.details?.error_code || 'snapshot'} · itens ${counts || 'n/a'} · checksum ${run.snapshot_checksum || 'n/a'}`;
        item.append(title, detail);
        root.appendChild(item);
      });
    } catch (error) { message('appMessage', error.message, true); }
  }

  async function loadHistory(offer, root) {
    try {
      const result = await request(`/api/admin/offers/${offer.id}/history?limit=10`);
      root.textContent = '';
      (result.items || []).forEach((entry) => {
        const item = document.createElement('small');
        const changes = Object.entries(entry.changes || {}).map(([field, change]) => `${field}: ${change.before ?? '—'} → ${change.after ?? '—'}`).join(' · ');
        item.textContent = `${entry.created_at} · ${entry.change_type} · ${changes || 'sem mudança de campo'}`;
        root.appendChild(item);
      });
      if (!result.items?.length) root.textContent = 'Sem histórico.';
    } catch (error) { message('appMessage', error.message, true); }
  }

  async function toggleProviderHighlight(offer) {
    try {
      await request(`/api/admin/offers/${offer.id}/overrides`, {
        method: 'POST',
        body: JSON.stringify({ field: 'is_highlight', value: !offer.is_highlight, reason: 'ajuste editorial no painel' })
      });
      await loadOffers();
    } catch (error) { message('appMessage', error.message, true); }
  }

  async function removeProviderHighlight(offer) {
    try {
      await request(`/api/admin/offers/${offer.id}/overrides/is_highlight`, { method: 'DELETE', body: '{}' });
      await loadOffers();
    } catch (error) { message('appMessage', error.message, true); }
  }

  function formData() {
    return {
      kind: 'pacote', title: $('title').value.trim(), destination: $('destination').value.trim(),
      origin_bucket: $('originBucket').value, origin_airport: $('originAirport').value.trim(), origin_city: $('originCity').value.trim(),
      dates: $('dates').value.split(',').map((value) => value.trim()).filter(Boolean), price: $('price').value,
      image_url: $('imageUrl').value.trim(), features: $('features').value.split('\n').map((value) => value.trim()).filter(Boolean), status: $('status').value
    };
  }

  async function save(event) {
    event.preventDefault();
    try {
      const id = $('offerId').value;
      await request(id ? `/api/admin/offers/${id}` : '/api/admin/offers', { method: id ? 'PUT' : 'POST', body: JSON.stringify(formData()) });
      message('appMessage', 'Oferta salva.'); resetForm(); await loadOffers();
    } catch (error) { message('appMessage', error.message, true); }
  }

  async function updateStatus(offer, status) {
    try { const data = Object.assign({}, offer.data || {}, { status }); await request(`/api/admin/offers/${offer.id}`, { method: 'PUT', body: JSON.stringify(data) }); await loadOffers(); }
    catch (error) { message('appMessage', error.message, true); }
  }

  async function archive(offer) {
    if (!window.confirm('Desativar este pacote?')) return;
    try { await request(`/api/admin/offers/${offer.id}`, { method: 'DELETE', body: '{}' }); await loadOffers(); }
    catch (error) { message('appMessage', error.message, true); }
  }

  $('loginForm').addEventListener('submit', login);
  $('offerForm').addEventListener('submit', save);
  $('clearButton').addEventListener('click', resetForm);
  $('logoutButton').addEventListener('click', async () => { try { await request('/api/admin/logout', { method: 'POST', body: '{}' }); } finally { window.location.reload(); } });
  $('loadAuditButton').addEventListener('click', loadAudit);
  $('loadSyncRunsButton').addEventListener('click', loadSyncRuns);
})();
