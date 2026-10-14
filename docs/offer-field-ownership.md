# Contrato de campos e ownership de ofertas

Este contrato separa a origem dos valores do catálogo. Ele não altera regras
comerciais nem autoriza o provider a publicar conteúdo manual.

## Matriz

| Campo/grupo | Oferta automática | Pacote manual | Regra de conflito |
|---|---|---|---|
| `source`, `provider`, `external_id`, `kind` | sistema/provider | sistema/admin | identidade não é editável; colisão entre manual e provider rejeita o sync |
| `title`, `destination`, origem e datas | provider | admin | automático segue snapshot; manual permanece separado |
| preço, moeda, parcelamento e taxas | provider | admin | provider não altera pacote manual; divergência exige revisão |
| operadora, categoria e informações do provider | provider | admin informado pelo operador | valor recebido é preservado no snapshot automático |
| tags, destaque, ordenação e imagem editorial | admin | admin | nunca são inferidos como edição do provider |
| `features`/informações adicionais | provider quando vierem no snapshot; override manual futuro | admin | override deve ser registrado em `offer_overrides` |
| `status`/publicação | sync pode publicar somente lote válido | admin | transições editoriais pertencem ao fluxo administrativo |
| `data_json` e `rendered_html` | derivados do registro aceito | derivados do formulário | não são fonte de ownership; devem refletir o valor final |

## Invariantes implementados

1. O upsert automático usa `(provider, external_id)` e nunca seleciona uma
   oferta `source = 'manual'` para atualização.
2. Se um identificador recebido pelo provider colidir com pacote manual, o lote
   é rejeitado com `ownership_conflict`, permanece sem publicação e a falha é
   registrada em `sync_runs.details_json`.
3. Falha de contrato ou ownership não remove o last-known-good.
4. Overrides editoriais permitidos (`is_highlight` e `display_order`) são
   persistidos na tabela `offer_overrides`, aplicados na leitura e nunca
   mutam silenciosamente o `data_json` do provider. Imagem, tags e features
   continuam reservados até haver renderer próprio para esses campos.
5. O admin identifica `Manual`/`Provider`, sinaliza `stale`, exibe histórico
   sanitizado de campos e não oferece edição direta de oferta automática.

## Validações

- campos textuais têm limites e são validados server-side;
- preço deve ser finito e não negativo;
- pacote manual aceita somente `kind = pacote`;
- status e origem usam allowlist;
- payload desconhecido do provider gera `schema_drift` antes do upsert;
- respostas de conflito expõem código acionável, não payload ou segredo.

## Exemplos de conflito

- provider envia preço novo para oferta automática: atualiza o registro
  automático conforme o contrato e registra a sync;
- admin edita um pacote manual com o mesmo identificador externo: o provider
  recebe `ownership_conflict`, sem criar/alterar a oferta manual;
- admin precisa corrigir a posição/destaque de uma oferta automática: usa os
  endpoints de override com motivo, autor, auditoria e remoção reversível.
- título, preço ou destino automáticos não podem ser sobrescritos por esse
  fluxo; o provider continua sendo a fonte desses campos.

## Rollback

Desabilitar o provider ou restaurar o snapshot last-known-good. Não apagar uma
oferta manual para resolver colisão e não transformar a oferta automática em
manual sem histórico/auditoria.
