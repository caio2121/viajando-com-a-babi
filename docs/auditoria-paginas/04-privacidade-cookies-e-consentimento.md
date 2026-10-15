# Privacidade, cookies e consentimento

## Comportamento observado

O comportamento foi conferido no código e exercitado no navegador local:

1. `_partials/ga4.html` define a chave `vcb_consent_analytics` no `localStorage`.
2. Antes de aceite, os sinais `analytics_storage`, `ad_storage`, `ad_user_data` e `ad_personalization` ficam negados.
3. O script remoto do Google só é inserido quando há consentimento concedido.
4. Aceitar grava `granted`, atualiza os sinais e carrega as tags configuradas.
5. Recusar grava `denied` e oculta o banner sem carregar as tags Google.
6. `VCBConsent.revoke()` grava `denied`, atualiza os sinais quando a função está disponível e permite nova escolha pelo banner.
7. `cookies.html` oferece um botão explícito de revogação e uma mensagem de status acessível.

## Dados do formulário

O formulário da home coleta destino, datas/período, adultos, idades de crianças, cidade de saída e orçamento para montar uma mensagem. O JavaScript abre o WhatsApp; não foi identificado envio desses campos para um backend próprio no fluxo observado. A conversa e o tratamento posterior passam a depender também do WhatsApp e dos procedimentos da empresa.

## Texto público alinhado

`privacidade.html` e `cookies.html` descrevem o `localStorage`, o carregamento condicionado, o compartilhamento com fornecedores quando necessário e a ausência de prazo operacional confirmado para retenção de mensagens. A redação evita afirmar que uma tag ou cookie de terceiro tenha prazo controlado pelo site.

## Pontos a confirmar pela empresa

- categorias e prazos de retenção no WhatsApp, e-mail e ferramentas internas;
- fornecedores que recebem dados em cada tipo de viagem;
- configuração efetiva da conta Google e retenção escolhida nela;
- canal e responsável formal para solicitações de titulares;
- procedimento de eliminação, correção, exportação e resposta aos pedidos.

## Evidências

- Código: `_partials/ga4.html`, `_partials/cookie-banner.html`, `script.js` e `index.html`.
- Páginas: `cookies.html`, `privacidade.html` e `contato-lgpd.html`.
- Teste browser: recusa → `denied` sem Google; aceite → `granted` com tags; revogação → `denied` e status atualizado.
