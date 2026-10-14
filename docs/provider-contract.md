# Contrato do provider Cativa

## Versão

O adapter atual é `cativa-v1`. Ele recebe grupos normalizados pelo snapshot
(`pacotes`, `promo_voos` e `campanhas`) e não expõe o formato bruto à API.

## Campos mínimos

| Campo | Obrigatório | Regra |
|---|---|---|
| `id` ou `fingerprint` | sim | string não vazia e estável entre syncs |
| `title` ou `destination` | sim | string não vazia após normalização |
| `sort_price` | não | número finito maior ou igual a zero |
| `origin_bucket` | não | normalizado; validação de domínio permanece no catálogo |
| `departure_date`/`sort_date` | não | texto ISO quando fornecido pelo source |
| `currency` | não | default `BRL` no adapter |

Tipos aceitos: `pacote`, `promo-voo` e `campanha`. Registros não objeto, tipo
desconhecido, identificador ausente, título/destino vazio e preço negativo,
infinito ou não numérico são rejeitados antes do upsert.

## Campos produzidos

O adapter produz `source`, `provider`, `external_id`, `kind`, título/destino,
origens, classificação, datas, preço/moeda, status, destaque, ordenação,
`data_json` e `rendered_html`. O status automático é `published` somente após o
lote passar pela validação/importação transacional.

O endpoint público expõe somente o contrato normalizado e o HTML renderizado;
`data_json` bruto do provider não é incluído. O payload completo só pode ser
consultado por fluxo administrativo autenticado quando necessário para operar
o catálogo.

## Compatibilidade e falha

1. Mudança de payload exige nova versão de contrato/fixture antes de alterar o
   adapter.
2. Campo opcional ausente recebe default seguro; campo obrigatório inválido
   rejeita o item/lote conforme a política de sync.
3. Rejeição não grava oferta nova nem remove o last-known-good.
4. O erro precisa identificar regra/campo sem registrar payload sensível.
5. O provider não deve acessar caminhos locais, executar comandos ou seguir
   host não permitido.

## Reconciliação do snapshot

Cada execução calcula um SHA-256 do JSON canônico e registra o valor em
`sync_runs.snapshot_checksum`. Os registros recebidos passam por
`sync_run_items` como staging: somente um lote inteiro validado pode fazer
upsert em `offers`. Falha de leitura, JSON inválido, snapshot vazio, schema
drift, duplicata ou conflito de ownership registra a execução como `failed`,
coloca os itens em `rejected` e preserva o catálogo anterior.

Quando uma execução válida não contém uma oferta automática existente, a
oferta não é apagada nem arquivada: permanece como last-known-good com
`offers.sync_state = 'stale'`, recebe um item `removed` na execução e pode ser
reconciliada em um snapshot posterior. Ofertas presentes retornam a
`sync_state = 'current'`. A reconciliação não se aplica a ofertas manuais.

## Fixtures

Os testes devem manter pelo menos: válido por grupo, identificador alternativo,
preço string/número, título derivado do destino, objeto inválido, tipo inválido,
ID ausente, título/destino ausente, preço inválido/negativo/infinito e payload
com campos extras. Nenhuma fixture usa dados reais ou segredo.
