# UX, acessibilidade e formulário

## Melhorias realizadas

- Skip link “Pular para o conteúdo principal” apontando para `#main-content`.
- Foco visível com `:focus-visible` em `style.css`.
- Labels associados aos campos do formulário por `for`/`id`.
- Texto auxiliar com `aria-describedby` informando campos obrigatórios e destino da mensagem.
- Validação nativa preservada: o `<form id="formViagem">` não usa mais `novalidate`.
- Botão de revogação de consentimento com `role="status"` e `aria-live="polite"` para o retorno da ação.
- Estrutura de conteúdo legal com um `h1`, headings sequenciais, listas, tabelas com cabeçalho e breadcrumb rotulado.

## Contrato do formulário

São obrigatórios: destino, datas/período, número de adultos, cidade de saída e orçamento. O número de adultos também exige mínimo de 1. Se o formulário estiver vazio, o navegador deve bloquear o submit antes de abrir a nova aba do WhatsApp.

## Verificações executadas

No navegador local, foi verificado que:

- o formulário vazio retorna `checkValidity: false`;
- nenhuma nova aba é aberta no submit inválido;
- o banner de consentimento muda de estado sem bloquear catálogo e contato;
- a página de cookies atualiza a mensagem após revogação.

## Limites do check

Não foi emitida certificação WCAG. Ainda não foram feitos teste com leitor de tela, auditoria automatizada completa de contraste, teste com teclado em todas as rotas ou teste em dispositivos físicos. Essas verificações são recomendadas antes de declarar conformidade formal.
