# Corrigir catálogo e fonte de Promo de Voos

O site já passou pelas alterações estruturais anteriores.

**Não refazer layout, navegação, footer ou unificação do catálogo que já estejam funcionando.**

O foco desta execução é corrigir a **integridade dos dados**, os **filtros** e principalmente a fonte da página **Promo de Voos**.

Antes de modificar qualquer arquivo:

```bash
git status
git diff
```

Inspecione:

* `_sync_operator.py`
* `_build_ofertas.py`
* `_build_pacotes.py`
* `_catalog_ui.py`
* `script.js`
* arquivos de dados gerados pelo sync
* HTML atualmente gerado para Pacotes, Promo de Voos e Campanhas

Não aplique patches apenas no HTML final se ele for gerado por scripts. Corrija sempre a origem do problema.

---

# P0 — Corrigir primeiro a normalização de datas

Este é o problema prioritário.

Atualmente a coleta/renderização pode produzir:

* ida posterior à volta;
* mês incorreto;
* ano incorreto;
* datas de `outras` assumidas como data principal;
* datas JavaScript brutas;
* datas vencidas tratadas como futuras.

Antes de corrigir os filtros, centralize a normalização das datas.

## 1. Criar uma representação canônica

Pacotes devem possuir conceitualmente:

```python
departure_dates = [
    "2026-08-20",
    "2026-09-16",
    "2026-10-10",
]
```

Promoções de voo devem possuir, quando a fonte fornecer:

```python
departure_date
departure_time
return_date
return_time
departure_airport
arrival_airport
```

Não usar uma única string formatada como fonte para filtro e ordenação.

---

## 2. `data-sort-date` e `data-dates`

Para Pacotes:

```text
data-sort-date
```

deve conter somente a **próxima saída futura válida**.

Exemplo:

```html
data-sort-date="2026-08-20"
```

Adicionar:

```html
data-dates="2026-08-20,2026-09-16,2026-10-10"
```

contendo todas as **datas de saída futuras conhecidas**, ordenadas e sem duplicidade.

`data-sort-date` serve para ordenar.

`data-dates` serve para filtrar.

---

# 3. Interpretar corretamente intervalos

Não tratar os dois lados de um intervalo como duas saídas.

Exemplo:

```text
16 a 21/09
```

significa:

```text
saída = 16/09
retorno = 21/09
```

e não:

```text
saídas = 16/09 e 21/09
```

Já:

```text
Outras saídas: 20/08, 19/09, 17/10
```

representa três datas adicionais de saída.

---

# 4. Inferência de ano

Existem datas sem ano.

A normalização deve considerar:

* ano explicitamente fornecido;
* data de atualização/coleta;
* contexto da oferta;
* mudança de ano.

Exemplo em agosto de 2026:

```text
20/09
10/10
15/01
```

deve normalmente resultar em:

```text
2026-09-20
2026-10-10
2027-01-15
```

quando esse encadeamento for compatível com a fonte.

Não transformar janeiro de uma temporada futura em janeiro já vencido de 2026.

---

# 5. Validação obrigatória de itinerário

Para Promo de Voos:

```python
return_datetime >= departure_datetime
```

deve ser uma invariável.

Se o resultado do parser produzir:

```text
ida 26/10
volta 13/10
```

não publique o registro.

Primeiro tente reinterpretar usando os campos originais.

Se ainda não for possível resolver com segurança:

* registre a inconsistência;
* descarte aquela ocorrência;
* não invente datas.

Da mesma forma, nenhuma string semelhante a:

```text
Sat Oct 10 2026 00:00:00 GMT-0300
```

pode chegar ao HTML.

Toda data precisa passar pela normalização antes da renderização.

---

# P0 — Corrigir filtro de datas de Pacotes

Em `script.js`, não filtrar Pacotes apenas por:

```text
data-sort-date
```

Ler:

```text
data-dates
```

como array.

Exemplo:

```javascript
function itemDates(el) {
  return (el.dataset.dates || '')
    .split(',')
    .map(v => v.trim())
    .filter(Boolean);
}
```

Quando existir intervalo de filtro:

```text
Saídas de
Saídas até
```

o pacote deve ser aceito se **pelo menos uma data de saída** estiver dentro do intervalo solicitado.

Conceitualmente:

```javascript
dates.some(date => {
    return (!from || date >= from) &&
           (!to || date <= to);
});
```

### Oferta sem data conhecida

Sem filtro de data ativo:

* pode continuar sendo mostrada;
* ordenar depois das ofertas que possuem data concreta.

Com filtro de data ativo:

* **não deve ser considerada compatível**, pois não existe informação suficiente para afirmar que possui saída naquele período.

Não usar “sem data não é excluída” quando o usuário explicitamente filtrou um período.

---

# P0 — Substituir a fonte atual da Promo de Voos

A página Promo de Voos deve ser alimentada exclusivamente pelos **Bloqueios Aéreos / Promo Voo** da operadora.

Não utilizar:

```text
PACOTES
```

como fonte de Promo de Voos.

Não converter pacote com hotel em tarifa aérea.

A fonte precisa representar exatamente o conteúdo da área:

```text
Promo Voo
Bloqueios aéreos
```

---

# 6. Descobrir corretamente o payload de voos

O código atual não deve depender de regex gulosa sobre todo o HTML.

Investigue os scripts da página da operadora e localize o objeto/array responsável pelos bloqueios aéreos.

Pode existir como:

```text
voos
DADOS
window.*
JSON serializado
estado inicial da aplicação
```

Primeira opção:

1. localizar exatamente a atribuição;
2. extrair o array/objeto por delimitadores balanceados;
3. transformar em estrutura Python;
4. validar quantidade e conteúdo.

Se o objeto não for JSON puro, não tente resolver com uma regex cada vez maior.

Como fallback:

* executar a página;
* inspecionar seu estado JavaScript;
* ou identificar a chamada de rede utilizada pelo próprio frontend.

A coleta precisa usar a **fonte completa dos bloqueios**, não uma amostra parcial como `PV_SNAPSHOT`.

---

# 7. Origem: RIO e SAO

Corrigir `classify_origin`.

Considerar:

```text
RIO
GIG
SDU
Rio de Janeiro
```

como grupo:

```text
Rio de Janeiro
```

Considerar:

```text
SAO
GRU
CGH
VCP
São Paulo
Campinas
```

como grupo comercial:

```text
São Paulo
```

para efeito da regra de seleção do site.

Mas não confundir código metropolitano com aeroporto.

`RIO` e `SAO` podem representar a região/cidade.

Quando o bloqueio trouxer o aeroporto real do trecho:

```text
GIG
SDU
GRU
CGH
VCP
```

esse IATA deve ser utilizado na linha exibida.

Não mostrar `RIO` como se fosse aeroporto específico quando existir `GIG` ou `SDU` no segmento.

---

# 8. Coletar nacionais e internacionais

A coleção final da página Promo de Voos deve conter todos os bloqueios válidos cuja origem comercial esteja em:

```text
Rio de Janeiro
São Paulo
```

independentemente de o destino ser:

```text
nacional
internacional
```

Não obter internacionais através de `PACOTES`.

Nacionais e internacionais precisam vir da **mesma fonte de bloqueios aéreos**.

Preservar no modelo:

```python
destination_type = "nacional"
```

ou:

```python
destination_type = "internacional"
```

quando a fonte fornecer essa informação.

---

# 9. Adicionar filtro Tipo de destino

Na página Promo de Voos, adicionar antes de Origem:

```text
Tipo de destino

Todos
Nacionais
Internacionais
```

Utilizar o campo normalizado da própria fonte.

Não classificar manualmente por uma lista fixa de países se o payload já informar o tipo.

Somente criar fallback por país/destino se a informação realmente não estiver disponível e houver uma implementação confiável.

---

# 10. Modelo correto de um bloqueio aéreo

Normalizar cada registro conceitualmente como:

```python
{
    "source_id": "...",
    "destination_type": "nacional",
    "origin_city": "Rio de Janeiro",
    "origin_airport": "GIG",
    "destination": "Gramado",
    "destination_airport": "POA",
    "departure_date": "2026-08-20",
    "departure_time": "07:35",
    "return_date": "2026-08-24",
    "return_time": "16:20",
    "nights": 4,
    "price": 431.00,
    "tax": 199.00,
    "seats": null,
    "last_seats": null
}
```

Campos inexistentes devem permanecer `None`/ausentes.

Não inventar:

* horário;
* aeroporto;
* companhia;
* lugares;
* taxa;
* retorno.

---

# 11. Taxa deve pertencer à oferta

Não utilizar uma taxa padrão global.

A taxa precisa vir do próprio bloqueio ou de um campo inequivocamente relacionado à tarifa.

Cada item deve ter:

```python
price
tax
```

independentes.

Se a fonte não fornecer taxa:

* não inventar;
* não reutilizar taxa de outro item;
* não aplicar `398,04` como fallback universal.

Renderizar simplesmente o valor disponível.

---

# 12. Remover parcelamento incorreto de Promo de Voos

A listagem de bloqueios da operadora é orientada a:

```text
tarifa
+
taxa
```

Não aproveitar dados de parcelamento vindos de Pacotes.

Só exibir algo como:

```text
10x de R$ ...
```

se esse parcelamento estiver explicitamente associado àquele bloqueio aéreo na fonte.

Caso contrário, o layout deve mostrar apenas:

```text
R$ 431
+ taxa R$ 199
```

Isso evita cruzamento acidental entre preço de tarifa e dados de pacote/hotel.

---

# 13. Horários e aeroportos

Atualizar `render_voo_row()` para aproveitar os campos reais quando presentes.

Exemplo:

```text
20 ago    07:35
GIG   →   POA

24 ago    16:20
POA   →   GIG
```

Se o horário não existir:

```text
20 ago
GIG → POA
```

Nunca utilizar horário fictício.

Se o aeroporto de destino não vier da fonte, usar apenas o nome do destino.

---

# 14. Noites

Se a fonte trouxer explicitamente:

```text
4 noites
```

preserve.

Se houver datas completas e confiáveis, pode calcular:

```python
(return_date - departure_date).days
```

Não calcular noites sobre datas incompletas ou inconsistentes.

---

# 15. Deduplicação dos bloqueios

Prioridade:

```text
source_id
```

Se houver ID confiável da operadora, ele é a chave principal.

Sem ID, fingerprint deve considerar no mínimo:

```text
origem
aeroporto de origem
destino
aeroporto de destino
data/hora ida
data/hora volta
preço
taxa
```

Não deduplicar apenas por:

```text
destino + origem + preço
```

pois podem existir voos diferentes no mesmo dia.

Por outro lado, registros realmente idênticos não devem aparecer repetidos.

---

# P1 — Corrigir preço máximo

Para Pacotes e Promo de Voos:

```javascript
const calculatedCeiling =
  Math.ceil((maxPrice || 0) / 100) * 100;

const ceiling = Math.max(10000, calculatedCeiling);
```

Assim o range nunca terá máximo inferior a:

```text
R$ 10.000
```

mas poderá ultrapassar esse valor se o catálogo tiver uma tarifa maior.

Não usar:

```javascript
Math.min(...)
```

aqui.

---

# 16. Valor inicial do range

Quando nenhum filtro estiver aplicado:

```javascript
input.value = ceiling;
```

O fato de o slider estar no teto significa:

```text
sem filtro efetivo de preço
```

Não considerar isso um filtro ativo.

---

# 17. Filtro em tempo real

Promo de Voos:

* `origin`: `change`
* `destination`: `change`
* `destinationType`: `change`
* `dateFrom`: `change`
* `dateTo`: `change`
* `price`: `input`

devem aplicar os filtros imediatamente.

O botão **Pesquisar** pode continuar existindo visualmente, mas a lista não pode depender dele para atualizar.

Para o range, se necessário, use `requestAnimationFrame` ou debounce curto para evitar renderizações excessivas.

---

# 18. Preços desconhecidos

Não tratar preço ausente como:

```text
0
```

Se nenhum filtro real de preço estiver ativo:

* oferta sem preço pode permanecer.

Se o usuário limitar explicitamente o preço:

* oferta sem preço numérico não pode ser considerada automaticamente compatível.

---

# P1 — Campanhas

Em `_catalog_ui.py`, quando:

```python
kind == "campanhas"
```

não renderizar:

```text
Ordenar por
```

Manter apenas:

```text
Destino
Contagem
Limpar filtros
Mostrar mais
```

Também garantir que `script.js` não dependa da existência do elemento de ordenação.

Ausência do select não pode produzir erro JavaScript.

---

# P1 — Não alterar o que já foi resolvido

Não refazer sem necessidade:

* catálogo único de Pacotes;
* modal de filtros;
* layout compacto de Promo de Voos;
* layout compacto de Campanhas;
* header;
* menu mobile;
* footer.

Somente alterar esses componentes se necessário para suportar os novos campos, especialmente:

```text
Tipo de destino
```

em Promo de Voos.

---

# Regeneração

Primeiro validar sintaxe:

```bash
python -m py_compile _sync_operator.py
python -m py_compile _build_ofertas.py
python -m py_compile _build_pacotes.py
python -m py_compile _catalog_ui.py
```

Depois identificar a ordem real do pipeline existente.

Se a ordem atual for:

```bash
python _sync_operator.py
python _build_ofertas.py
python _build_pacotes.py
```

executá-la nessa sequência.

Após gerar:

```bash
git diff --stat
git diff
```

Não assumir `script.js?v=25`.

Localize a versão atual e incremente o cache-buster apenas se `script.js` tiver sido alterado.

Faça o mesmo com CSS somente se CSS tiver realmente mudado.

Atualize todas as páginas/templates que referenciem o asset.

---

# Teste de idempotência

Após uma execução bem-sucedida, execute novamente o mesmo pipeline.

A segunda execução, sem mudança na fonte, não deve produzir alterações materiais.

Validar com:

```bash
git diff
```

Isso é obrigatório porque o processo será executado novamente no futuro.

---

# Validações obrigatórias

## Integridade das datas

Programaticamente verificar todas as Promo de Voos:

```text
return_date >= departure_date
```

quando ambos existirem.

Falhar a validação se houver qualquer registro contrário.

Procurar também no HTML gerado por:

```text
GMT-
GMT+
Horário Padrão
Invalid Date
NaN
undefined
null
```

quando esses textos não forem intencionais.

Nenhuma representação interna de Date pode vazar para o HTML.

---

## Pacotes

Validar uma oferta com várias saídas.

Exemplo conceitual:

```text
principal: agosto
outras: setembro e outubro
```

Aplicando:

```text
Saídas de: 01/09/2026
Saídas até: 30/09/2026
```

a oferta deve aparecer porque possui **qualquer saída** em setembro.

Depois aplicar agosto e outubro separadamente e confirmar o mesmo comportamento.

---

## Promo de Voos

Confirmar:

* Rio presente;
* São Paulo presente;
* GIG/SDU aceitos;
* GRU/CGH/VCP aceitos;
* `RIO` aceito como origem metropolitana;
* `SAO` aceito como origem metropolitana;
* destinos nacionais presentes;
* destinos internacionais presentes quando existirem na fonte;
* Tipo de destino funcional;
* horários apresentados somente quando existentes;
* aeroporto de destino apresentado somente quando existente;
* taxa específica por oferta;
* nenhum parcelamento herdado de Pacotes;
* slider com teto de pelo menos R$ 10.000;
* alteração do slider atualizando imediatamente;
* datas filtrando por qualquer saída válida;
* nenhuma volta anterior à ida.

---

## Comparação com a operadora

Escolher amostras reais diretamente do payload:

### Rio → nacional

Validar manualmente:

```text
origem
destino
ida
volta
horários
preço
taxa
lugares
```

### São Paulo → nacional

Mesma validação.

### Rio → internacional

Mesma validação.

### São Paulo → internacional

Mesma validação.

Comparar os valores diretamente contra a fonte antes de considerar o trabalho concluído.

Não validar somente contra o próprio JSON produzido pelo script.

---

# Campanhas

Confirmar:

```text
Ordenar por
```

não aparece.

Confirmar:

* filtro Destino funciona;
* contagem funciona;
* Mostrar mais funciona;
* console sem erros.

---

# Critérios de aceite

A tarefa somente está concluída quando:

* [ ] `data-dates` contém todas as saídas futuras conhecidas dos pacotes.
* [ ] `data-sort-date` contém somente a próxima saída válida.
* [ ] Filtro por data considera qualquer saída do pacote.
* [ ] Datas sem ano são normalizadas corretamente atravessando 2026/2027.
* [ ] Nenhuma data JavaScript bruta aparece no site.
* [ ] Nenhum voo possui volta anterior à ida.
* [ ] Promo de Voos não utiliza `PACOTES` como fonte.
* [ ] Promo de Voos utiliza o conjunto real de Bloqueios Aéreos.
* [ ] `RIO` e `SAO` são reconhecidos corretamente.
* [ ] Nacionais e internacionais vêm da mesma fonte.
* [ ] Existe filtro Todos/Nacionais/Internacionais.
* [ ] Aeroportos reais são preservados quando fornecidos.
* [ ] Horários são preservados quando fornecidos.
* [ ] Preço vem do bloqueio correto.
* [ ] Taxa vem do bloqueio correto.
* [ ] Não existe taxa genérica aplicada a todos os itens.
* [ ] Parcelamento só aparece se existir explicitamente na fonte do voo.
* [ ] Não existem duplicatas reais.
* [ ] Slider chega a pelo menos R$ 10.000.
* [ ] Filtro de preço responde durante o movimento.
* [ ] Campanhas não possui Ordenar por.
* [ ] Nenhum erro aparece no console.
* [ ] Segunda execução do pipeline é idempotente.

---

# Relatório final

Ao terminar, retornar:

```text
PROMO DE VOOS
Bloqueios encontrados na fonte:
Bloqueios Rio:
Bloqueios São Paulo:
Nacionais:
Internacionais:
Descartados por data inválida:
Duplicatas removidas:
Itens publicados:

VALIDAÇÃO
Voos com retorno < ida: 0
Datas JS brutas no HTML: 0
Itens sem preço:
Itens sem taxa:
Itens com horários:
Itens com aeroporto de destino:
Teto slider:
Filtro nacional/internacional: OK/FALHA
Filtro de datas: OK/FALHA
Filtro de preço: OK/FALHA

PACOTES
Total:
Com múltiplas saídas:
Teste filtro por saída adicional: OK/FALHA

CAMPANHAS
Ordenação removida: OK/FALHA
Filtro destino: OK/FALHA

IDEMPOTÊNCIA
Segunda execução gerou diff: SIM/NÃO
```

Não marcar a tarefa como concluída se ainda houver datas invertidas, valores comerciais cruzados entre produtos ou coleta incompleta dos bloqueios aéreos.
