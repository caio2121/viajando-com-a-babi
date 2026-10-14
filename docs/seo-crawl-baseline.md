# Baseline de rastreamento SEO

## Escopo e data

Baseline local coletado em 2026-09-28 antes de novas alterações dinâmicas. O
recorte cobre os 16 arquivos HTML na raiz do repositório. O arquivo de
verificação do Google não é página editorial e deve permanecer fora do conjunto
indexável.

## Resultado factual

| Métrica | Resultado |
|---|---:|
| HTMLs encontrados | 16 |
| HTMLs com `<title>` | 15 |
| HTMLs com meta description | 14 |
| HTMLs com canonical | 14 |
| Páginas editoriais com um `<h1>` | 15 |
| Arquivo de verificação sem metadata editorial | `google194769ee1567755b.html` |

Arquivos que precisam de decisão explícita:

- `404.html`: possui title/description/canonical ausentes no baseline; decidir
  se deve ter metadata mínima ou permanecer não indexável.
- `google194769ee1567755b.html`: token de verificação; não adicionar conteúdo
  editorial nem incluir no sitemap.

## Inventário de URLs

Páginas HTML observadas:

```text
/
/campanhas.html
/como-funciona.html
/consultoria-de-viagem.html
/faq.html
/pacotes.html
/privacidade.html
/promo-voos.html
/roteiro-personalizado.html
/servicos.html
/sobre.html
/viagem-em-familia.html
/viagem-europa.html
/lua-de-mel.html
/404.html
/google194769ee1567755b.html
```

O sitemap, robots, canonical e redirects precisam ser comparados com esta lista
em uma execução de crawler HTTP. A lista não autoriza remover ou renomear URL
existente.

## Contratos a preservar

1. URLs já indexadas mantêm caminho ou recebem redirect explícito.
2. `admin/`, rascunhos, previews e APIs não entram no índice.
3. Cada página indexável tem title, description, canonical, um h1 e headings em
   ordem coerente.
4. JSON-LD só declara entidades/ofertas cujos dados existem e estão válidos.
5. Sitemap lista somente URLs canônicas que retornam 200.
6. 404 retorna status 404 e oferece navegação útil sem ser indexada como página
   editorial.
7. Imagens têm alt e metadata coerente com direitos/estado de mídia.

## Evidências e próximos checks

- Baseline de titles/descriptions/canonical/h1 foi executado por script Python
  local e o resultado está registrado acima.
- `docs/seo-baseline.md` contém metas de Search Console, schema e performance.
- Próxima validação deve executar crawler HTTP local, parser de sitemap/robots,
  link checker, redirects/404 e schema validator.
- A migração dinâmica deve gerar URL map e comparar este baseline antes de
  qualquer promoção.

## Riscos ainda abertos

- metadata de ofertas dinâmicas, slug e structured data;
- removals/redirects de pacotes e campanhas;
- validação externa no Search Console/Rich Results;
- performance e imagens responsivas;
- conteúdo jurídico, que depende de revisão profissional.
