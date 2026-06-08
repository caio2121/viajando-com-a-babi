# Analytics de pacotes — Viajando com a Babi

Guia para ler no GA4 quais pacotes e categorias geram mais interesse.

> **Manutenção:** regras do repositório em `.cursor/rules/` (`analytics-ga4.mdc`, `pacotes-catalogo.mdc`, `site-estatico.mdc`).

## Eventos por etapa do interesse

| Etapa | Evento | O que mede |
|-------|--------|------------|
| Viu o card na tela | `view_item` + `package_impression` | Impressão do pacote (1x por visita) |
| Viu a categoria | `package_category_view` | Grupos com guia / Pacote completo / Cruzeiros |
| Clicou no card ou imagem | `select_item` + `destination_interest` | Exploração ativa |
| Clicou "Quero esse pacote!" | `service_click` + `generate_lead` + `package_lead` | Intenção comercial por destino |
| Abriu formulário | `form_start` | Interesse em roteiro personalizado |
| Enviou formulário | `form_submit` + `generate_lead` | Lead qualificado (sem PII) |

## Parâmetros principais (criar dimensões customizadas no GA4)

| Parâmetro | Uso |
|-----------|-----|
| `package_name` | Nome legível do pacote |
| `package_slug` | ID estável para relatórios (ex: `aracaju_imperdivel`) |
| `package_category` | `grupos_com_guia`, `pacote_completo`, `cruzeiro` |
| `package_region` | `brasil_nordeste`, `argentina`, `caribe`, `cruzeiro`, etc. |
| `interaction_type` | `viewport`, `card_explore`, `image_click`, `whatsapp_cta` |
| `interest_level` | `high` (lead direto) ou `medium` |

## Como configurar no GA4 (Admin)

1. **Admin → Definições de dados → Parâmetros personalizados**
2. Criar parâmetros de evento (escopo Evento):
   - `package_name`
   - `package_slug`
   - `package_category`
   - `package_region`
3. **Admin → Eventos → Modificar eventos** (opcional): renomear `package_lead` para aparecer em relatórios de conversão secundária.

## Relatórios recomendados

### Pacotes mais vistos
- **Explorar → Eventos** → evento `view_item`
- Dimensão secundária: `package_name` ou `package_slug`
- Métrica: contagem de eventos

### Pacotes com mais cliques (interesse ativo)
- Evento `select_item` ou `destination_interest`
- Comparar com `view_item` para taxa de interesse = cliques / impressões

### Pacotes que mais geram lead
- Evento `package_lead` ou `generate_lead` onde `package_slug` não é `(not set)`
- Ordenar por `package_name`

### Regiões mais buscadas
- Evento `destination_interest`
- Dimensão: `package_region`

### Categorias mais populares
- Evento `package_category_view`
- Dimensão: `category_name`

### Funil formulário personalizado
1. `form_start` (abriu modal)
2. `form_submit` (enviou)
3. Taxa = submit / start

## Regiões inferidas automaticamente

O site classifica destinos sem editar cada card:

| Região | Exemplos |
|--------|----------|
| `brasil_nordeste` | Aracaju, Fortaleza, Bahia, João Pessoa… |
| `brasil_sul` | Gramado, Bonito |
| `argentina` | Buenos Aires, Bariloche, Ushuaia |
| `chile` | Santiago, Atacama |
| `peru` | Vale Sagrado |
| `caribe` | Cancún, Bahamas, San Andrés |
| `cruzeiro` | MSC Divina, Costa Serena |

Para forçar região em um pacote novo, adicione no HTML: `data-regiao="caribe"` no `<article class="card">`.

## Privacidade

Nenhum evento envia dados digitados no formulário (destino, datas, orçamento, etc.).
