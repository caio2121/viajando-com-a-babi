# Ajuste fino do site Viajando com a Babi

Você está trabalhando sobre um repositório **já modificado por uma execução anterior**.

A implementação anterior realizou a sincronização de conteúdos do site público da operadora:

https://viajandocomdesconto.com/

para:

https://viajandocomababi.com.br/

O mecanismo de coleta e sincronização já existe e **não deve ser refeito do zero** sem necessidade.

Sua tarefa agora é realizar uma segunda etapa de refinamento focada em:

* organização do catálogo;
* UX;
* filtros;
* ordenação;
* navegação;
* layout das páginas Promo de Voos e Campanhas;
* consistência visual;
* responsividade.

Você possui acesso ao repositório e deve **analisar o estado real atual antes de modificar qualquer arquivo**.

Não responda apenas com plano ou recomendações.

Implemente as alterações reais.

Não use mocks, placeholders ou dados fictícios.

---

# 1. Auditoria antes das alterações

Primeiro analise recursivamente o repositório atual.

Execute:

```bash
git status
git diff
```

Identifique:

* estrutura atual das páginas;
* arquivos gerados pela sincronização;
* arquivos de dados;
* scripts de sincronização;
* CSS;
* JavaScript;
* componentes ou trechos reutilizados;
* header;
* menu mobile;
* footer;
* cards dos pacotes;
* página Promo de Voos;
* página Campanhas;
* analytics;
* SEO;
* sitemap;
* scripts responsáveis por ordenação ou filtros, se já existirem.

Também inspecione o site atualmente publicado para comparar o resultado real com o código.

Não assuma nomes de arquivos ou classes.

Adapte as alterações à arquitetura real encontrada.

---

# 2. Não refazer o que já funciona

A sincronização anterior deve continuar funcionando.

Preserve:

* scraping/coleta;
* normalização;
* identificação de ofertas;
* fingerprints;
* controle de duplicidades;
* atualização periódica;
* exclusão de ofertas expiradas;
* links de WhatsApp;
* SEO;
* analytics;
* dados comerciais;
* identidade visual.

O objetivo desta execução é principalmente **alterar a apresentação e organização dos dados já sincronizados**.

Se alguma alteração no gerador/sincronizador for necessária para manter o novo layout nas próximas execuções, faça também essa alteração.

Isso é essencial.

Não corrija apenas o HTML gerado atual se a próxima sincronização for recriar o problema.

---

# 3. Pacotes sincronizados não podem formar uma categoria separada

Atualmente as ofertas sincronizadas foram colocadas em um grupo separado do catálogo existente.

Isso deve ser removido.

Não deve existir uma divisão visível semelhante a:

```text
Pacote completo

[...]

Cruzeiros

[...]

Mais ofertas

[ofertas sincronizadas]
```

Especificamente:

**remova o conceito visual de “Mais ofertas” utilizado para distinguir pacotes sincronizados.**

Pacotes existentes manualmente e pacotes sincronizados devem participar do **mesmo catálogo**.

Para o visitante não deve existir distinção entre:

* pacote antigo;
* pacote manual;
* pacote sincronizado;
* pacote vindo da operadora.

A origem dos dados pode continuar sendo registrada internamente para controle da sincronização, mas **não deve determinar o agrupamento visual**.

---

# 4. Catálogo único de pacotes

Todos os pacotes comerciais devem participar de uma coleção lógica única.

Exemplo conceitual:

```text
TODOS OS PACOTES
    ├── Salvador
    ├── Gramado
    ├── Foz do Iguaçu
    ├── Buenos Aires
    ├── Aruba
    ├── Bonito
    ├── Cruzeiro
    ├── Orlando
    └── etc.
```

Não organize os pacotes de acordo com a origem técnica dos dados.

Se houver diferenciação comercial realmente necessária, como:

* cruzeiro;
* pacote terrestre;
* pacote com aéreo;

ela deve funcionar como **atributo/filtro**, e não como separação baseada em “manual versus sincronizado”.

---

# 5. Preservar o visual atual dos pacotes

Na página Pacotes, continue utilizando o padrão de card existente do site.

Não transforme a página de pacotes na mesma lista compacta utilizada em Promo de Voos.

Os cards de pacote possuem mais conteúdo e podem continuar mostrando:

* imagem;
* destino;
* datas;
* origem;
* hospedagem;
* serviços;
* passeios;
* aéreo;
* preço;
* parcelamento;
* taxas;
* CTA WhatsApp.

A alteração principal nesta página é:

1. unificação;
2. filtros;
3. ordenação.

---

# 6. Ordenação dos pacotes

Adicionar controle claro:

**Ordenar por**

com pelo menos:

```text
Data
Preço
```

O usuário deve conseguir alternar a ordenação sem recarregar a página.

## Data

Ordenar pela próxima data futura válida da oferta.

Ofertas com múltiplas datas devem utilizar a próxima saída futura válida como referência.

## Preço

Ordenar pelo menor preço total válido disponível para aquele pacote.

A ordenação por preço deve ser:

```text
menor preço → maior preço
```

Pode existir visualmente uma opção adicional:

```text
Maior preço
```

se isso puder ser feito sem complicar a interface.

Mas obrigatoriamente devem existir pelo menos:

* Data;
* Preço.

---

# 7. Normalização necessária para ordenação

Não ordene valores comparando strings.

Exemplo errado:

```text
"R$ 9.000"
"R$ 800"
```

Devem existir valores normalizados internamente.

Cada pacote deve disponibilizar ao JavaScript, diretamente ou através da fonte de dados:

```text
sortDate
sortPrice
```

Exemplo conceitual:

```html
data-sort-date="2026-09-20"
data-sort-price="2180.00"
```

ou estrutura equivalente no modelo de dados existente.

Não altere o preço exibido ao visitante.

Esses campos servem apenas para lógica.

---

# 8. Modal de filtros dos pacotes

Adicionar um botão visível próximo ao controle de ordenação:

**Filtrar pacotes**

Ao clicar, abrir um modal inspirado na experiência observada no site da operadora.

Não copie literalmente o design da operadora.

Use:

* identidade visual da Viajando com a Babi;
* tipografia existente;
* cores existentes;
* componentes existentes.

O conceito do filtro deve seguir a referência apresentada.

---

# 9. Campos do modal de pacotes

O modal deverá conter, quando existirem dados suficientes:

### Origem

Opções derivadas dinamicamente dos próprios pacotes.

Exemplos:

```text
Todas
Rio de Janeiro
São Paulo
Sem aéreo
```

Quando tecnicamente conveniente, aeroportos podem aparecer dentro da origem:

```text
Rio de Janeiro — GIG
Rio de Janeiro — SDU
São Paulo — GRU
São Paulo — CGH
São Paulo — VCP
```

Não hardcode destinos ou aeroportos que não existam nos dados.

---

### Destino

Campo/select contendo somente destinos realmente disponíveis no catálogo atual.

Exemplo:

```text
Todos os destinos
Gramado
Salvador
Foz do Iguaçu
Buenos Aires
Cancún
Aruba
...
```

Preferencialmente com busca quando a quantidade for grande.

---

### Saídas de

Data inicial.

---

### Saídas até

Data final.

---

### Faixa de preço

Permitir limitar o valor máximo.

Pode ser implementado como:

* range;
* slider;
* campo numérico;

desde que seja simples e responsivo.

O valor máximo deve ser baseado nos dados atuais.

Não hardcode `R$ 8.800` ou qualquer outro valor visto no site da operadora.

---

### Tipo de pacote

Quando houver dados confiáveis:

```text
Todos
Com aéreo
Sem aéreo
Cruzeiro
```

Não force classificação incorreta apenas para preencher esse filtro.

---

# 10. Ações do modal

O modal precisa possuir:

```text
Limpar filtros
Aplicar filtros
```

Ao aplicar:

* fechar modal;
* atualizar catálogo imediatamente;
* não recarregar página;
* manter ordenação escolhida;
* mostrar apenas os pacotes compatíveis.

Ao limpar:

* remover todos os filtros;
* restaurar todo o catálogo.

---

# 11. Indicador de filtros ativos

Quando algum filtro estiver ativo, o botão não deve parecer igual ao estado padrão.

Exemplo conceitual:

```text
Filtrar pacotes (3)
```

onde `3` representa a quantidade de critérios ativos.

Também pode existir:

```text
Limpar filtros
```

próximo aos resultados quando houver filtros ativos.

---

# 12. Quantidade de resultados

Mostrar próximo aos controles algo semelhante a:

```text
42 pacotes encontrados
```

Atualizar dinamicamente quando os filtros mudarem.

Não precisa usar exatamente essa frase se o site possuir outra linguagem visual melhor.

---

# 13. Estado vazio

Se nenhum pacote corresponder aos filtros, não deixe simplesmente uma área vazia.

Mostrar:

```text
Nenhum pacote encontrado com esses filtros.
Tente alterar o destino, as datas ou a faixa de preço.
```

Adicionar ação:

```text
Limpar filtros
```

---

# 14. Modal acessível

O modal deve funcionar corretamente com:

* desktop;
* mobile;
* teclado;
* ESC;
* clique no botão fechar;
* clique externo, quando apropriado;
* foco.

Não permitir scroll problemático da página ao fundo enquanto o modal estiver aberto.

Utilize os padrões e bibliotecas já existentes no projeto.

Não adicione um framework inteiro apenas para criar um modal.

---

# 15. Promo de Voos — abandonar cards tradicionais

A página **Promo de Voos** não deve utilizar cards de viagem convencionais.

Não depende de imagens.

Ela deve adotar uma **listagem horizontal compacta**, baseada conceitualmente no modelo da operadora apresentado como referência.

Objetivo:

permitir que o usuário compare rapidamente muitas tarifas.

---

# 16. Estrutura da lista Promo de Voos

Desktop, conceitualmente:

```text
┌─────────────────────────────────────────────────────────────┐
│ Gramado · 4 noites                                          │
│ Saindo do Rio de Janeiro (GIG)                              │
│                                                             │
│ IDA                   VOLTA                   R$ 431          │
│ 20 ago 07:35          24 ago 16:20           + taxa R$ 199  │
│ GIG → POA             POA → GIG                            │
│                                                             │
│ Companhia / lugares                         Tenho interesse │
└─────────────────────────────────────────────────────────────┘
```

Não precisa copiar pixels ou cores da operadora.

O layout deve ser reinterpretado usando a identidade visual atual da Viajando com a Babi.

---

# 17. Informações prioritárias na Promo de Voos

Exibir, quando fornecido pela fonte:

* destino;
* duração/noites;
* origem;
* aeroporto;
* data de ida;
* horário de ida;
* aeroporto de chegada;
* data de retorno;
* horário de retorno;
* companhia aérea;
* lugares disponíveis;
* preço por pessoa;
* taxa;
* outras datas;
* informação de “último lugar”, quando real;
* CTA para WhatsApp.

Não inventar:

* horários;
* companhia;
* assentos;
* aeroportos;
* taxas.

Se uma informação não existir na fonte, adapte a linha sem deixar um placeholder.

---

# 18. Promo de Voos — filtros

A página pode utilizar uma barra de filtros semelhante conceitualmente à referência da operadora.

Utilizar apenas dados disponíveis na versão sincronizada.

Filtros úteis:

```text
Origem
Destino
Saídas de
Saídas até
Preço máximo
```

Como o escopo comercial da sincronização continua focado em Rio e São Paulo, as opções deverão refletir os dados realmente publicados.

Não consultar a operadora em tempo real no navegador.

Todo filtro deve trabalhar sobre os dados estáticos já sincronizados.

---

# 19. Promo de Voos — ordenação

Adicionar:

```text
Ordenar por:
Data
Preço
```

Preferencialmente utilizando o mesmo componente visual usado na página de Pacotes.

Não crie dois padrões de UX completamente diferentes para a mesma função.

---

# 20. Promo de Voos — carregamento progressivo

A quantidade de promoções pode ser grande.

Não é necessário renderizar visualmente centenas de linhas simultaneamente.

Pode ser utilizado:

```text
Mostrar mais ofertas
```

Exemplo:

* mostrar inicialmente 20 ou 30;
* carregar mais blocos da coleção já disponível localmente.

Isso não é paginação do backend.

Os dados continuam estáticos.

Filtros e ordenação devem considerar a coleção completa, inclusive itens ainda não exibidos.

---

# 21. Promo de Voos — mobile

No smartphone, transformar cada linha horizontal em um bloco vertical compacto.

Exemplo conceitual:

```text
Gramado
Rio de Janeiro (GIG)

IDA
20 ago · 07:35

VOLTA
24 ago · 16:20

R$ 431
+ taxa R$ 199

[Tenho interesse]
```

Não permitir overflow horizontal.

---

# 22. Campanhas — remover dependência de imagens

A página **Campanhas** também deve deixar de utilizar qualquer estrutura cujo resultado pareça um card aguardando imagem.

Campanhas devem utilizar uma lista compacta.

Não é necessário buscar imagens adicionais para preencher essa página.

Não use:

* placeholders;
* imagem genérica;
* imagem aleatória;
* imagem repetida apenas para preencher layout.

---

# 23. Estrutura da lista Campanhas

Adaptar o mesmo conceito visual da lista de Promo de Voos, porém utilizando campos próprios de campanhas.

Desktop, conceitualmente:

```text
┌──────────────────────────────────────────────────────────────┐
│ Porto Seguro                                                 │
│ Resort Arcobaleno All Inclusive                              │
│                                                              │
│ BENEFÍCIO             HOSPEDAGEM           VENDAS ATÉ         │
│ 7x6                   01/08 a 30/11        31/08              │
│                                                              │
│ All Inclusive · 2 crianças até 11 anos                       │
│                                             [Quero saber mais]│
└──────────────────────────────────────────────────────────────┘
```

---

# 24. Informações prioritárias nas campanhas

Mostrar, quando disponíveis:

* destino;
* hotel/resort;
* nome da campanha;
* desconto;
* benefício;
* período de hospedagem;
* prazo de venda;
* regime de alimentação;
* política de crianças;
* condição especial;
* CTA.

Informações muito longas não devem destruir a listagem.

---

# 25. Condições extensas das campanhas

Quando houver textos longos de regras, como:

* exceções;
* datas bloqueadas;
* restrições;
* políticas;
* condições cumulativas;

mostrar apenas um resumo na linha.

Disponibilizar:

```text
Ver condições
```

utilizando:

* `<details>`;
* expansão inline;
* modal leve;

conforme for mais compatível com o projeto.

**Nenhuma informação comercial deve ser descartada.**

O objetivo é apenas reduzir poluição visual.

---

# 26. Campanhas — carregamento progressivo

Existem muitas campanhas.

Utilize também um mecanismo:

```text
Mostrar mais campanhas
```

ou paginação client-side leve.

Exemplo:

```text
30 inicialmente
+30 por clique
```

Não é obrigatório exatamente 30.

Escolha um valor coerente com performance e UX.

---

# 27. Footer está desatualizado

Corrigir a navegação existente no footer.

Essa alteração deve ser feita **globalmente**, não apenas nas três páginas novas.

O footer deve refletir a navegação real atual do site.

Deve conter pelo menos acesso coerente a:

```text
Início
Sobre a Babi
Como funciona
Pacotes de viagem
Promo de Voos
Campanhas
Serviços
FAQ
Depoimentos
Pagamento
Privacidade
Certificado Cadastur
```

A ordem pode ser ajustada conforme o layout existente.

---

# 28. Não corrigir footer página por página manualmente se houver solução central

Investigue como o site replica:

* header;
* footer;
* menu.

Se houver gerador/template/include, altere a fonte central.

Se for um site totalmente estático e os trechos estiverem realmente duplicados em vários HTML, atualize todas as páginas relevantes de forma consistente.

Pesquise o repositório depois para garantir que versões antigas do bloco não ficaram esquecidas.

---

# 29. Consistência do menu principal

Durante a auditoria, verifique também se páginas antigas ainda apresentam menu sem:

* Promo de Voos;
* Campanhas.

Caso existam versões diferentes da navegação superior, normalize-as para o padrão atual.

A navegação principal e o footer não podem fornecer mapas diferentes do site.

---

# 30. Fonte de dados versus visualização

Mantenha clara a separação:

```text
dados
↓
normalização
↓
HTML/UI
```

Não duplique dados apenas para suportar filtros.

Quando possível, utilize a fonte normalizada já criada pela sincronização.

Por exemplo:

```javascript
offers = [...]
```

ou dados equivalentes já existentes.

Filtros, ordenação e renderização devem operar sobre essa coleção.

---

# 31. Preservar conteúdo manual

A unificação da página Pacotes é apenas visual/lógica.

Ela **não significa transformar conteúdo manual em conteúdo sincronizado**.

Internamente continue distinguindo:

```text
source: manual
source: viajandocomdesconto
```

quando isso for necessário para sincronização.

Essa informação simplesmente não deve criar categorias separadas para o visitante.

---

# 32. Atualizações futuras

Esta mudança precisa sobreviver às futuras execuções mensais da sincronização.

Depois da próxima atualização automática:

* pacotes novos devem entrar no catálogo único;
* não deve reaparecer “Mais ofertas”;
* Promo de Voos deve continuar em lista;
* Campanhas deve continuar em lista;
* filtros devem continuar funcionando;
* ordenação deve continuar funcionando.

Portanto investigue o gerador atual.

Se ele gerar diretamente os HTMLs, altere também os templates/renderizadores responsáveis.

Não faça uma correção temporária no arquivo final.

---

# 33. Não usar chamadas à operadora no browser

Os filtros adicionados ao site da Babi devem operar localmente.

Não implementar no frontend do visitante:

```javascript
fetch("https://viajandocomdesconto.com/...")
```

A operadora continua sendo consultada somente durante o processo de atualização/sincronização.

O visitante usa a versão estática publicada no GitHub Pages.

---

# 34. Analytics

Preserve o analytics atual.

Caso o site já possua eventos compatíveis, rastrear:

```text
filter_packages_open
filter_packages_apply
filter_packages_clear
sort_packages
sort_flights
flight_whatsapp_click
campaign_whatsapp_click
package_whatsapp_click
```

Somente faça isso seguindo exatamente o padrão existente.

Não invente ID GA4.

Não crie uma segunda implementação.

Não envie dados pessoais ou textos digitados pelo usuário para analytics.

---

# 35. URLs e SEO

Preservar:

```text
pacotes.html
promo-voos.html
campanhas.html
```

caso estas sejam as URLs atuais.

Não alterar URLs públicas sem necessidade.

Preserve:

* title;
* description;
* canonical;
* OpenGraph;
* sitemap;
* headings.

Mudanças de layout não devem reduzir a indexabilidade do conteúdo.

O conteúdo relevante deve continuar presente no HTML ou ser acessível de forma adequada para mecanismos de busca.

---

# 36. JavaScript sem dependências desnecessárias

O site é estático.

Implemente:

* filtros;
* ordenação;
* modal;
* “mostrar mais”;

com JavaScript leve compatível com a arquitetura existente.

Não introduza React, Vue, Angular ou outro framework apenas para essas funções se o projeto não os utiliza.

---

# 37. Performance

As páginas possuem muitas ofertas.

Evite:

* centenas de listeners individuais desnecessários;
* reflows excessivos;
* reconstruir todo DOM a cada pequeno evento;
* scripts pesados;
* grandes dependências.

Considere event delegation e manipulação eficiente das coleções.

---

# 38. Responsividade obrigatória

Validar pelo menos:

```text
375px
768px
1024px
1440px
```

Verificar:

### Pacotes

* cards;
* modal;
* selects;
* datas;
* range/preço;
* botões;
* ordenação.

### Promo de Voos

* linhas;
* origem/destino;
* datas;
* preços;
* CTA;
* ausência de overflow.

### Campanhas

* textos;
* benefícios;
* datas;
* condições expansíveis;
* CTA.

---

# 39. Estados visuais

Implementar estados adequados para:

```text
hover
focus
active
disabled
empty
filtered
```

Priorize acessibilidade.

---

# 40. Referência visual da operadora

Utilize o site:

https://viajandocomdesconto.com/

apenas como referência de **organização da informação e experiência de comparação**.

Não copie sua identidade.

A referência conceitual é:

```text
FILTROS
↓
ORDENAÇÃO
↓
CONTAGEM
↓
LISTA COMPACTA
↓
MOSTRAR MAIS
```

A identidade final continua sendo:

**Viajando com a Babi.**

---

# 41. Resultado esperado para Pacotes

Antes:

```text
Pacotes existentes
↓
Cruzeiros
↓
Mais ofertas
↓
Pacotes sincronizados
```

Depois:

```text
[ Filtrar pacotes ]   [ Ordenar por: Data ▾ ]

42 pacotes encontrados

Pacote A
Pacote B
Pacote C
Pacote sincronizado D
Pacote manual E
Pacote F
...
```

Tudo em uma única coleção visual.

---

# 42. Resultado esperado para Promo de Voos

Antes:

```text
card
card
card
card
card
...
```

Depois:

```text
Promo de Voos

[Origem] [Destino] [Saídas] [Preço] [Pesquisar]

Ordenar por: Data

Gramado        GIG → POA       20/08 → 24/08       R$ 431
Foz            GRU → IGU       18/09 → 22/09       R$ 584
Salvador       GIG → SSA       04/09 → 08/09       R$ 693
...

[Mostrar mais ofertas]
```

---

# 43. Resultado esperado para Campanhas

Antes:

```text
card sem imagem
card sem imagem
card sem imagem
...
```

Depois:

```text
Campanhas

Porto Seguro | Arcobaleno    7x6      hosp. até 30/11   vendas até 31/08
Praia Forte  | Iberostar     20%      hosp. ...         vendas até ...
Orlando      | Universal     30%      hosp. ...         vendas até ...
...

[Mostrar mais campanhas]
```

Mantendo CTA individual.

---

# 44. Validação funcional

Depois de implementar, testar obrigatoriamente:

* filtro por origem;
* filtro por destino;
* filtro por data inicial;
* filtro por data final;
* filtro por preço;
* combinação de vários filtros;
* limpar filtros;
* modal abrir;
* modal fechar;
* ESC;
* ordenação por data;
* ordenação por preço;
* resultado vazio;
* mostrar mais;
* WhatsApp Pacotes;
* WhatsApp Promo Voos;
* WhatsApp Campanhas;
* menu desktop;
* menu mobile;
* footer;
* links;
* imagens dos pacotes;
* páginas sem imagens Promo/Campanhas.

---

# 45. Validar dados

Após reestruturar as páginas, confirme que nenhum campo comercial foi alterado acidentalmente.

Compare amostras com os dados existentes antes da alteração:

* preço;
* taxa;
* destino;
* origem;
* data;
* hotel;
* desconto;
* benefício;
* aéreo.

Layout não pode mudar dados comerciais.

---

# 46. Validar conteúdo expirado

Não altere as regras de expiração já existentes sem necessidade.

Porém durante a validação confirme que o novo filtro/ordenador não passa a considerar datas históricas como `sortDate`.

Em ofertas com:

```text
datas anteriores + datas futuras
```

utilize a próxima data futura.

---

# 47. Revisão do código

Ao concluir:

```bash
git status
git diff --stat
git diff
```

Revise todo o diff.

Procure por:

```text
TODO
FIXME
placeholder
mock
Lorem
```

Valide também console JavaScript.

---

# 48. Critérios de aceite

A execução somente poderá ser considerada concluída se:

* [ ] Pacotes sincronizados e pacotes existentes estiverem no mesmo catálogo.
* [ ] A seção visual “Mais ofertas” tiver sido eliminada.
* [ ] Origem técnica não determinar agrupamento visual.
* [ ] Pacotes puderem ser ordenados por data.
* [ ] Pacotes puderem ser ordenados por preço.
* [ ] Existir modal funcional para filtros de pacotes.
* [ ] Filtros funcionarem sem reload.
* [ ] Quantidade de resultados atualizar corretamente.
* [ ] Estado vazio funcionar.
* [ ] Promo de Voos utilizar listagem compacta.
* [ ] Promo de Voos não depender de imagens.
* [ ] Campanhas utilizar listagem compacta.
* [ ] Campanhas não depender de imagens.
* [ ] Condições completas das campanhas continuarem acessíveis.
* [ ] Footer estiver atualizado em todo o site.
* [ ] Header estiver consistente entre páginas.
* [ ] Navegação mobile estiver atualizada.
* [ ] WhatsApp continuar funcionando.
* [ ] Analytics continuar funcionando.
* [ ] SEO continuar funcionando.
* [ ] Sincronizações futuras preservarem o novo layout.
* [ ] Não existirem mocks.
* [ ] Não existirem placeholders.
* [ ] O site continuar compatível com GitHub Pages.
* [ ] Desktop e mobile tiverem sido validados.

---

# 49. Relatório final obrigatório

Ao terminar, forneça:

## Arquivos modificados

Liste arquivos e finalidade.

## Pacotes

Informe:

```text
Total no catálogo:
Pacotes manuais:
Pacotes sincronizados:
Ordenação por data: OK/FALHA
Ordenação por preço: OK/FALHA
Filtros: OK/FALHA
```

## Promo de Voos

Informe:

```text
Total de ofertas:
Novo layout de lista: OK/FALHA
Filtros: OK/FALHA
Ordenação: OK/FALHA
Mostrar mais: OK/FALHA
```

## Campanhas

Informe:

```text
Total de campanhas:
Novo layout de lista: OK/FALHA
Condições expansíveis: OK/FALHA
Mostrar mais: OK/FALHA
```

## Navegação

Informe:

```text
Header: OK/FALHA
Menu mobile: OK/FALHA
Footer: OK/FALHA
```

## Testes

Liste os testes/comandos realmente executados.

## Pendências

Liste somente problemas reais que não tenham sido solucionados.

---

# 50. Instrução final

Não apenas descreva essas alterações.

**Inspecione o repositório, implemente, teste e revise.**

Priorize uma solução simples, robusta e compatível com a arquitetura existente.

Não reescreva o projeto sem necessidade.

Não utilize mocks.

Não deixe trabalho incompleto para uma etapa posterior se puder ser resolvido nesta execução.
