"""Separa catálogo completo (fonte) da vitrine da home (8 destaques). Executar uma vez ou após mudança estrutural."""
import re
from pathlib import Path

root = Path(__file__).parent
index_path = root / "index.html"
text = index_path.read_text(encoding="utf-8")

start_marker = "<!-- PACOTES_CATALOGO_INICIO -->"
end_marker = "<!-- PACOTES_CATALOGO_FIM -->"

if start_marker in text:
    print("Catálogo já reestruturado; pulando.")
    raise SystemExit(0)

catalog_start = text.find('<div class="pacotes__category" id="pacotes-completos">')
cta_start = text.find('<div class="pacotes__cta-extra">')
cta_end = text.find("</div>", cta_start) + len("</div>")

full_catalog = text[catalog_start:cta_end]

HOME_FEATURED = {
    "completo": [
        "pacote-aracaju",
        "pacote-fortaleza",
        "pacote-maceio",
        "pacote-natal-luz-gramado",
        "pacote-buenos-aires-essencial",
        "pacote-cancun-oasis-palm",
    ],
    "sem-aereo": ["pacote-navio-daniel-2027"],
    "grupo-guia": ["pacote-chapada-salvador"],
}

article_pattern = re.compile(
    r'<article class="card reveal" id="([^"]+)"[^>]*>.*?</article>',
    re.DOTALL,
)

articles = {m.group(1): m.group(0) for m in article_pattern.finditer(full_catalog)}

CATEGORY_META = {
    "completo": {
        "id": "pacotes-completos",
        "icon": "fa-plane-departure",
        "title": "Pacote completo",
        "desc": "Aéreo, hospedagem e serviços principais inclusos.",
    },
    "sem-aereo": {
        "id": "pacotes-sem-aereo",
        "icon": "fa-ship",
        "title": "Cruzeiros",
        "desc": "Cruzeiros com embarque nacional.",
        "extra_id": ' id="cruzeiros"',
    },
    "grupo-guia": {
        "id": "pacotes-grupos-guia",
        "icon": "fa-user-friends",
        "title": "Grupos com Guia",
        "desc": "Roteiros em grupo com guia.",
    },
}


def build_category(cat_key: str) -> str:
    meta = CATEGORY_META[cat_key]
    ids = HOME_FEATURED[cat_key]
    cards = "\n\n        ".join(articles[i] for i in ids if i in articles)
    extra_id = meta.get("extra_id", "")
    return f"""      <div class="pacotes__category" id="{meta["id"]}">
        <h3 class="pacotes__subhead"{extra_id}><i class="fas {meta["icon"]}" aria-hidden="true"></i> {meta["title"]}</h3>
        <p class="pacotes__category-desc">{meta["desc"]}</p>
        <div class="pacotes__grid">

        {cards}

        </div>
      </div>"""


home_categories = "\n\n".join(build_category(k) for k in HOME_FEATURED)

home_section = f"""  <section id="pacotes" class="pacotes">
    <div class="container">
      <span class="label label--center">Pacotes disponíveis</span>
      <h2 class="section-title">Pacotes de viagem: destinos que vão te apaixonar</h2>
      <p class="section-sub">Destaques do catálogo com aéreo, hospedagem e serviços principais. <a href="pacotes.html">Ver catálogo completo de pacotes</a> ({len(articles)} opções).</p>

{home_categories}

      <div class="pacotes__cta-extra">
        <p>Não encontrou o destino que procura?</p>
        <a href="pacotes.html" class="btn btn--whatsapp btn--md">
          <i class="fab fa-whatsapp"></i> Ver todos os pacotes
        </a>
        <a href="https://wa.me/5521920064617?text=Ol%C3%A1%20Babi!%20Vim%20pelo%20site%20e%20quero%20montar%20um%20roteiro%20personalizado"
           target="_blank" rel="noopener noreferrer"
           class="btn btn--outline btn--md" style="margin-left:8px">
          <i class="fab fa-whatsapp"></i> Montar roteiro personalizado
        </a>
      </div>
    </div>
  </section>"""

catalog_source = f"""
{start_marker}
<div id="pacotes-catalog-source" hidden aria-hidden="true">
{full_catalog}
</div>
{end_marker}
"""

section_start = text.find('<section id="pacotes" class="pacotes">')
section_end = text.find("</section>", section_start) + len("</section>")

scripts_pos = text.rfind('<script src="script.js')
new_text = text[:section_start] + home_section + text[section_end:scripts_pos] + catalog_source + "\n\n" + text[scripts_pos:]

index_path.write_text(new_text, encoding="utf-8")
print(f"Home: {sum(len(v) for v in HOME_FEATURED.values())} cards | Catálogo fonte: {len(articles)} cards")
