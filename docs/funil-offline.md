# Funil offline — Google Sheets + GA4 Measurement Protocol

Guia para registrar etapas comerciais que acontecem fora do site (WhatsApp, atendimento, fechamento).

## Planilha sugerida (colunas)

| Coluna | Exemplo |
|--------|---------|
| DataLead | 08/06/2026 |
| Origem | website |
| Canal | whatsapp / form / email |
| ServicoInteresse | roteiro_personalizado |
| DestinoInteresse | Itália |
| Status | Em atendimento |
| MotivoDesqualificacao | — |
| MotivoPerda | — |
| ValorEstimado | 15000 |
| ValorFechado | 12000 |
| DataFechamento | 20/06/2026 |
| UltimoEventoGA4 | working_lead |
| Observacoes | Cliente quer julho/2027 |

## Status → Evento GA4

| Status na planilha | Evento |
|--------------------|--------|
| Novo lead | (já disparado no site: `generate_lead`) |
| Em atendimento | `working_lead` |
| Qualificado | `qualify_lead` |
| Desqualificado | `disqualify_lead` |
| Fechado | `close_convert_lead` |
| Perdido | `close_unconvert_lead` |

## Pré-requisitos no GA4

1. Measurement ID: `G-WGDNTSY8WM`
2. Criar **API Secret** em Admin → Data Streams → Web → Measurement Protocol API secrets
3. Marcar como conversão: `working_lead`, `qualify_lead`, `close_convert_lead`

## Apps Script

Arquivo precisa ser **Planilhas Google** (não Excel `.xlsx`). Aba pode ser `Leads` dentro da planilha da empresa.

`onEdit` simples **não** pode usar `UrlFetchApp`. Use gatilho instalável: cole o script → Execute **`instalarGatilhoLeads`** uma vez → autorize.

Colunas: `DataLead | Origem | Canal | ServicoInteresse | DestinoInteresse | Status | MotivoDesqualificacao | MotivoPerda | ValorEstimado | ValorFechado | DataFechamento | UltimoEventoGA4 | Observacoes`

```javascript
const MEASUREMENT_ID = 'G-WGDNTSY8WM';
const API_SECRET = 'COLE_SEU_API_SECRET_AQUI';
const SHEET_NAME = 'Leads';

const COL = {
  ORIGEM: 2, CANAL: 3, SERVICO: 4, STATUS: 6,
  VALOR_FECHADO: 10, ULTIMO_EVENTO: 12
};

const STATUS_EVENT_MAP = {
  'Em atendimento': 'working_lead',
  'Qualificado': 'qualify_lead',
  'Desqualificado': 'disqualify_lead',
  'Fechado': 'close_convert_lead',
  'Perdido': 'close_unconvert_lead'
};

function instalarGatilhoLeads() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'onLeadStatusEdit') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('onLeadStatusEdit')
    .forSpreadsheet(SpreadsheetApp.getActive())
    .onEdit()
    .create();
}

function onLeadStatusEdit(e) {
  if (!e || !e.range) return;
  const sheet = e.range.getSheet();
  if (sheet.getName() !== SHEET_NAME) return;
  const row = e.range.getRow();
  if (row < 2 || e.range.getColumn() !== COL.STATUS) return;

  const status = String(sheet.getRange(row, COL.STATUS).getValue() || '').trim();
  const eventName = STATUS_EVENT_MAP[status];
  if (!eventName) return;

  const lastSent = String(sheet.getRange(row, COL.ULTIMO_EVENTO).getValue() || '').trim();
  if (lastSent === eventName) return;

  const payload = {
    client_id: 'offline.' + Utilities.getUuid(),
    events: [{
      name: eventName,
      params: {
        lead_source: String(sheet.getRange(row, COL.ORIGEM).getValue() || 'website'),
        lead_channel: String(sheet.getRange(row, COL.CANAL).getValue() || 'whatsapp'),
        service_name: String(sheet.getRange(row, COL.SERVICO).getValue() || 'geral'),
        engagement_time_msec: 1
      }
    }]
  };

  if (eventName === 'close_convert_lead') {
    payload.events[0].params.value = Number(sheet.getRange(row, COL.VALOR_FECHADO).getValue()) || 0;
    payload.events[0].params.currency = 'BRL';
    payload.events[0].params.conversion_type = 'payment_confirmed';
  }

  const url = 'https://www.google-analytics.com/mp/collect?measurement_id=' +
    encodeURIComponent(MEASUREMENT_ID) + '&api_secret=' + encodeURIComponent(API_SECRET);

  try {
    const resp = UrlFetchApp.fetch(url, {
      method: 'post', contentType: 'application/json',
      payload: JSON.stringify(payload), muteHttpExceptions: true
    });
    const code = resp.getResponseCode();
    sheet.getRange(row, COL.ULTIMO_EVENTO).setValue(
      code >= 200 && code < 300 ? eventName : 'ERRO HTTP ' + code
    );
  } catch (err) {
    sheet.getRange(row, COL.ULTIMO_EVENTO).setValue('ERRO: ' + String(err.message || err).slice(0, 80));
  }
}
```

**Importante:** não envie nome, e-mail, telefone ou mensagens do cliente nos parâmetros do GA4.

## Próximo passo

1. Aba `Leads` com cabeçalhos acima (Planilhas Google nativa)
2. API Secret no GA4 (Admin → Fluxos de dados → Web → Measurement Protocol)
3. Colar script → Executar `instalarGatilhoLeads` → autorizar
4. Status `Em atendimento` → coluna `UltimoEventoGA4` = `working_lead`
5. GA4: marcar `working_lead` / `qualify_lead` como eventos-chave → importar no Ads (meta principal). Contato por clique do site: meta secundária.
