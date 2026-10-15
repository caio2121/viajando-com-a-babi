# SEO, indexação e metadados

## Controles implementados

As seis páginas legais geradas possuem:

- `<title>` específico com a marca;
- `meta name="description"` específico;
- canonical absoluto para `https://viajandocomababi.com.br/<rota>`;
- Open Graph e Twitter Card derivados da mesma URL e descrição;
- `lang="pt-BR"`, viewport e favicon existente;
- um único `h1`.

`sitemap.xml` inclui as seis URLs legais. Nenhuma delas contém `noindex`. O `robots.txt` mantém a referência ao sitemap e não bloqueia os documentos legais.

## Integridade interna

O gerador usa `config/site-config.json` para a base pública, marca e canais, reduzindo risco de canonical ou contato divergente. A suíte estática verifica existência das páginas, descriptions, canonicals, ausência de marcadores provisórios, quantidade de `h1` e cobertura do sitemap.

## Observações

- O sitemap representa URLs canônicas, não todos os arquivos HTML existentes em subdiretórios.
- Disponibilidade HTTP, indexação efetiva e dados de Search Console dependem do ambiente publicado e não são garantidos por um arquivo local.
- A página de verificação do Google não é uma página de conteúdo e não foi incluída no sitemap.
