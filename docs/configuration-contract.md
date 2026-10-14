# Contrato de configuração

## Objetivo e limites

Este é o inventário inicial para separar valores públicos, comportamento e
segredos. Ele não implementa multi-tenant e não autoriza inserir valores reais
da empresa. A configuração inválida deve falhar de forma segura no boot futuro,
sem imprimir segredo ou stack trace para o cliente.

## Precedência proposta

```text
defaults seguros
  < arquivo/env do ambiente
  < secret store do ambiente (somente segredos)
  < configuração aprovada da instalação
```

O cliente/browser recebe somente valores explicitamente públicos. `SESSION_SECRET`,
`ADMIN_PASSWORD`, chaves privadas e credenciais de provider nunca podem ser
renderizados em HTML, JavaScript público, logs ou endpoint de configuração.

## Inventário

| Chave/conceito | Fonte atual | Tipo | Público? | Validação |
|---|---|---|---|---|
| `APP_HOST`/`APP_PORT` | compose/env/backend | runtime | não | host/porta válidos |
| `DATABASE_PATH` | compose/env/backend | runtime | não | path permitido no volume |
| `ADMIN_PASSWORD` | `.env`/compose/backend | secret | não | obrigatório, força mínima futura |
| `SESSION_SECRET` | `.env`/compose/backend | secret | não | obrigatório, entropia mínima futura |
| `WHATSAPP_NUMBER` | env + HTML/JS atuais | contato público | sim | dígitos E.164/normalização |
| `COOKIE_SECURE` | env/compose | segurança | não | `0` somente local; `1` com HTTPS |
| `LOG_LEVEL` | env/compose | observabilidade | não | allowlist DEBUG/INFO/WARN/ERROR |
| nome/logo/domínio | HTML/assets/CNAME | marca pública | sim | URL/path/asset existente |
| GA4 ID | partials/HTML | tracker público | sim, após consentimento | formato G- + allowlist |
| Google Ads ID/conversão | partials/HTML | tracker público | sim, após consentimento | formato/allowlist |
| provider/endpoint | scripts/env | integração | endpoint pode ser público; credencial não | HTTPS/host allowlist/timeout |
| limites body/media/query | código atual | segurança | não | inteiro positivo e teto seguro |
| storage de mídia | volume/config futura | operação | não | path fora da imagem e permissão |
| políticas legais | páginas/config futura | conteúdo | público após revisão | owner, versão e aprovação |

## Problemas atuais rastreados

- os arquivos estáticos antigos continuam contendo o bundle já publicado, mas
  a fonte de build agora é centralizada;
- o `.env.example` é local e contém placeholders; valores públicos ficam em
  `config/site-config.json` com schema validado;
- o provider e a origem externa são lidos pela mesma fonte pública, sem
  transportar credencial para o bundle;
- limites e flags de produção ainda não possuem matriz dev/test/staging/prod;
- dados legais e de white-label não devem ser inferidos nem preenchidos nesta
  task.

## Contrato de validação futura

1. Boot valida chaves obrigatórias e tipos antes de abrir tráfego.
2. Config ausente/inválida retorna erro operacional genérico e diagnóstico
   redigido somente em log autorizado.
3. Secret scan verifica que nenhum valor secreto aparece no repositório,
   imagem, artefato ou resposta pública.
4. Cada ambiente tem arquivo/matriz própria; staging nunca reutiliza volume ou
   segredo de produção.
5. Alterar uma chave pública gera smoke de todas as superfícies consumidoras.
6. Alterar tracker respeita consentimento e não ativa coleta por acidente.
7. Valores legais faltantes mantêm gate em FAIL com
   `VALIDAÇÃO JURÍDICA NECESSÁRIA`.

## Evidências exigidas

- schema de configuração versionado;
- matriz de ambientes sanitizada;
- smoke com configuração de teste;
- render público sem secrets;
- boot failure test para chave inválida/ausente;
- secret scan e logs redigidos.

## Fonte pública implementada

`config/site-config.json` é a fonte versionada dos valores públicos de marca,
domínio, contato, WhatsApp, redes sociais, trackers, logo e endpoint do
provider. `_site_config.py` valida o schema e renderiza os partials; o comando
`python _generate_site_config.py` atualiza `site-config.js` sem transportar
segredos para o browser. Os scripts de build usam a mesma fonte.

IDs de analytics/Ads ausentes devem resultar em trackers desativados; eles não
são credenciais. Segredos continuam exclusivamente em ambiente/backend.
