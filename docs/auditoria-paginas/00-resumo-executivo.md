# Auditoria das páginas — resumo executivo

**Projeto:** Viajando com a Babi  
**Snapshot auditado:** 14 de outubro de 2026  
**Escopo:** páginas HTML públicas no repositório, navegação, documentos legais, consentimento, formulário, SEO e acessibilidade básica.

## Resultado

O site é um conjunto de páginas HTML estáticas que direciona o atendimento para WhatsApp e e-mail. As seis páginas legais que estavam provisórias foram substituídas por conteúdo publicável, com layout compartilhado, `title`, `description`, canonical, links relacionados e inclusão no sitemap:

- `condicoes-comerciais.html`;
- `cancelamento-reembolso.html`;
- `contato-lgpd.html`;
- `termos-de-uso.html`;
- `cookies.html`;
- `privacidade.html`.

As páginas descrevem apenas o que foi observado no código ou o que precisa ser confirmado na proposta/contrato. Não foram adicionados percentuais, prazos, taxas, garantias ou regras comerciais não confirmados.

## Alterações entregues

1. Gerador `_build_legal_pages.py` para manter as seis páginas com os mesmos partials e metadados.
2. Conteúdo legal factual, com limites explícitos para decisões comerciais e validação jurídica.
3. Consentimento Google alinhado ao código, com revogação em `cookies.html`.
4. Validação nativa reativada no formulário de viagem.
5. Skip link, foco visível e estilos para leitura das páginas legais.
6. Canonicals, descriptions e URLs legais no `sitemap.xml`.
7. Testes stdlib em `tests/test_site_audit.py` e verificação manual no navegador.

## Pendências fora do código

Ainda exigem decisão da empresa e/ou revisão profissional: prazos de retenção por categoria, identificação formal do encarregado, regras específicas de fornecedores, taxas e prazos de cancelamento, inventário de operadores de dados e confirmação de registros comerciais aplicáveis. Essas pendências estão detalhadas em [08-fontes-e-pendencias.md](08-fontes-e-pendencias.md) e não foram mascaradas como fatos nas páginas públicas.

## Evidências principais

- Testes automatizados: `python -m unittest discover -s tests -v` — 42 testes aprovados no ciclo de implementação.
- Navegador local: recusa, aceite e revogação do consentimento; formulário vazio inválido e sem abertura de nova aba.
- Implementação: `_build_legal_pages.py`, `_partials/ga4.html`, `index.html`, `style.css` e `sitemap.xml`.
- Matriz de rastreabilidade: [07-matriz-rastreabilidade.md](07-matriz-rastreabilidade.md).
