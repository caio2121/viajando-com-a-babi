"""Regenera pacotes.html a partir dos cards em index.html. Executar após alterar pacotes na home."""
from pathlib import Path

root = Path(__file__).parent
index = (root / "index.html").read_text(encoding="utf-8")

start = index.find('<div class="pacotes__category" id="pacotes-completos">')
cta_start = index.find('<div class="pacotes__cta-extra">')
cta_end = index.find("</div>", cta_start) + len("</div>")

blocks = index[start:cta_start]
cta_block = index[cta_start:cta_end]

head_end = (root / "pacotes.html").read_text(encoding="utf-8").split("<main")[0]
head_end = head_end.replace("style.css?v=15", "style.css?v=16")

main = f"""  <section class="pacotes pacotes-page">
    <div class="container pacotes-page__header">
      <nav class="breadcrumb breadcrumb--light" aria-label="Navegação"><a href="/">Início</a> / Pacotes de viagem</nav>
      <span class="label label--center">Catálogo completo</span>
      <h1 class="section-title">Pacotes de viagem</h1>
      <p class="section-sub">Pacotes com aéreo, hospedagem e serviços principais — além de cruzeiros e roteiros em grupo. Quer algo sob medida? <a href="roteiro-personalizado.html">Monte um roteiro personalizado</a>.</p>
    </div>
    <div class="container">
{blocks}{cta_block}

    </div>
  </section>
"""

tail = (root / "pacotes.html").read_text(encoding="utf-8").split("</section>", 1)[1]
tail = "</section>" + tail.split("<footer", 1)[1]
tail = "\n\n  <footer" + tail.split("<footer", 1)[1] if "<footer" in tail else ""

# Read tail from template file footer onwards
template_tail = """
  <footer class="footer" id="contato">
    <div class="container">
      <div class="footer__grid">
        <div class="footer__brand">
          <img src="assets/logo-vcb.png" alt="Viajando com a Babi" class="footer__logo" />
          <p>Pacotes e roteiros personalizados — do planejamento ao embarque.</p>
        </div>
        <div class="footer__links">
          <h4>Navegação</h4>
          <ul>
            <li><a href="/">Início</a></li>
            <li><a href="sobre.html">Sobre a Babi</a></li>
            <li><a href="pacotes.html">Pacotes de viagem</a></li>
            <li><a href="servicos.html">Serviços</a></li>
            <li><a href="faq.html">FAQ</a></li>
            <li><a href="privacidade.html">Privacidade</a></li>
          </ul>
        </div>
        <div class="footer__contato">
          <h4>Fale comigo</h4>
          <a href="https://wa.me/5521920064617" target="_blank" rel="noopener noreferrer" class="footer__social-link footer__social-link--wa"><i class="fab fa-whatsapp"></i><span>+55 21 92006-4617</span></a>
          <a href="mailto:viajandocomababi@gmail.com" class="footer__social-link footer__social-link--email"><i class="fas fa-envelope"></i><span>viajandocomababi@gmail.com</span></a>
        </div>
      </div>
      <div class="footer__bottom">
        <p>&copy; <span id="year"></span> Viajando com a Babi — CNPJ 60.536.280/0001-89</p>
      </div>
    </div>
  </footer>

  <div class="lightbox-overlay" id="lightbox" role="dialog" aria-modal="true" aria-label="Visualizar imagem">
    <button class="lightbox__close" id="lightboxClose" aria-label="Fechar imagem">&#x2715;</button>
    <img class="lightbox__img" id="lightboxImg" src="" alt="" />
  </div>

  <a href="https://wa.me/5521920064617?text=Ol%C3%A1%20Babi!%20Vim%20pelo%20site%20e%20quero%20saber%20mais%20sobre%20os%20pacotes%20de%20viagem"
     target="_blank" rel="noopener noreferrer"
     class="fab-whatsapp" aria-label="Falar no WhatsApp">
    <i class="fab fa-whatsapp"></i>
    <span class="fab-whatsapp__tooltip">Falar no WhatsApp</span>
  </a>

  <script src="analytics.js?v=3"></script>
  <script src="script.js?v=16"></script>
</body>
</html>
"""

(root / "pacotes.html").write_text(
    head_end + '<main id="conteudo-principal">\n' + main + template_tail,
    encoding="utf-8",
)
print("pacotes.html atualizado")
