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
| EventoGA4Enviado | sim |
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
3. Marcar como conversão: `qualify_lead`, `close_convert_lead` (e opcionalmente `working_lead`)

## Apps Script (exemplo)

No Google Sheets: Extensões → Apps Script. Cole e preencha `MEASUREMENT_ID` e `API_SECRET`:

```javascript
const MEASUREMENT_ID = 'G-WGDNTSY8WM';
const API_SECRET = 'COLE_SEU_API_SECRET_AQUI';

const STATUS_EVENT_MAP = {
  'Em atendimento': 'working_lead',
  'Qualificado': 'qualify_lead',
  'Desqualificado': 'disqualify_lead',
  'Fechado': 'close_convert_lead',
  'Perdido': 'close_unconvert_lead'
};

function onEdit(e) {
  const sheet = e.source.getActiveSheet();
  if (sheet.getName() !== 'Leads') return;

  const row = e.range.getRow();
  if (row < 2) return;

  const status = sheet.getRange(row, 6).getValue(); // coluna Status
  const eventName = STATUS_EVENT_MAP[status];
  if (!eventName) return;

  const alreadySent = sheet.getRange(row, 12).getValue(); // EventoGA4Enviado
  if (alreadySent === 'sim') return;

  const clientId = 'offline.' + Utilities.getUuid();
  const payload = {
    client_id: clientId,
    events: [{
      name: eventName,
      params: {
        lead_source: 'website',
        lead_channel: String(sheet.getRange(row, 3).getValue() || 'whatsapp'),
        service_name: String(sheet.getRange(row, 4).getValue() || 'geral')
      }
    }]
  };

  if (eventName === 'close_convert_lead') {
    const value = Number(sheet.getRange(row, 10).getValue()) || 0;
    payload.events[0].params.value = value;
    payload.events[0].params.currency = 'BRL';
    payload.events[0].params.conversion_type = 'payment_confirmed';
  }

  const url = 'https://www.google-analytics.com/mp/collect?measurement_id=' +
    MEASUREMENT_ID + '&api_secret=' + API_SECRET;

  UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  sheet.getRange(row, 12).setValue('sim');
}
```

**Importante:** não envie nome, e-mail, telefone ou mensagens do cliente nos parâmetros do GA4.

## Próximo passo

1. Criar aba `Leads` com os cabeçalhos acima
2. Gerar API Secret no GA4
3. Colar o script e autorizar
4. Testar mudando um status para "Qualificado" e verificar em DebugView (pode levar alguns minutos)
