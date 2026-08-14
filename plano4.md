# Corrigir preços, ordenação e filtro do catálogo de Pacotes

O site já está estruturalmente correto.

Não refaça:

* layout geral;
* catálogo único;
* cards;
* modal;
* header;
* footer;
* Promo de Voos;
* Campanhas;

salvo quando alguma pequena alteração for necessária para suportar esta correção.

O foco desta execução é exclusivamente:

1. corrigir a semântica dos preços dos pacotes;
2. impedir mistura entre preço de aéreo e preço de pacote;
3. corrigir valores exibidos incorretamente;
4. corrigir `data-sort-price`;
5. implementar corretamente menor preço e maior preço;
6. corrigir filtro por preço máximo;
7. validar programaticamente todos os 296+ pacotes.

**Não trate isso como simples bug de JavaScript.**

O problema atual começa na normalização/geração dos dados.

---

# 1. Auditoria obrigatória

Antes de alterar qualquer coisa:

```bash
git status
git diff
```

Inspecione especialmente:

```text
_sync_operator.py
_build_pacotes.py
_catalog_ui.py
script.js
```

e qualquer JSON/estrutura intermediária produzida durante a sincronização.

Localize exatamente:

* de onde vem o preço do aéreo;
* de onde vem o preço total do pacote;
* de onde vem a parcela;
* de onde vem a quantidade de parcelas;
* de onde vêm as taxas;
* como `data-sort-price` é gerado;
* como o JavaScript lê esse atributo;
* como menor/maior preço são comparados.

Não aplique apenas correção visual no HTML final.

Corrija a origem dos dados.

---

# 2. Bug concreto que precisa ser resolvido

Hoje existem cards semanticamente impossíveis.

Exemplos atuais:

```text
São Paulo GP Fórmula 1 2026

Aéreo:
de R$ 846
por R$ 446

Pagamento:
10x R$ 759

Total:
R$ 446
```

Outro:

```text
GP Fórmula 1 — Heineken Village

Aéreo:
por R$ 612

Pagamento:
10x R$ 1.066

Total:
R$ 612
```

Outro:

```text
GP Fórmula 1 — Pacote completo

Aéreo:
por R$ 633

Pagamento:
10x R$ 1.068

Total:
R$ 633
```

Isso indica que o preço promocional **do trecho aéreo** está sendo reutilizado indevidamente como:

```text
total do pacote
data-sort-price
```

Corrigir essa associação.

---

# 3. Separar semanticamente todos os valores

A estrutura normalizada de um pacote deve possuir campos separados.

Conceitualmente:

```python
{
    "package_total_price": None,
    "installment_count": None,
    "installment_value": None,

    "airfare_original_price": None,
    "airfare_sale_price": None,

    "fees": None,

    "currency": "BRL",
    "price_source": None
}
```

Não é obrigatório utilizar exatamente esses nomes.

É obrigatório existir a separação lógica.

Nunca utilizar uma variável genérica:

```python
price
```

para representar ora:

* aéreo;
* pacote;
* parcela;
* total;
* taxa.

---

# 4. Definição do preço canônico do catálogo

Criar um conceito único:

```text
PACKAGE SORT PRICE
```

ou equivalente.

Ele representa:

> o menor preço total efetivamente anunciado para adquirir o pacote, por pessoa, sem incluir taxas quando as taxas forem apresentadas separadamente.

Este será o único valor utilizado para:

* ordenar por menor preço;
* ordenar por maior preço;
* filtro de preço máximo;
* `data-sort-price`.

---

# 5. O preço do aéreo NÃO é preço do pacote

Exemplo:

```text
Aéreo de R$ 1.012 por R$ 612
```

significa apenas:

```python
airfare_original_price = 1012
airfare_sale_price = 612
```

Isso **não significa**:

```python
package_total_price = 612
```

quando o produto também contém:

* hospedagem;
* transfers;
* ingresso;
* passeio;
* serviços;
* outros componentes.

O valor R$ 612 pode continuar aparecendo na descrição:

```text
✈ Saída do Rio de Janeiro (SDU):
aéreo de R$ 1.012 por R$ 612
```

mas nunca deve alimentar o total do pacote.

---

# 6. Fonte preferencial para `package_total_price`

Determinar o preço total utilizando esta ordem de confiança.

## Prioridade 1 — total explícito da fonte

Se os dados originais da oferta possuírem campo inequivocamente equivalente a:

```text
valor total
preço do pacote
total por pessoa
a partir de
valor do pacote
```

utilizar esse valor.

---

## Prioridade 2 — parcela explicitamente pertencente ao pacote

Se houver:

```text
10x de R$ 759
```

e a fonte deixar inequivocamente claro que esse parcelamento corresponde ao **pacote completo**, pode existir:

```python
installment_count = 10
installment_value = 759
```

Se não houver total explícito, pode ser calculado:

```python
package_total_price = installment_count * installment_value
```

**somente quando a fonte deixar claro que não existe entrada, parcela diferenciada, juros ou composição especial.**

Exemplo:

```text
10 x 759 = 7590
```

Então:

```text
package_total_price = 7590
```

e nunca `446`, caso R$ 446 seja apenas o aéreo.

---

# 7. Não inventar total quando o parcelamento for ambíguo

Se houver algo como:

```text
entrada + 10 parcelas
sinal + parcelas
parcelas a partir de
financiamento
parcelamento com juros
```

não calcular:

```python
parcelas * valor
```

como se fosse necessariamente o total.

Nesse caso:

* preserve o valor explícito da fonte;
* ou deixe `package_total_price = None`.

Não invente preço para fazer o filtro funcionar.

---

# 8. Não misturar registros diferentes

Investigue especificamente se o bug atual vem de:

* arrays paralelos;
* índices;
* reutilização de variável;
* associação por destino;
* associação por imagem;
* associação por título parcialmente igual;
* associação entre Promo Voo e Pacote;
* merge de objetos;
* `dict.update`;
* fallback genérico.

Preços devem acompanhar a identidade da oferta.

Exemplo:

```text
GP Fórmula 1
GP Fórmula 1 — Heineken
GP Fórmula 1 — pacote completo
```

são produtos diferentes.

Não permitir que:

```text
preço do aéreo da oferta A
```

seja associado ao:

```text
parcelamento do pacote B
```

---

# 9. Definir fonte do preço

Durante a normalização, adicionar internamente algo equivalente a:

```python
price_source = "explicit_total"
```

ou:

```python
price_source = "installment_calculated"
```

ou:

```python
price_source = "unknown"
```

Isso não precisa aparecer para o visitante.

Serve para auditoria e futuras sincronizações.

Não utilizar:

```text
airfare_sale
```

como fonte válida de `package_total_price`.

---

# 10. Garantir coerência do card

Um card que exibe:

```text
10x a partir de R$ 759
```

não pode imediatamente abaixo dizer:

```text
Total a partir de R$ 446
```

quando ambos representam o mesmo pacote.

Criar validação obrigatória.

Quando existir:

```python
installment_count
installment_value
package_total_price
```

calcular:

```python
calculated = installment_count * installment_value
```

e comparar com o total.

---

# 11. Tolerância

Devido a arredondamentos, aceitar pequena diferença.

Exemplo:

```python
difference = abs(
    package_total_price -
    installment_count * installment_value
)
```

Permitir algo equivalente a:

```text
até R$ 5
ou
até 1%
```

Escolher uma regra simples e documentada.

Diferenças enormes não podem ser aceitas.

Exemplo:

```text
10 × 759 = 7590

Total exibido = 446
```

deve obrigatoriamente falhar.

---

# 12. Não corrigir inconsistência silenciosamente sem entender a fonte

Quando houver conflito:

```text
total explícito
versus
parcelamento
```

volte à oferta original e identifique qual informação pertence ao pacote.

Não simplesmente escolher:

```python
max(total, installments_total)
```

ou:

```python
min(...)
```

Isso apenas esconderia o bug.

---

# 13. Cards sem preço confiável

Quando não for possível determinar um preço total de pacote confiável:

```python
package_total_price = None
```

No card, utilizar algo como:

```text
Consulte o valor
```

ou preservar a redação comercial real da fonte.

Não usar:

```text
R$ 0
```

Não usar preço do aéreo como substituto.

---

# 14. Alterar `data-sort-price`

Cada card deve receber somente um valor numérico canônico.

Exemplo:

```html
data-sort-price="7590.00"
```

Não:

```html
data-sort-price="R$ 7.590,00"
```

Não:

```html
data-sort-price="759"
```

se `759` for apenas a parcela.

Não:

```html
data-sort-price="446"
```

se `446` for apenas o aéreo.

O atributo representa exclusivamente:

```text
package_total_price
```

---

# 15. Não extrair o preço novamente do texto no browser

Se o backend/build já determinou:

```text
data-sort-price
```

o JavaScript deve utilizar esse número diretamente.

Não fazer parsing de:

```text
.innerText
```

do card para descobrir preço.

Não procurar:

```text
R$
```

no DOM.

Isso é especialmente perigoso porque o mesmo card possui:

* aéreo original;
* aéreo promocional;
* parcela;
* total;
* taxa.

---

# 16. Ordenação deve possuir três estados explícitos

No controle `Ordenar por`, utilizar:

```text
Data
Menor preço
Maior preço
```

Não utilizar apenas:

```text
Preço
```

porque é ambíguo.

---

# 17. Menor preço

Implementação conceitual:

```javascript
items.sort((a, b) => {
    const pa = itemPrice(a);
    const pb = itemPrice(b);

    if (pa == null && pb == null) return tieBreak(a, b);
    if (pa == null) return 1;
    if (pb == null) return -1;

    if (pa !== pb) return pa - pb;

    return tieBreak(a, b);
});
```

Resultado esperado:

```text
1.650
1.780
2.080
2.180
2.270
...
```

e não baseado em:

```text
valor da parcela
ou
valor do aéreo
```

---

# 18. Maior preço

Implementação conceitual:

```javascript
items.sort((a, b) => {
    const pa = itemPrice(a);
    const pb = itemPrice(b);

    if (pa == null && pb == null) return tieBreak(a, b);
    if (pa == null) return 1;
    if (pb == null) return -1;

    if (pa !== pb) return pb - pa;

    return tieBreak(a, b);
});
```

Importante:

**itens sem preço ficam no final também no modo decrescente.**

Não deixar `NaN`, `Infinity` ou `0` fazer cards sem preço aparecerem no início.

---

# 19. Desempate determinístico

Quando dois pacotes possuírem mesmo preço, desempatar por:

1. próxima saída;
2. título.

Isso evita mudança aleatória entre renderizações.

---

# 20. Ordenar a coleção inteira

A página utiliza `Mostrar mais`.

A ordenação não pode ser aplicada apenas aos cards atualmente visíveis.

Fluxo correto:

```text
TODOS OS PACOTES
        ↓
APLICAR FILTROS
        ↓
ORDENAR TODOS OS RESULTADOS
        ↓
PAGINAR / MOSTRAR PRIMEIROS N
```

Não:

```text
mostrar 20
↓
ordenar só esses 20
```

Ao alterar ordenação:

```text
visibleLimit = initialLimit
```

e renderizar novamente a coleção ordenada.

---

# 21. Filtro de preço máximo

O modal deve utilizar exatamente o mesmo:

```text
package_total_price
```

da ordenação.

Se:

```text
Preço máximo = R$ 3.000
```

devem aparecer somente pacotes cujo:

```python
package_total_price <= 3000
```

---

# 22. Pacotes sem preço e filtro ativo

Sem filtro de preço:

```text
pacotes sem preço podem aparecer
```

Com filtro de preço ativo:

```text
pacotes sem package_total_price devem ser excluídos
```

porque não é possível afirmar que atendem ao limite.

---

# 23. Teto do slider

O teto deve ser calculado sobre:

```text
package_total_price
```

e não sobre:

* aéreo;
* parcela;
* taxa.

Exemplo:

```javascript
const validPrices = items
  .map(itemPrice)
  .filter(Number.isFinite);

const catalogMax = Math.max(...validPrices);
```

Arredondar de forma apropriada.

Pode manter teto mínimo de R$ 10.000 caso essa regra já tenha sido adotada.

Mas para Pacotes, se existirem produtos de:

```text
R$ 30.000
R$ 50.000
```

o range deve chegar até eles.

---

# 24. Atualizar visualmente o preço principal

Hoje o preço de maior destaque no card é frequentemente a parcela:

```text
10x a partir de R$ 759
```

Isso dificulta perceber a ordenação por preço total.

Reestruture a hierarquia visual sem redesenhar o card.

Preferência:

```text
A partir de R$ 7.590
10x de R$ 759
+ taxas
```

O **total do pacote deve ser o valor visual principal**.

A parcela deve ser secundária.

Isso torna evidente por que:

```text
R$ 7.590
```

vem antes de:

```text
R$ 10.660
```

na ordenação crescente.

---

# 25. Não alterar condições comerciais

Se a fonte utiliza explicitamente:

```text
10x a partir de R$ ...
```

preserve a redação adequada.

Mas não permita que o valor parcelado tenha mais destaque que o total a ponto de tornar a ordenação incompreensível.

Não invente:

* juros;
* entrada;
* desconto;
* taxa;
* parcelamento.

---

# 26. Separar taxas

As taxas não entram no `package_total_price` quando o anúncio comercial apresenta:

```text
R$ X + taxas
```

Armazenar separadamente:

```python
fees
```

Exemplo:

```text
Pacote: R$ 7.590
Taxas: R$ 119
```

Ordenar por:

```text
7.590
```

e não:

```text
7.709
```

porque o preço anunciado é "a partir de R$ 7.590 + taxas".

Caso a fonte forneça um preço final já com taxas incluídas, preservar essa semântica.

---

# 27. Parser monetário brasileiro

Centralizar o parser monetário.

Precisa interpretar corretamente:

```text
R$ 446
R$ 446,00
R$ 1.066
R$ 1.066,00
R$ 13.370,00
R$ 9.511,75
```

como:

```python
446.00
446.00
1066.00
1066.00
13370.00
9511.75
```

Não utilizar:

```python
float(text.replace(",", "."))
```

sem tratar separadores de milhar.

---

# 28. Criar função única

Preferencialmente centralizar em algo equivalente a:

```python
parse_brl()
```

e utilizar a mesma função em toda normalização.

Evitar implementações diferentes em:

```text
_sync_operator.py
_build_pacotes.py
```

---

# 29. Testes de parser obrigatórios

Adicionar/testar no mínimo:

```text
"R$ 446"       -> 446.00
"R$ 446,00"    -> 446.00
"R$ 1.066"     -> 1066.00
"R$ 1.066,00"  -> 1066.00
"R$ 9.511,75"  -> 9511.75
"13.370,00"    -> 13370.00
```

---

# 30. Não confundir ponto decimal com milhar

Esse ponto é crítico.

No padrão brasileiro:

```text
1.066
```

normalmente significa:

```text
mil e sessenta e seis
```

e não:

```text
1 real e 6 centavos
```

A normalização interna deve usar:

```text
1066.00
```

---

# 31. Auditoria automática de todos os cards

Após gerar Pacotes, criar uma validação programática temporária ou permanente que percorra todos os produtos.

Para cada pacote, imprimir algo semelhante a:

```text
TITLE
package_total_price
installment_count
installment_value
installment_total
airfare_sale_price
fees
price_source
```

---

# 32. Detectar inconsistências

Marcar como erro quando:

```python
package_total_price <= 0
```

ou:

```python
installment_count <= 0
```

ou:

```python
installment_value <= 0
```

quando esses campos existirem.

E especialmente:

```python
abs(
    package_total_price -
    installment_count * installment_value
) > tolerance
```

quando ambos supostamente representarem o mesmo preço.

---

# 33. Detectar preço do aéreo usado como total

Criar validação específica:

Se o pacote contém:

```python
airfare_sale_price
```

e:

```python
package_total_price == airfare_sale_price
```

ao mesmo tempo em que o produto contém:

* hotel;
* serviço;
* transfer;
* ingresso;
* outros componentes;

isso deve gerar **warning/erro de validação**, porque é altamente suspeito.

Não bloqueie apenas pacotes genuinamente aéreos; esta regra é para a página de Pacotes.

---

# 34. Casos de regressão obrigatórios

Validar explicitamente os cards atuais:

```text
São Paulo GP Fórmula 1 2026
São Paulo GP Fórmula 1 2026 — Setor Heineken Village Estrela
São Paulo GP Fórmula 1 2026 — Pacote completo
SÃO PAULO (CGH) — Show Ed Sheeran
```

Nenhum deles pode continuar com combinações equivalentes a:

```text
10x 759 / total 446
10x 1066 / total 612
10x 1068 / total 633
10x 254 / total 678
```

sem que a fonte original confirme explicitamente essa estrutura.

Volte ao registro original de cada um e corrija o mapeamento.

---

# 35. Validar também pacotes que já funcionavam

Não quebrar os cards manuais/antigos.

Usar como casos de regressão:

```text
Salvador
10x R$ 165
Total R$ 1.650
```

```text
Porto de Galinhas
12x R$ 225
Total R$ 2.700
```

```text
João Pessoa
10x R$ 227
Total R$ 2.270
```

Eles devem permanecer semanticamente consistentes.

---

# 36. Teste de ordenação automatizado

Depois da geração, obter todos os:

```text
data-sort-price
```

válidos.

Para "Menor preço", verificar programaticamente:

```python
prices == sorted(prices)
```

Para "Maior preço":

```python
prices == sorted(prices, reverse=True)
```

Ignorar `None` na comparação e garantir que esses elementos fiquem no final.

Não validar apenas visualmente cinco cards.

---

# 37. Validar o DOM após filtro e sort

No navegador automatizado:

1. abrir `pacotes.html`;
2. selecionar `Menor preço`;
3. coletar `data-sort-price` dos cards mostrados;
4. confirmar ordem crescente;
5. selecionar `Maior preço`;
6. confirmar ordem decrescente;
7. aplicar preço máximo;
8. confirmar que nenhum card visível ultrapassa o teto;
9. clicar em `Mostrar mais`;
10. confirmar que a ordenação continua correta.

---

# 38. Validar interação filtro + ordenação

Testar:

```text
Destino = São Paulo
Ordenação = Menor preço
```

Depois:

```text
Preço máximo = R$ 5.000
```

Depois:

```text
Ordenação = Maior preço
```

Todos os resultados devem continuar dentro do filtro e trocar somente de ordem.

---

# 39. Não perder filtros ao ordenar

Quando o usuário mudar:

```text
Menor preço
→
Maior preço
```

não limpar:

* origem;
* destino;
* datas;
* tipo;
* preço máximo.

Ordenação e filtros são estados independentes.

---

# 40. Atualizar contador

Após:

* filtro;
* ordenação;
* limpar filtro;

o contador deve continuar refletindo a coleção filtrada total.

Exemplo:

```text
296 pacotes encontrados
```

não representa necessariamente o número atualmente renderizado por `Mostrar mais`, mas o total correspondente aos filtros ativos.

---

# 41. Não usar preço formatado como chave

O JS nunca deve comparar:

```text
"R$ 900"
"R$ 1.200"
```

como strings.

Converter/receber sempre:

```text
900
1200
```

---

# 42. Não usar parcela como fallback silencioso

Se `package_total_price` estiver ausente, não fazer automaticamente:

```javascript
price = installmentValue;
```

Isso produziria exatamente o tipo de problema atual.

A parcela não é o preço total.

---

# 43. Não usar aéreo como fallback silencioso

Também proibido:

```python
package_total_price = (
    package_total_price
    or airfare_sale_price
)
```

para Pacotes.

Se não houver preço de pacote:

```text
Consulte
```

é melhor do que um valor incorreto.

---

# 44. Alterar o gerador, não somente HTML

A próxima sincronização mensal deve continuar correta.

Portanto, se:

```text
_sync_operator.py
```

gera dados errados e:

```text
_build_pacotes.py
```

apenas renderiza, corrigir o sync.

Se o sync estiver correto e o build estiver sobrescrevendo os campos, corrigir o build.

Se ambos contribuírem para o problema, corrigir ambos.

---

# 45. Regenerar

Validar sintaxe:

```bash
python -m py_compile _sync_operator.py
python -m py_compile _build_pacotes.py
python -m py_compile _catalog_ui.py
```

Executar a ordem real do pipeline já utilizada no projeto.

Exemplo, somente se essa continuar sendo a ordem correta:

```bash
python _sync_operator.py
python _build_ofertas.py
python _build_pacotes.py
```

---

# 46. Cache busting

Se `script.js` mudar:

* identificar versão atual;
* incrementar cache-buster.

Não assumir número fixo.

Se CSS não mudar:

* não alterar sua versão sem necessidade.

---

# 47. Teste de idempotência

Depois da primeira geração:

```bash
git diff
```

Executar o pipeline novamente.

Sem alteração na fonte, a segunda execução não deve gerar alterações materiais.

---

# 48. Critérios obrigatórios de aceite

A tarefa só estará concluída quando:

* [ ] Preço do aéreo estiver separado do preço do pacote.
* [ ] Parcela estiver separada do total.
* [ ] Taxa estiver separada do total.
* [ ] `package_total_price` possuir semântica única.
* [ ] `data-sort-price` usar exclusivamente `package_total_price`.
* [ ] Menor preço ordenar numericamente em ordem crescente.
* [ ] Maior preço ordenar numericamente em ordem decrescente.
* [ ] Pacotes sem preço permanecerem no final em ambas as ordenações.
* [ ] Filtro de preço máximo utilizar o mesmo preço da ordenação.
* [ ] O filtro funcionar sobre a coleção inteira.
* [ ] `Mostrar mais` preservar a ordenação.
* [ ] O total do pacote tiver maior destaque visual que a parcela.
* [ ] Nenhum preço seja comparado como string.
* [ ] Valores BRL sejam parseados corretamente.
* [ ] Nenhum preço do aéreo seja usado como fallback de pacote.
* [ ] Nenhuma parcela seja usada como preço total sem regra explícita.
* [ ] Cards GP Fórmula 1 estejam corrigidos.
* [ ] Card Ed Sheeran esteja corrigido.
* [ ] Cards antigos consistentes continuem corretos.
* [ ] Nenhum card exiba combinação comercial matematicamente contraditória.
* [ ] Filtros existentes continuem funcionando.
* [ ] Segunda execução seja idempotente.

---

# 49. Relatório final obrigatório

Retornar:

```text
AUDITORIA DE PREÇOS

Pacotes analisados:
Pacotes com preço total confiável:
Pacotes sem preço total:
Pacotes com parcelamento:
Pacotes com preço de aéreo:
Inconsistências preço/parcela encontradas:
Inconsistências corrigidas:
Ofertas mantidas como "Consulte":

ORDENAÇÃO

Menor preço:
Primeiros 10 valores:
Resultado: OK/FALHA

Maior preço:
Primeiros 10 valores:
Resultado: OK/FALHA

Pacotes sem preço no final:
OK/FALHA

FILTRO

Preço máximo testado:
Maior preço encontrado entre os resultados:
Resultado: OK/FALHA

REGRESSÕES

GP Fórmula 1:
OK/FALHA

Heineken Village:
OK/FALHA

GP pacote completo:
OK/FALHA

Ed Sheeran:
OK/FALHA

Salvador:
OK/FALHA

Porto de Galinhas:
OK/FALHA

João Pessoa:
OK/FALHA

IDEMPOTÊNCIA

Segunda execução gerou diff:
SIM/NÃO
```

---

# 50. Instrução final

Não considere a tarefa concluída apenas porque a ordem visual parece correta.

O objetivo é garantir que:

```text
PREÇO EXIBIDO
=
PREÇO SEMANTICAMENTE CORRETO DO PACOTE
=
PREÇO USADO NA ORDENAÇÃO
=
PREÇO USADO NO FILTRO
```

O preço promocional do aéreo deve permanecer somente como informação complementar quando fizer parte de um pacote.

Se a fonte não permitir determinar com segurança o preço total de um produto, apresente:

```text
Consulte o valor
```

em vez de publicar ou ordenar usando um preço incorreto.
