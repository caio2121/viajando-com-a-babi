# Estratégia de testes e matriz de evidências

## Objetivo

Validar o site estático, a API local, o admin e os componentes futuros com
testes determinísticos, negativos e reproduzíveis. A cobertura é orientada a
risco; não há meta artificial de 100%.

## Pirâmide

| Camada | Escopo | Comando/ambiente | Gate |
|---|---|---|---|
| Unitário | validação de payload, normalização, renderer, consentimento e helpers | Python/Node sem rede | zero falha |
| Integração | SQLite, migrations, provider, transações, fallback e storage | banco temporário/fixtures | zero falha e integrity_check |
| API | health, catálogo, login, CSRF, CRUD, autorização, erros e limites | processo local isolado | todos os P0 |
| Segurança | XSS, SQLi, SSRF, path traversal, IDOR, upload, headers, secrets | alvo local autorizado | critical/high bloqueiam |
| E2E | catálogo, filtros, CTA, consentimento, admin, mídia e sync | Playwright desktop/mobile | smoke obrigatório |
| Acessibilidade | axe, teclado, foco, modal, formulários, contraste e leitor | páginas críticas | nenhuma regressão critical |
| Performance | Lighthouse, payload, API p95, query plan e imagem | cenários versionados | budgets aprovados |
| Resiliência | timeout, retry, lock, falha de provider, banco, mídia, disco e job | compose descartável | last-known-good e restore |
| Release | build, SBOM, scan, staging, migration, smoke e rollback | CI/staging fictício | todos os gates |

## Matriz requisito → teste → evidência

| ID | Requisito | Teste obrigatório | Evidência |
|---|---|---|---|
| T-01 | Fallback estático continua funcionando sem API | contrato HTML + servidor sem backend | report de contrato e screenshot |
| T-02 | Import é idempotente e vazio não apaga estado | fixture válida, repetida, vazia e inválida | contagens, sync_runs e diff |
| T-03 | Migrations funcionam em banco limpo/existente | upgrade, constraints, FK, integrity_check e falha parcial | migration log e DB checks |
| T-04 | Admin autentica e aplica CSRF/autorização | login inválido, cookie adulterado, CSRF, IDOR e role matrix | respostas HTTP e audit events |
| T-05 | Conteúdo do usuário não executa | HTML/URL/JSON adversarial | assertions XSS e DAST |
| T-06 | Upload aceita somente mídia segura | MIME forjado, polyglot, executável, limite, EXIF, resolução | manifest sanitizado e testes |
| T-07 | Mídia persiste e variantes são corretas | rebuild/restart, preview, substituição, órfão e srcset | hashes, network log e screenshot |
| T-08 | Consentimento controla trackers | denied/granted/revoked com inspeção de rede | HAR, requests e screenshots |
| T-09 | Provider não derruba catálogo | timeout, 4xx/5xx, schema drift, lote vazio/parcial | last-known-good e sync history |
| T-10 | Jobs são exclusivos e idempotentes | concorrência, crash, retry, timeout e reexecução | job_runs, lock e logs |
| T-11 | Backup permite restore | checksum, corrupção, clean-room e DR drill | backup manifest, restore e RPO/RTO |
| T-12 | Imagem/release é governada | dependency scan, secret scan, SBOM, digest e tamper | reports e exception register |
| T-13 | UI é acessível e responsiva | axe, teclado, foco, 320/375/768/1440 | screenshots, traces e a11y report |
| T-14 | Performance não regride | Lighthouse, API load, EXPLAIN, budgets | before/after JSON |
| T-15 | URLs/SEO são preservados | crawl, sitemap, robots, schema, redirects e 404 | URL map e crawl report |

## Fixtures e dados permitidos

- somente destinos, preços, datas e credenciais sintéticas;
- nenhum token, cookie, IP real ou dado de cliente;
- provider fake com respostas válidas, vazias, incompatíveis, lentas e 5xx;
- banco temporário por teste, com migrations aplicadas automaticamente;
- mídia gerada no laboratório, com bytes malformados e EXIF sintético;
- snapshots e HTML de teste versionados somente quando necessários para
  reproduzir um contrato;
- cada fixture informa origem, finalidade e limpeza.

## Cenários de erro obrigatórios

1. payload JSON inválido, incompleto, grande, Unicode inválido e `Content-Length`
   inválido/negativo;
2. cookie administrativo malformado, expirado, adulterado e replay;
3. CSRF ausente/incorreto, usuário desativado e permissão insuficiente;
4. SQL/HTML/URL/path adversarial e IDOR entre ofertas;
5. imagem falsa, executável renomeado, resolução/tamanho excessivos e disco
   cheio;
6. provider indisponível, schema inesperado, lote vazio/parcial e corrida;
7. migration falha no meio, backup corrompido e restore de versão anterior;
8. job simultâneo, timeout, retry excedido e alerta duplicado;
9. tracker recusado, revogado e script externo indisponível;
10. viewport móvel, teclado, reduced motion, rede lenta e API indisponível.

## Política de execução

- testes não acessam produção, DNS, banco remoto ou provider real;
- testes destrutivos usam somente volumes/instalações descartáveis identificadas;
- cada falha preserva trace, log redigido, screenshot ou fixture mínima;
- teste flaky recebe issue, owner e prazo; não é ignorado silenciosamente;
- qualquer P0 sem teste ou justificativa formal mantém release bloqueada;
- a matriz final de `EPIC-19.2` deve apontar o comando e o artefato exatos.

## Baseline atual

No momento desta task, a suíte local existente executa 12 testes com sucesso após
a migration fundacional. Isso é apenas baseline e não aprova os controles ainda
pendentes desta matriz.
