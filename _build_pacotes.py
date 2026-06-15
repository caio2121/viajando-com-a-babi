"""Regenera pacotes.html a partir dos cards em index.html. Executar após alterar pacotes na home."""
from pathlib import Path

root = Path(__file__).parent
index = (root / "index.html").read_text(encoding="utf-8")

start = index.find('<div class="pacotes__category" id="pacotes-completos">')
cta_start = index.find('<div class="pacotes__cta-extra">')
cta_end = index.find("</div>", cta_start) + len("</div>")

blocks = index[start:cta_start]
cta_block = index[cta_start:cta_end]

head_before = (root / "pacotes.html").read_text(encoding="utf-8").split("<header class=\"navbar\"")[0]
head_before = head_before.replace("style.css?v=15", "style.css?v=17").replace("style.css?v=16", "style.css?v=17")
ga4 = (root / "_partials/ga4.html").read_text(encoding="utf-8")
if "G-WGDNTSY8WM" not in head_before:
    head_before = head_before.replace("</head>", ga4 + "</head>")
hub_header = (root / "_partials/hub-header.html").read_text(encoding="utf-8")
head_end = head_before + hub_header

main = f"""  <section id="pacotes" class="pacotes pacotes-page">
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
"""

tail = (root / "pacotes.html").read_text(encoding="utf-8").split("</section>", 1)[1]
tail = "</section>" + tail.split("<footer", 1)[1]
tail = "\n\n  <footer" + tail.split("<footer", 1)[1] if "<footer" in tail else ""

hub_footer = (root / "_partials/hub-footer.html").read_text(encoding="utf-8")
lightbox = """
  <div class="lightbox-overlay" id="lightbox" role="dialog" aria-modal="true" aria-label="Visualizar imagem">
    <button class="lightbox__close" id="lightboxClose" aria-label="Fechar imagem">&#x2715;</button>
    <img class="lightbox__img" id="lightboxImg" src="" alt="" />
  </div>

"""
template_tail = hub_footer.replace(
    "  <script src=\"script.js?v=17\"></script>",
    lightbox + "  <script src=\"analytics.js?v=4\"></script>\n  <script src=\"script.js?v=17\"></script>",
)

(root / "pacotes.html").write_text(
    head_end + '<main id="conteudo-principal">\n' + main + template_tail,
    encoding="utf-8",
)
print("pacotes.html atualizado")
