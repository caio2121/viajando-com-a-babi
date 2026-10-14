# Modelo de ameaças e matriz de verificação

## Escopo

Este modelo cobre a aplicação dinâmica local e a futura promoção para staging e
produção. O site estático, o workflow que publica no GitHub Pages e o fallback
HTML são tratados como ativos de compatibilidade. Nenhum achado deste documento
autoriza deploy.

Referências técnicas usadas na matriz: práticas do OWASP Developer Guide sobre
autorização server-side, BOLA/IDOR, secure-by-default e logging seguro. A
aceitação final exige revisão independente da matriz e testes executados no alvo
local/staging.

## Ativos e limites de confiança

| Ativo | Confidencialidade | Integridade | Disponibilidade | Limite de confiança |
|---|---|---|---|---|
| Catálogo publicado | baixa | alta | alta | API/backend → navegador público |
| SQLite e mídia | média | alta | alta | container app → volume persistente |
| Sessão administrativa | alta | alta | média | navegador admin → endpoint admin |
| Credenciais e chaves | alta | alta | alta | ambiente/secret store → processo |
| Snapshot/provider | média | alta | média | operadora externa → adapter |
| Logs e auditoria | média | alta | média | processo → armazenamento de logs |
| Backups | alta | alta | alta | runtime → destino externo |
| Código/imagem de release | alta | alta | alta | repositório/CI → runtime |

## Fluxos e ameaças

| Fluxo | Abuso considerado | Controle necessário | Evidência futura | Estado |
|---|---|---|---|---|
| Visitante → catálogo/API | SQLi, XSS, enumeração, payload excessivo | queries parametrizadas, allowlist, limites, escape e erros genéricos | testes negativos + DAST local | pendente |
| Admin → login/sessão | brute force, replay, cookie forjado, CSRF | identidade individual, rate limit, sessão revogável, Secure/HttpOnly/SameSite e CSRF | testes auth/session/header | pendente |
| Admin → oferta por ID | IDOR, mass assignment, publicação indevida | autorização server-side por ação/recurso e ownership provider/manual | matriz ator × recurso × ação | parcial |
| Admin → mídia | polyglot, MIME forjado, path traversal, malware | magic bytes, re-encode, limites, nomes opacos e storage fora do código | fixtures de upload malicioso | pendente |
| Provider → adapter | SSRF, schema drift, lote inválido, remoção indevida | allowlist, timeout, validação, staging, last-known-good e transação | fixtures válidas/inválidas + outage | pendente |
| Job → banco/storage | concorrência, retry duplicado, limpeza excessiva | lock, idempotência, timeout, dry-run e quarentena | fault injection + job history | pendente |
| CI → release | segredo, dependência vulnerável, artefato adulterado | lockfiles, secret scan, SBOM, digest e gates | scan/SBOM/provenance | pendente |
| Runtime → logs | token/senha/PII, log injection | redaction, campos estruturados, retenção e controle de acesso | corpus redigido + scan | pendente |
| Runtime → backup | corrupção, cópia incompleta, exfiltração | checksum, criptografia, destino externo e restore | Disaster Recovery Drill | pendente |

## Requisitos de verificação

| ID | Requisito | Task consumidora | Critério de saída |
|---|---|---|---|
| SEC-01 | Toda decisão de autorização é server-side e falha fechada | EPIC-04.2, EPIC-04.4, EPIC-14.3 | ator sem permissão não lê nem altera recurso de outro escopo |
| SEC-02 | Objetos referenciados por ID têm controle contra BOLA/IDOR | EPIC-04.4, EPIC-14.3 | matriz negativa passa sem alteração de estado |
| SEC-03 | Entrada é validada por allowlist e tamanho antes do parser/SQL | EPIC-04.4 | payloads adversariais retornam erro seguro |
| SEC-04 | Sessão, CSRF, cookies e login têm ciclo de vida e limitação | EPIC-04.2, EPIC-04.3, EPIC-04.5 | testes de replay, CSRF, brute force e cookie malformado passam |
| SEC-05 | Upload aceita somente imagem decodificada e re-encodada | EPIC-01.2, EPIC-04.4 | executável, MIME forjado, SVG perigoso e polyglot são rejeitados |
| SEC-06 | Provider não pode apagar last-known-good por falha | EPIC-11.1–11.4 | lote inválido/outage mantém estado publicado |
| SEC-07 | Logs não contêm segredo, senha, token ou PII desnecessária | EPIC-05.4, EPIC-12.1 | redaction scan e amostra revisada passam |
| SEC-08 | Build/release é reproduzível e escaneado | EPIC-14.6, EPIC-21.1–21.4 | critical/high bloqueia ou tem exceção com expiração |
| SEC-09 | Banco e mídia podem ser restaurados | EPIC-16.1–16.4 | drill limpo recupera dados, mídia e smoke |
| SEC-10 | Debug e documentação interna não são públicos | EPIC-04.5, EPIC-08.3, EPIC-17.3 | crawl/headers não expõem endpoint ou stack trace |

## Riscos atuais e decisão

- **Crítico:** autenticação ainda usa senha de ambiente compartilhada; produção
  permanece bloqueada até identidade/RBAC, rate limit e ciclo de senha.
- **Crítico:** upload de mídia ainda é URL relativa; produção permanece
  bloqueada até pipeline binário seguro e storage persistente.
- **Alto:** não há backup/restore/DR comprovado; nenhuma perda de dados pode ser
  simulada fora de laboratório descartável.
- **Alto:** conteúdo jurídico e bases de tratamento não foram inventados;
  decisões empresariais/jurídicas ficam marcadas como
  `VALIDAÇÃO JURÍDICA NECESSÁRIA`.
- **Médio:** logs, métricas, headers e rate limiting ainda precisam de
  implementação e teste dinâmico.

Não há exceção aceita neste documento. Cada risco crítico precisa de owner,
mitigação, evidência e prazo antes da revisão final.

## Checklist de revisão

- [ ] Todos os ativos têm owner e classificação.
- [ ] Todos os fluxos administrativos têm matriz de autorização.
- [ ] Cada ameaça crítica aponta teste automatizado ou dinâmica local.
- [ ] Findings medium/low têm tratamento ou justificativa registrada.
- [ ] Exceções possuem expiração e não escondem bloqueio P0.
- [ ] EPIC-19.2 recebe os relatórios e não somente este documento.
