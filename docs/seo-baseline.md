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
- [PageSpeed Insights](https://pagespeed.web.dev/) — mobile, URL `/`

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
