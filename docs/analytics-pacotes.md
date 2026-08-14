# Analytics de pacotes — Viajando com a Babi

Guia para ler no GA4 quais pacotes e categorias geram mais interesse.

> **Manutenção:** regras do repositório em `.cursor/rules/` (`analytics-ga4.mdc`, `pacotes-catalogo.mdc`, `site-estatico.mdc`).

## Eventos por etapa do interesse

| Etapa | Evento | O que mede |
|-------|--------|------------|
| Viu o card na tela | `view_item` + `package_impression` | Impressão do pacote (1x por visita) |
| Viu a categoria | `package_category_view` | Grupos com guia / Pacote completo / Cruzeiros |
| Clicou no card ou imagem | `select_item` + `destination_interest` | Exploração ativa |
| Clicou "Tenho interesse" na opção do destino | `purchase` + `package_lead` + Ads `conversion` | Mesma intenção alta, a partir do modal de opções |
| Clicou WhatsApp genérico (FAB, navbar, hero, footer) | `generate_lead` | Engajamento GA4 **sem** conversão Ads |
| Abriu formulário | `form_start` | Interesse em roteiro personalizado |
| Enviou formulário | `form_submit` + `generate_lead` + Ads `conversion` | Lead qualificado (sem PII) + conversão Ads |
| Filtrou/ordenou catálogo | `filter_packages_*`, `sort_packages`, `sort_flights` | Uso de filtros (sem texto digitado) |
| WhatsApp de voo/campanha | `flight_whatsapp_click` / `campaign_whatsapp_click` | Lead de oferta compacta |
| Contato real (mensagem chegou) | `working_lead` (planilha) | Conversão confiável; ver [`funil-offline.md`](funil-offline.md) |
| Clicou CTA interno (catálogo, FAQ, serviços) | `cta_click` | Exploração sem contato direto |

## Google Ads "Contato" (`gtag_report_conversion`)

Dispara **apenas** em:

1. Botão **Quero esse pacote!** no card (`.card__footer .btn--whatsapp`) ou **Tenho interesse** no modal de opções (`.dest-option__cta`)
2. Envio do formulário de roteiro personalizado (`script.js`)

Não dispara em FAB, navbar, hero ou footer. Meta principal no Ads: `working_lead` (planilha). **Contato** (tag): secundária / intenção alta.

### Conversões otimizadas (alerta do Ads)

A tag usa o snippet in-page recomendado pelo Google:

- `allow_enhanced_conversions: true` no `gtag('config', AW-...)`
- `gtag('set', 'user_data', ...)` antes do evento `conversion`
- `transport_type: 'beacon'` para não perder o clique ao abrir o WhatsApp
- Só dispara com cookies de publicidade aceitos (`ad_storage` granted)
- `transaction_id` único por clique (pacote ou formulário)

Sem e-mail/telefone no formulário: não enviamos PII ao Ads; o alerta de cobertura pode persistir até o Ads reavaliar (48–72 h).

## Parâmetros principais (criar dimensões customizadas no GA4)

| Parâmetro | Uso |
|-----------|-----|
| `package_name` | Nome legível do pacote |
| `package_slug` | ID estável para relatórios (ex: `aracaju_imperdivel`) |
| `package_category` | `grupos_com_guia`, `pacote_completo`, `cruzeiro` |
| `package_region` | `brasil_nordeste`, `argentina`, `caribe`, `mexico`, `oriente`, `eua`, `uruguai`, `cruzeiro`, etc. |
| `interaction_type` | `viewport`, `card_explore`, `image_click`, `whatsapp_cta` |
| `interest_level` | `high` (lead direto) ou `medium` |
| `purchase_type` | `whatsapp_intent` (tentativa via botão do pacote) |
| `value` / `price` | Valor estimado do pacote em BRL (parseado do card) |

## Funil e-commerce no relatório de itens

| Coluna GA4 | Evento |
|------------|--------|
| Itens vistos | `view_item` |
| Itens comprados | `purchase` (clique em "Quero esse pacote!") |
| Receita do item | `purchase.value` (estimado, "a partir de") |

**Nota:** `purchase` no site = intenção comercial, não pagamento confirmado. Vendas fechadas: `close_convert_lead` via [`funil-offline.md`](funil-offline.md).

## Valor do pacote no `purchase`

Ordem de leitura em `analytics.js`:

1. `data-valor-total="2712"` no card (recomendado para cruzeiros sem total fixo)
2. Texto `.card__total` — ex.: "Total a partir de R$ 2.712"
3. `.card__parcela strong` × 12
4. `0` se não houver valor parseável

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

### Pacotes com tentativa de compra
- Evento `purchase` com `purchase_type = whatsapp_intent`
- Relatório **Monetização → Desempenho do item** → coluna **Itens comprados**
- Comparar com **Itens vistos** para taxa de conversão por pacote

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
| `brasil_nordeste` | Aracaju, Fortaleza, Bahia, João Pessoa, Porto de Galinhas… |
| `brasil_sul` | Gramado, Bonito |
| `brasil_centro` | Rio Quente, Caldas Novas |
| `argentina` | Buenos Aires, Bariloche, Ushuaia |
| `chile` | Santiago, Atacama |
| `peru` | Essências do Peru, Vale Sagrado |
| `caribe` | Cancún, Riviera Maya, Bahamas, San Andrés |
| `cruzeiro` | MSC Divina, Costa Serena |

Para forçar região em um pacote novo, adicione no HTML: `data-regiao="caribe"` no `<article class="card">`.

Para forçar valor no `purchase`, use `data-valor-total="7236"` quando `.card__total` não tiver número claro.

## Privacidade

Nenhum evento envia dados digitados no formulário (destino, datas, orçamento, etc.).
