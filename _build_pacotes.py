"""Regenera pacotes.html a partir dos cards em index.html. Executar após alterar pacotes na home."""
from pathlib import Path

root = Path(__file__).parent
index = (root / "index.html").read_text(encoding="utf-8")

start = index.find('<div class="pacotes__category" id="pacotes-completos">')
cta_start = index.find('<div class="pacotes__cta-extra">')
cta_end = index.find("</div>", cta_start) + len("</div>")

blocks = index[start:cta_start]
cta_block = index[cta_start:cta_end]

head_assets = (root / "_partials/head-assets.html").read_text(encoding="utf-8")
ga4 = (root / "_partials/ga4.html").read_text(encoding="utf-8")
hub_header = (root / "_partials/hub-header.html").read_text(encoding="utf-8")

head = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Pacotes de viagem | Viajando com a Babi</title>
  <meta name="description" content="Catálogo de pacotes de viagem com aéreo e hospedagem: Nordeste, Gramado, América do Sul, Caribe e cruzeiros. Agência Cadastur. Fale com a Babi." />
  <link rel="canonical" href="https://viajandocomababi.com.br/pacotes.html" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://viajandocomababi.com.br/pacotes.html" />
  <meta property="og:title" content="Pacotes de viagem | Viajando com a Babi" />
  <meta property="og:description" content="Pacotes de viagem com aéreo e hospedagem para destinos nacionais e internacionais." />
  <meta property="og:image" content="https://viajandocomababi.com.br/assets/og-share.jpeg" />
  <meta property="og:locale" content="pt_BR" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="icon" type="image/png" href="assets/logo-vcb.png" />
{head_assets}  <link rel="stylesheet" href="style.css?v=20" />
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@graph": [
      {{ "@type": "WebPage", "@id": "https://viajandocomababi.com.br/pacotes.html#webpage", "url": "https://viajandocomababi.com.br/pacotes.html", "name": "Pacotes de viagem | Viajando com a Babi", "isPartOf": {{ "@id": "https://viajandocomababi.com.br/#website" }} }},
      {{ "@type": "BreadcrumbList", "itemListElement": [
        {{ "@type": "ListItem", "position": 1, "name": "Início", "item": "https://viajandocomababi.com.br/" }},
        {{ "@type": "ListItem", "position": 2, "name": "Pacotes de viagem", "item": "https://viajandocomababi.com.br/pacotes.html" }}
      ]}}
    ]
  }}
  </script>
{ga4}</head>
<body>
"""

main = f"""<main id="conteudo-principal">
  <section id="pacotes" class="pacotes pacotes-page">
    <div class="container pacotes-page__header">
      <nav class="breadcrumb breadcrumb--light" aria-label="Navegação"><a href="/">Início</a> / Pacotes de viagem</nav>
      <span class="label label--center">Catálogo completo</span>
      <h1 class="section-title">Pacotes de viagem</h1>
      <p class="section-sub">Pacotes com aéreo, hospedagem e serviços principais, além de cruzeiros e roteiros em grupo. Quer algo sob medida? <a href="roteiro-personalizado.html">Monte um roteiro personalizado</a>.</p>
    </div>
    <div class="container">
{blocks}{cta_block}

    </div>
  </section>
</main>
"""

hub_footer = (root / "_partials/hub-footer.html").read_text(encoding="utf-8")
lightbox = """
  <div class="lightbox-overlay" id="lightbox" role="dialog" aria-modal="true" aria-label="Visualizar imagem">
    <button class="lightbox__close" id="lightboxClose" aria-label="Fechar imagem">&#x2715;</button>
    <img class="lightbox__img" id="lightboxImg" src="" alt="" />
  </div>

"""
template_tail = hub_footer.replace(
    '  <script src="script.js?v=20"></script>',
    lightbox + '  <script src="analytics.js?v=6"></script>\n  <script src="script.js?v=20"></script>',
)

(root / "pacotes.html").write_text(head + hub_header + main + template_tail, encoding="utf-8")
print("pacotes.html atualizado")
