# Arquitetura dinâmica local

## Escopo

Esta etapa adiciona um backend administrável apenas para desenvolvimento local.
Produção continua sendo o site estático publicado no GitHub Pages; não há deploy,
alteração de DNS, segredo de produção ou banco remoto neste fluxo.

## Componentes

- `backend/app.py`: servidor HTTP da API pública e do admin local.
- `backend/storage.py`: SQLite, migrations e transações.
- `backend/providers.py`: contrato de provider, adapter `CativaAdapter` e upsert.
- `backend/presentation.py`: renderização segura dos pacotes manuais no mesmo
  formato de card usado pelo catálogo.
- `api-catalog.js`: tenta a API local e mantém os fragments HTML versionados como
  fallback quando a API não existe ou está indisponível.
- `admin/`: login com cookie assinado, CSRF e CRUD de pacotes manuais.
- `data/operator-sync.json`: snapshot versionado que continua sendo a fonte do
  pipeline estático existente.

## Fluxos

### Operadora → catálogo local

1. `_sync_operator.py` coleta e normaliza o snapshot da operadora.
2. O pipeline gera `data/generated/*.html` e atualiza `data/operator-sync.json`.
3. Com `--persist-local`, o snapshot também é importado no SQLite por upsert
   `(provider, external_id)`.
4. Um snapshot vazio ou uma falha de importação não remove o último conjunto
   persistido; a transação é revertida.

Exemplo:

```bash
python _sync_operator.py --from-json --persist-local
```

### API → site

As páginas preservam os cards HTML gerados. Quando executadas pelo backend local,
`api-catalog.js` consulta `/api/offers` e substitui os catálogos pelos registros
publicados do banco. Se a requisição falhar, o HTML original permanece visível.

### Admin local

O admin gerencia somente `source=manual`. Ofertas do provider são somente leitura
no admin. Publicar, despublicar ou arquivar um pacote manual atualiza o status no
SQLite; a API pública expõe apenas registros `published`.

## Modelo de dados

`offers` guarda identidade do provider, classificação de catálogo, ordenação,
status, payload normalizado em `data_json` e o fragment renderizado. `sync_runs`
registra cada importação. A migration é aplicada automaticamente na inicialização.

## Paridade e limites conhecidos

- O HTML estático continua preservando SEO, URLs, CTAs, filtros e analytics quando
  a API não está disponível.
- O backend local serve o mesmo diretório do site; ele não é um servidor de
  produção e não inclui TLS ou exposição pública.
- O admin inicial cobre pacotes manuais. Promoções de voo e campanhas permanecem
  sob controle do provider.
- A migração futura para hospedagem dinâmica exige revisão independente de
  autenticação, backups, observabilidade, rate limiting, TLS, secrets e rollback.

## Verificação local

```bash
copy .env.example .env
docker compose config
docker compose up -d --build
curl http://127.0.0.1:8080/health
python -m unittest discover -s tests -v
```

Para desligar sem remover os dados:

```bash
docker compose down
```

`docker compose down -v` remove o volume do SQLite e exige confirmação explícita.
