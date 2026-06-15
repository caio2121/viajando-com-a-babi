# SEO — baseline e monitoramento

Documento de referência para a **Fase 8** do plano SEO/GEO (Viajando com a Babi).

## Google Search Console

1. Acesse [Google Search Console](https://search.google.com/search-console)
2. Adicionar propriedade: `https://viajandocomababi.com.br/` (domínio ou prefixo URL)
3. Verificar via DNS (recomendado para domínio customizado no GitHub Pages) ou arquivo HTML
4. Enviar sitemap: `https://viajandocomababi.com.br/sitemap.xml`

## URLs para inspecionar após deploy

| URL | Objetivo |
|-----|----------|
| `/` | Home — pacotes + institucional |
| `/pacotes.html` | Hub catálogo |
| `/faq.html` | FAQPage Schema |
| `/sobre.html` | Entidade Person |
| `/consultoria-de-viagem.html` | Serviço secundário |

## GA4 (Measurement ID: G-WGDNTSY8WM)

- Baseline: relatório **Aquisição → Tráfego orgânico** (primeiros 30 dias pós-deploy)
- Conversões: eventos `generate_lead`, `package_lead`, `purchase` (intenção WhatsApp)
- Documentação de eventos: [`docs/analytics-pacotes.md`](analytics-pacotes.md)

## Validações técnicas

- [Rich Results Test](https://search.google.com/test/rich-results) — `faq.html`
- [Schema Markup Validator](https://validator.schema.org/) — home e páginas de serviço
- [PageSpeed Insights](https://pagespeed.web.dev/) — mobile, URLs `/` e `/pacotes.html`

## Performance (Lighthouse / PSI)

Checklist pós-deploy (mobile):

| URL | Verificar |
|-----|-----------|
| `/` | LCP &lt; 2,5 s · payload &lt; 1,2 MB · render-blocking &lt; 200 ms · 8 cards destaque |
| `/pacotes.html` | Catálogo completo (23 cards) · imagens responsivas · GA4 deferido |

Metas de payload e DOM na home (jun/2026):

| Métrica | Antes (approx.) | Meta |
|---------|-----------------|------|
| Payload total | ~3,8 MB | &lt; 1,2 MB |
| DOM elements | ~1.021 | &lt; 550 |
| Render-blocking | ~560 ms | &lt; 200 ms |

Scripts de manutenção: `_optimize_images.py`, `_update_picture_srcset.py`, `_build_pacotes.py`.

## Cache (Cloudflare + GitHub Pages)

GitHub Pages serve HTML com `Cache-Control: max-age=600` (10 min). Assets versionados (`style.css?v=19`, `script.js?v=19`) devem ter TTL longo via **Cloudflare Cache Rules** (domínio `viajandocomababi.com.br`):

| Padrão | TTL sugerido | Notas |
|--------|--------------|-------|
| `/assets/*` | 1 ano | WebP, logos, og-share |
| `/pacotes/*` | 1 ano | Imagens de pacotes + variantes `-400`/`-800` |
| `/*.css`, `/*.js` | 1 ano | Query `?v=N` invalida cache ao bump |
| `/*.html` | Respeitar origem (10 min) ou 1 h | HTML muda com mais frequência |

Regra exemplo (Cloudflare Dashboard → Cache → Cache Rules): *If URI Path matches `/assets/*` OR `/pacotes/*` OR ends with `.css` OR `.js` → Cache eligibility: Eligible · Edge TTL: 1 year*.

Sem Cloudflare na frente do GitHub Pages: revisitas dentro de 10 min ainda se beneficiam de cache de sessão do browser para assets versionados.

## Métricas alvo (mobile)

| Métrica | Meta |
|---------|------|
| LCP | &lt; 2,5 s |
| CLS | &lt; 0,1 |
| INP | &lt; 200 ms |

## Relatório mensual sugerido

1. Impressões e cliques orgânicos (GSC)
2. Queries com "pacote", "viagem [destino]", "consultoria viagem"
3. Páginas mais exibidas
4. Leads GA4 por origem (orgânico vs direto vs social)

## Pendências de dados (atualizar quando disponível)

- URL do Google Business Profile (link em depoimentos)
- Bio expandida da Babi em `sobre.html`
- Termos de uso (`termos.html`), se necessário

## Histórico de alterações SEO

| Data | Fase | Resumo |
|------|------|--------|
| 2026-06 | 1–7 | FAQ hub, páginas institucionais, Schema expandido, robots.txt, logo-vcb, performance |
| 2026-06 | Perf | Home 8 destaques, srcset 400w/800w, LCP preload, GA4/FA defer, scroll depth throttle |
