# Inventário inicial de supply chain

## Escopo

Inventário dos componentes que participam do build local, do sync estático e
da futura imagem dinâmica. Esta task fixa somente a dependência Python opcional
já usada pelo workflow; scans de vulnerabilidade, SBOM, provenance e pins por
SHA ficam nas tasks seguintes.

## Componentes observados

| Componente | Local | Versão atual | Estado |
|---|---|---|---|
| Python runtime | Dockerfile | `3.12.7-slim-bookworm` | tag fixa; digest pendente |
| Pillow | workflow de sync | `11.3.0` | lockfile criado em `requirements-dev.txt` |
| Python stdlib | backend/scripts | versão do runtime | sem dependências externas adicionais observadas |
| Node runtime | checks locais | ambiente do runner | não é dependência de runtime; versão do CI pendente |
| GitHub Actions checkout | workflow diário | `@v7` | versão major fixa; pin SHA pendente |
| GitHub Actions setup-python | workflow diário | `@v7` | versão major fixa; pin SHA pendente |
| Imagem Docker | Dockerfile | `python:3.12.7-slim-bookworm` | digest/SBOM pendentes |
| Fontes/Font Awesome | HTML público | CDN externa | inventário/licença e SRI pendentes |

## Política provisória

1. Dependências Python devem ser declaradas em arquivo versionado, com versão
   exata e revisão de atualização.
2. O workflow deve instalar o arquivo, não repetir versões em comandos
   dispersos.
3. Actions, imagem base, fontes e scripts externos ainda precisam de pin por
   digest/SHA ou justificativa registrada.
4. Uma vulnerabilidade crítica/alta não é ignorada; bloqueia release ou exige
   exceção com owner, mitigação e expiração.
5. Nenhum segredo é dependência, fixture ou artefato de build.

## Gaps encaminhados

- EPIC-21.2: SBOM e scan da imagem/dependências.
- EPIC-21.3: severidade, SLA e política de exceções.
- EPIC-21.4: secret scan e proveniência/tamper test.
- EPIC-15.2: digest, multi-stage e hardening da imagem.
- EPIC-17.2: build reproduzível e artifact manifest.

## Verificação de reprodutibilidade

O arquivo `requirements-dev.txt` é a única fonte da versão Pillow usada pelo
workflow diário. A resolução completa/transitiva e os hashes do ambiente devem
ser produzidos pelo pipeline de supply chain antes de qualquer release.
