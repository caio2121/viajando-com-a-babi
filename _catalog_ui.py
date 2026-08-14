"""HTML compartilhado de filtros, ordenação e estados vazios do catálogo."""

CSS_VERSION = "28"
JS_VERSION = "25"
ANALYTICS_VERSION = "14"


def toolbar(kind: str, page_size: int = 24) -> str:
    labels = {
        "pacotes": ("Filtrar pacotes", "Mostrar mais pacotes", "pacote", "pacotes"),
        "voos": ("Filtrar voos", "Mostrar mais ofertas", "promoção", "promoções"),
        "campanhas": ("Filtrar campanhas", "Mostrar mais campanhas", "campanha", "campanhas"),
    }
    filter_label, more_label, one, many = labels[kind]
    sort_block = ""
    if kind != "campanhas":
        sort_price = """
            <option value="price">Preço</option>
            <option value="price-desc">Maior preço</option>"""
        sort_block = f"""
        <label class="catalog-bar__sort">
          <span>Ordenar por</span>
          <select data-catalog-sort>
            <option value="date">Data</option>
            {sort_price}
          </select>
        </label>"""
    inline_filters = ""
    if kind in ("voos", "campanhas"):
        dest_filter = """
      <label class="catalog-bar__field">
        <span>Destino</span>
        <select data-catalog-dest>
          <option value="">Todos os destinos</option>
        </select>
      </label>"""
        origin_filter = ""
        dest_type_filter = ""
        if kind == "voos":
            dest_type_filter = """
      <label class="catalog-bar__field">
        <span>Tipo de destino</span>
        <select data-catalog-dest-type>
          <option value="">Todos</option>
          <option value="nacional">Nacionais</option>
          <option value="internacional">Internacionais</option>
        </select>
      </label>"""
            origin_filter = """
      <label class="catalog-bar__field">
        <span>Origem</span>
        <select data-catalog-origin>
          <option value="">Todas as origens</option>
        </select>
      </label>"""
        price_filter = ""
        if kind == "voos":
            price_filter = """
      <label class="catalog-bar__field">
        <span>Saídas de</span>
        <input type="date" data-catalog-from>
      </label>
      <label class="catalog-bar__field">
        <span>Saídas até</span>
        <input type="date" data-catalog-to>
      </label>
      <label class="catalog-bar__field catalog-bar__field--price">
        <span>Preço máximo</span>
        <input type="range" data-catalog-price min="0" max="10000" value="10000">
        <output data-catalog-price-label></output>
      </label>"""
        inline_filters = f"""
    <form class="catalog-bar__filters" data-catalog-inline novalidate>
      {dest_type_filter}{origin_filter}{dest_filter}{price_filter}
      <button type="submit" class="btn btn--md">Pesquisar</button>
      <button type="button" class="btn btn--outline btn--md" data-catalog-clear hidden>Limpar filtros</button>
    </form>"""

    filter_btn = ""
    if kind == "pacotes":
        filter_btn = f"""
      <button type="button" class="btn btn--outline btn--md" data-catalog-open-filter>
        <i class="fas fa-sliders-h" aria-hidden="true"></i> {filter_label}
      </button>"""

    return f"""
    <div class="catalog-bar" data-catalog="{kind}" data-page-size="{page_size}">
      <div class="catalog-bar__row">
        {filter_btn}
        {sort_block}
        <p class="catalog-bar__count" data-catalog-count></p>
      </div>
      {inline_filters}
      <button type="button" class="catalog-bar__clear-inline" data-catalog-clear hidden>Limpar filtros</button>
    </div>
"""


def empty_state(kind: str) -> str:
    copy = {
        "pacotes": (
            "Nenhum pacote encontrado com esses filtros.",
            "Tente alterar o destino, as datas ou a faixa de preço.",
        ),
        "voos": (
            "Nenhuma promoção de voo encontrada com esses filtros.",
            "Tente ampliar as datas, aumentar o preço ou trocar o destino.",
        ),
        "campanhas": (
            "Nenhuma campanha encontrada com esses filtros.",
            "Tente outro destino ou limpe os filtros.",
        ),
    }
    title, hint = copy[kind]
    more = {
        "pacotes": "Mostrar mais pacotes",
        "voos": "Mostrar mais ofertas",
        "campanhas": "Mostrar mais campanhas",
    }[kind]
    return f"""
    <div class="catalog-empty" data-catalog-empty hidden>
      <p><strong>{title}</strong></p>
      <p>{hint}</p>
      <button type="button" class="btn btn--outline btn--md" data-catalog-clear>Limpar filtros</button>
    </div>
    <div class="catalog-more">
      <button type="button" class="btn btn--outline btn--md" data-catalog-more>{more}</button>
    </div>
"""


def filter_modal() -> str:
    return """
  <div class="modal-overlay catalog-filter-overlay" id="modalCatalogFilter" role="dialog" aria-modal="true" aria-labelledby="catalogFilterTitle" hidden>
    <div class="modal catalog-filter-modal">
      <button class="modal__close" type="button" data-catalog-close-filter aria-label="Fechar filtros">
        <i class="fas fa-times"></i>
      </button>
      <div class="modal__header">
        <i class="fas fa-sliders-h" aria-hidden="true"></i>
        <div>
          <h3 id="catalogFilterTitle">Filtrar pacotes</h3>
          <p>Refine por origem, destino, datas e preço.</p>
        </div>
      </div>
      <form class="catalog-filter-form" data-catalog-form novalidate>
        <label class="form__group">
          <span>Origem</span>
          <select name="origin" data-catalog-origin>
            <option value="">Todas</option>
          </select>
        </label>
        <label class="form__group">
          <span>Destino</span>
          <input type="search" name="destSearch" data-catalog-dest-search placeholder="Buscar destino" autocomplete="off">
          <select name="destination" data-catalog-dest>
            <option value="">Todos os destinos</option>
          </select>
        </label>
        <div class="form__row">
          <label class="form__group">
            <span>Saídas de</span>
            <input type="date" name="dateFrom" data-catalog-from>
          </label>
          <label class="form__group">
            <span>Saídas até</span>
            <input type="date" name="dateTo" data-catalog-to>
          </label>
        </div>
        <label class="form__group">
          <span>Tipo de pacote</span>
          <select name="tipo" data-catalog-tipo>
            <option value="">Todos</option>
            <option value="com-aereo">Com aéreo</option>
            <option value="sem-aereo">Sem aéreo</option>
            <option value="cruzeiro">Cruzeiro</option>
          </select>
        </label>
        <label class="form__group">
          <span>Preço máximo</span>
          <input type="range" name="priceMax" data-catalog-price min="0" max="10000" value="10000">
          <output data-catalog-price-label></output>
        </label>
        <div class="catalog-filter-actions">
          <button type="button" class="btn btn--outline btn--md" data-catalog-clear>Limpar filtros</button>
          <button type="submit" class="btn btn--md">Aplicar filtros</button>
        </div>
      </form>
    </div>
  </div>
"""
