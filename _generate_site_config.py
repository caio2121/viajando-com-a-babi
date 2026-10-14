from _site_config import ROOT, load_public_config, public_js


(ROOT / "site-config.js").write_text(public_js(load_public_config()), encoding="utf-8")
print("site-config.js atualizado")
