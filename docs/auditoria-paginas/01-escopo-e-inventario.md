# Escopo e inventário

## Método

Foi feita uma leitura do repositório e dos artefatos de publicação, seguida de inspeção das rotas listadas no sitemap, dos links internos, dos partials compartilhados e dos fluxos de consentimento e formulário. O inventário abaixo é um retrato do estado local em 14/10/2026; não é uma garantia de disponibilidade em produção.

## Inventário de HTML no root

O root contém 20 arquivos `.html`: 19 páginas/artefatos de publicação e o arquivo de verificação do Google Search Console.

| Grupo | Arquivos |
|---|---|
| Entrada e catálogo | `index.html`, `pacotes.html`, `promo-voos.html`, `campanhas.html` |
| Institucional e serviço | `sobre.html`, `como-funciona.html`, `servicos.html`, `consultoria-de-viagem.html`, `roteiro-personalizado.html` |
| Conteúdo de destino | `lua-de-mel.html`, `viagem-europa.html`, `viagem-em-familia.html`, `faq.html` |
| Documentos legais | `privacidade.html`, `cookies.html`, `termos-de-uso.html`, `condicoes-comerciais.html`, `cancelamento-reembolso.html`, `contato-lgpd.html` |
| Verificação | `google194769ee1567755b.html` |

Também existem templates e artefatos HTML em subdiretórios de marketing, materiais de evento, dados gerados e administração. Eles não foram tratados como rotas públicas do sitemap nesta etapa.

## Artefatos operacionais observados

- `style.css`: estilos globais, responsividade, foco e componentes legais.
- `script.js`: navegação, catálogo, modais e composição do contato.
- `_partials/hub-header.html` e `_partials/hub-footer.html`: navegação e rodapé reutilizados.
- `_partials/head-assets.html`: assets compartilhados.
- `_partials/ga4.html`: consentimento e carregamento condicional das tags.
- `_partials/cookie-banner.html`: interface inicial de escolha.
- `_build_legal_pages.py`: fonte de geração dos seis documentos legais.
- `tests/test_site_audit.py`: contratos automatizados da auditoria.
- `sitemap.xml` e `robots.txt`: descoberta e regras de rastreamento.

## Limites do inventário

O servidor estático local não implementa a API dinâmica de ofertas observada pelo front-end; por isso, a solicitação `/api/offers?...` retorna o 404 esperado nesse modo. A arquitetura local com Compose está documentada no `README.md` e não foi alterada nesta auditoria.
