# Baseline e budgets de performance

## Escopo

Este documento separa medições de laboratório de métricas reais de usuários. A
fonte local disponível é `.lighthouse-desktop.json`, gerada para a home de
produção em 2026-06-15. Ela não prova o estado atual mobile nem autoriza
otimização ou deploy.

## Baseline disponível

| Dimensão | Valor |
|---|---|
| URL solicitada | `https://viajandocomababi.com.br/` |
| Data do artifact | 2026-06-15T17:36:54Z |
| Perfil | Lighthouse desktop |
| Viewport | 1350 × 940, DPR 1 |
| Performance score | 0,95 |
| FCP | 1,117 s |
| LCP | 1,166 s |
| CLS | 0,0002 |
| TBT | 0 ms |
| Speed Index | 1,117 s |

Os números acima são lab data e devem ser comparados somente com execuções de
mesmo perfil. A baseline mobile histórica em `docs/seo-baseline.md` é separada
e precisa de nova execução reproduzível antes de virar gate.

## Budgets propostos

São limites iniciais para validação em staging; não são aprovação final.

| Página/perfil | LCP | INP | CLS | TTFB | JS transferido | Imagens |
|---|---:|---:|---:|---:|---:|---:|
| Home mobile | ≤ 2,5 s | ≤ 200 ms | ≤ 0,10 | ≤ 800 ms | ≤ 180 KB | ≤ 1,2 MB |
| Catálogo mobile | ≤ 2,8 s | ≤ 200 ms | ≤ 0,10 | ≤ 800 ms | ≤ 220 KB | ≤ 1,8 MB |
| Home desktop | ≤ 2,0 s | ≤ 200 ms | ≤ 0,10 | ≤ 500 ms | ≤ 220 KB | ≤ 1,5 MB |
| API catálogo p95 | — | — | — | ≤ 500 ms | payload ≤ 250 KB | — |
| Admin critical path | ≤ 3,0 s | ≤ 300 ms | ≤ 0,10 | ≤ 800 ms | ≤ 250 KB | upload conforme limite |

Os budgets devem ser ajustados após medir rede/dispositivo representativo,
payload dinâmico, mídia real e API paginada. Uma exceção precisa de métrica,
causa, owner e prazo.

## Cenários reproducíveis

1. Home sem API local, preservando fallback estático.
2. Home com API local e catálogo completo.
3. Catálogo com filtros/ordenação e dataset representativo.
4. Admin após login com listagem e formulário.
5. Mobile 320/375 px em rede controlada; desktop 1350 px.
6. API com banco vazio, banco fixture e provider indisponível.

Cada execução deve registrar versão do commit/worktree, navegador, viewport,
rede, dataset, data, JSON completo e screenshot/trace em caso de regressão.

## Checks de regressão

- [ ] Lighthouse mobile e desktop das páginas críticas.
- [ ] LCP/INP/CLS e TTFB reportados separadamente.
- [ ] Tamanho transferido de HTML/CSS/JS/imagens.
- [ ] API p50/p95 e plano das queries críticas.
- [ ] Comparação com baseline do mesmo perfil.
- [ ] Sem regressão de SEO, alt, fallback ou analytics consentido.
- [ ] Budgets ainda não bloqueiam release até nova medição e aprovação.

## Limitações e próximos passos

- não há RUM aprovado; ver EPIC-10.5;
- não há baseline mobile atual no artifact local;
- não há perfil de carga da API dinâmica;
- compressão/cache e variantes de mídia dependem de EPIC-01/10.2/10.3;
- Core Web Vitals de campo exigem revisão de consentimento e privacidade.
