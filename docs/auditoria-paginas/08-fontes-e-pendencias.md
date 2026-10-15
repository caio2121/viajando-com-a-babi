# Fontes, evidências e pendências

## Fontes oficiais consultadas

As referências abaixo foram usadas para orientar a redação e os checks; não constituem parecer jurídico:

| Tema | Fonte |
|---|---|
| LGPD | [Lei nº 13.709/2018 — Planalto](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm) |
| Direitos do titular | [ANPD — Titular de dados](https://www.gov.br/anpd/pt-br/assuntos/titular-de-dados) |
| Defesa do consumidor | [Código de Defesa do Consumidor — Planalto](https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm) |
| Comércio eletrônico | [Decreto nº 7.962/2013 — Planalto](https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/decreto/d7962.htm) |
| Turismo | [Lei nº 11.771/2008 — Planalto](https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11771.htm) |
| Cadastro de prestadores | [Cadastur — Ministério do Turismo](https://www.gov.br/turismo/pt-br/assuntos/cadastur) |
| Acessibilidade | [WCAG 2.2 — W3C](https://www.w3.org/TR/WCAG22/) |
| Consentimento Google | [Consent mode — Google](https://developers.google.com/tag-platform/security/guides/consent) |

## Evidências do repositório

- Configuração pública: `config/site-config.json` e `_site_config.py`.
- Fonte das páginas: `_build_legal_pages.py`.
- Consentimento: `_partials/ga4.html` e `_partials/cookie-banner.html`.
- Formulário: `index.html` e `script.js`.
- Apresentação: `style.css`, `_partials/hub-header.html` e `_partials/hub-footer.html`.
- Descoberta: `sitemap.xml` e `robots.txt`.
- Checks: `tests/test_site_audit.py`.

## Pendências comerciais e jurídicas

1. Validar os seis textos com profissional habilitado e aprovar a versão pública.
2. Confirmar razão social, CNPJ, endereço/canal institucional e eventual registro aplicável antes de afirmar esses dados em documentos.
3. Definir responsável formal por privacidade/encarregado, canal oficial e procedimento de atendimento de titulares.
4. Criar matriz de retenção por finalidade e canal, com rotina de eliminação, bloqueio ou anonimização.
5. Documentar fornecedores que recebem dados e respectivas bases, transferências e contratos.
6. Confirmar, por produto, regras de alteração, cancelamento, multa, reembolso, prazo e forma de pagamento; publicar somente o que for aprovado na oferta/contrato.
7. Confirmar configuração, retenção e classificação de analytics/publicidade no Google e no painel de consentimento.
8. Definir responsável e periodicidade para atualizar textos, ofertas, sitemap e evidências.
