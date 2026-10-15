# Mapa de rotas e links

## URLs incluídas no sitemap

O `sitemap.xml` atual lista 19 URLs canônicas no domínio `https://viajandocomababi.com.br/`:

```text
/
pacotes.html
promo-voos.html
campanhas.html
sobre.html
como-funciona.html
servicos.html
consultoria-de-viagem.html
roteiro-personalizado.html
lua-de-mel.html
viagem-europa.html
viagem-em-familia.html
faq.html
privacidade.html
cookies.html
termos-de-uso.html
condicoes-comerciais.html
cancelamento-reembolso.html
contato-lgpd.html
```

`robots.txt` permite o site, bloqueia caminhos de imagens e `/novaspostagens/`, e aponta para esse sitemap. Os caminhos bloqueados não foram tratados como páginas públicas nesta auditoria.

## Relações entre documentos legais

As seis páginas legais usam o mesmo cabeçalho, rodapé, breadcrumb e navegação de documentos relacionados. Relações funcionais principais:

| Origem | Destino | Motivo |
|---|---|---|
| `condicoes-comerciais.html` | `cancelamento-reembolso.html` | encaminhar dúvidas pós-venda |
| `cancelamento-reembolso.html` | `condicoes-comerciais.html` | explicar o fluxo antes do pagamento |
| `cancelamento-reembolso.html` | `contato-lgpd.html` | separar pedido comercial de pedido de dados |
| `contato-lgpd.html` | `privacidade.html` | detalhar tratamento e direitos |
| `cookies.html` | `privacidade.html` | complementar tecnologias e dados |
| `privacidade.html` | `cookies.html` e `contato-lgpd.html` | consentimento e exercício de direitos |
| Todas as páginas | `index.html` | breadcrumb “Início” |

## Canais externos

O atendimento comercial e o formulário encaminham o visitante ao WhatsApp configurado no repositório. O e-mail `contato@viajandocomababi.com.br` aparece como canal textual nas páginas legais. Links externos usam `target="_blank"` com `rel="noopener noreferrer"` quando aplicável.

## Verificação

`tests/test_site_audit.py::test_internal_links_resolve_to_repository_files` percorre os HTML do root e confirma que links relativos para HTML, CSS, JavaScript, XML e imagens apontam para arquivos existentes. A verificação não afirma que serviços de terceiros estejam disponíveis.
