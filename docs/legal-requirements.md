# Inventário de requisitos legais

Este arquivo é uma lista de fornecimento e revisão. Não cria dados
empresariais, não define base legal e não é conteúdo jurídico publicado.
Qualquer item sem fonte oficial deve permanecer bloqueado com
`VALIDAÇÃO JURÍDICA NECESSÁRIA`.

## Matriz de fornecimento

| Item necessário | Fonte exigida | Owner | Estado atual | Bloqueia publicação |
|---|---|---|---|---|
| Nome fantasia e marca | aprovação da empresa | empresa + produto | Viajando com a Babi observado | sim, se divergente |
| Razão social | documento oficial da empresa | empresa/jurídico | não fornecido nesta task | sim |
| CNPJ | documento oficial da empresa | empresa/jurídico | não fornecido nesta task | sim |
| Endereço empresarial | decisão empresarial/jurídica | empresa/jurídico | não fornecido nesta task | avaliar juridicamente |
| Cadastur/licenças | registro oficial vigente | empresa/jurídico | referência existente precisa conferência | sim se publicado |
| Canal de contato | número/e-mail oficial | empresa | WhatsApp existe no site; confirmação pendente | sim se divergente |
| Encarregado/canal LGPD | decisão da empresa + jurídico | empresa/jurídico | não fornecido | sim |
| Política de privacidade | matriz técnica + revisão profissional | jurídico | página existe; revisão pendente | sim |
| Política de cookies | inventário de trackers + revisão | jurídico | banner/Consent Mode existem; conteúdo pendente | sim |
| Termos de uso | regras comerciais aprovadas | jurídico | não identificado | sim |
| Condições comerciais | operação/financeiro + jurídico | empresa | não documentado | sim |
| Pagamento e parcelamento | operação/financeiro | empresa | não documentado no admin atual | sim |
| Cancelamento/reembolso | operadora/financeiro + jurídico | empresa/jurídico | não documentado | sim |
| Disponibilidade/preço | operação/provider | empresa | preços dinâmicos observados | sim, com aviso correto |
| Responsabilidade por dados da operadora | contratos/provider + jurídico | empresa/jurídico | não fornecido | sim |
| Direitos autorais/licença de imagens | origem/contrato de cada asset | empresa | inventário pendente | sim para mídia nova |

## Páginas e componentes

| Superfície | Conteúdo esperado | Estado permitido antes da aprovação |
|---|---|---|
| Rodapé | links para privacidade, cookies, termos e contato | somente links existentes/revisados |
| `privacidade.html` | tratamento real, retenção, terceiros e direitos | pode permanecer, mas não declarar fatos não confirmados |
| Política de cookies | categorias, fornecedores, finalidade e revogação | não publicar como final sem validação |
| Termos de uso | uso do site, ofertas, limitações e contato | não publicar placeholder |
| Condições comerciais | preço, disponibilidade, pagamento, cancelamento e reembolso | não publicar placeholder |
| Página de pacote | preço/validade, operadora, responsabilidade e CTA | exibir aviso aprovado sobre alteração/disponibilidade |
| Formulário/WhatsApp | finalidade e canal de atendimento | não adicionar coleta persistente sem matriz |

## Placeholders seguros

Placeholders podem existir apenas em configuração de desenvolvimento ou em
checklist interno, nunca no frontend de produção. Exemplos de campos que devem
falhar no gate de conteúdo quando vazios:

```text
LEGAL_COMPANY_NAME
LEGAL_CNPJ
LEGAL_BUSINESS_ADDRESS
LEGAL_CONTACT_EMAIL
LEGAL_DPO_CONTACT
LEGAL_TERMS_VERSION
LEGAL_PRIVACY_VERSION
LEGAL_COOKIES_VERSION
LEGAL_CANCELLATION_POLICY
LEGAL_REFUND_POLICY
```

Os valores acima não devem ser preenchidos com dados inventados. O pipeline de
produção futuro deve emitir erro sem imprimir secrets ou dados incompletos.

## Critérios de publicação

1. Cada página tem owner, versão, data de revisão e fonte.
2. Não há placeholder obrigatório, CNPJ, endereço ou política inventada.
3. O texto coincide com a matriz de dados e com o comportamento do tracker.
4. Alteração comercial/jurídica exige aprovação rastreável e release notes.
5. Itens sem decisão recebem exatamente `VALIDAÇÃO JURÍDICA NECESSÁRIA` e
   mantêm o gate em FAIL.

## Pendências para a empresa/jurídico

- fornecer dados empresariais oficiais;
- definir políticas comerciais e de cancelamento/reembolso;
- revisar privacidade/cookies/termos;
- confirmar operadores, contratos e direitos de imagens;
- nomear owner e aprovador de cada página;
- aprovar versões antes de qualquer publicação dinâmica.
