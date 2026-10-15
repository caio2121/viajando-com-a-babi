# Auditoria do conteúdo legal

## Situação encontrada

As seis páginas legais inicialmente continham marcadores de documento provisório. A fonte atual é `_build_legal_pages.py`; as páginas geradas não contêm os marcadores `pending-review`, `lorem ipsum`, “documento pendente de revisão” ou “validação jurídica necessária”.

Isso significa que há conteúdo navegável e coerente, não que exista aprovação jurídica profissional. A necessidade de revisão especializada permanece registrada como pendência interna.

## Cobertura por página

| Página | Cobertura implementada | Limite declarado |
|---|---|---|
| Condições comerciais | cotação, confirmação, oferta, pagamento, inclusão e requisitos de viagem | preço, disponibilidade e regras dependem da proposta/fornecedor |
| Cancelamento e reembolso | canal de solicitação, alteração, remarcação, análise e reembolso | não cria percentual ou prazo geral |
| Contato LGPD | canal, dados mínimos do pedido, direitos e retorno | não há formulário ou backend LGPD próprio |
| Termos de uso | finalidade do site, conteúdo, uso permitido, terceiros e responsabilidades | não afasta direitos obrigatórios |
| Cookies | `localStorage`, categorias, ativação, escolha e revogação | retenção de terceiros depende das configurações externas |
| Privacidade | controlador apresentado no site, dados, finalidades, compartilhamentos, consentimento, retenção e segurança | prazos operacionais e alguns papéis precisam ser confirmados |

## Regras de redação aplicadas

- Não foram inventados prazos de reembolso, percentuais de multa, taxas, parcelas ou obrigações do cliente.
- Regras que variam por passagem, hospedagem, pacote, seguro ou fornecedor são remetidas à oferta, contrato e confirmação aplicáveis.
- Direitos legais são descritos com ressalva de análise do caso concreto.
- O fluxo real — vitrine, atendimento e WhatsApp, sem checkout público nas páginas — é distinguido de uma contratação automática.
- O texto orienta a não enviar cartão, senha ou dados desnecessários por canais inadequados.

## Evidência de geração

`_build_legal_pages.py` define os seis conteúdos, metadados, canonical, data de atualização, navegação relacionada e controle de revogação da página de cookies. O mesmo script deve ser executado quando houver alteração dos textos, evitando divergência entre a fonte e o HTML publicado.
