# Viajando com a Babi — Site Oficial

Site estático de conversão para a agência de viagens **Viajando com a Babi**, focado em direcionar visitantes ao WhatsApp e ao Instagram.

**URL de produção:** https://viajandocomababi.com.br/

---

## Visão geral

| Item | Detalhe |
|---|---|
| Tipo | Site estático (single-page) |
| Tecnologias | HTML5, CSS3, JavaScript puro (ES6+) |
| Dependências externas | Google Fonts (Nunito + Dancing Script) · Font Awesome 6 |
| Hospedagem | GitHub Pages — branch `main`, raiz `/` |
| Responsividade | Mobile-first (320 px → 1440 px+) |

---

## Estrutura do repositório

```
/
├── index.html          # Página principal (única)
├── style.css           # Estilos mobile-first
├── script.js           # JavaScript: scroll-reveal, navbar, smooth-scroll
├── README.md           # Este arquivo
├── .gitignore
├── assets/
│   └── Logo viajando com a Babi - fundo transparente.png
├── fotos/
│   └── WhatsApp Image 2026-02-23 at 21.49.58.jpeg   # Foto da Babi
├── pacotes/
│   ├── WhatsApp Image 2026-02-11 at 16.41.06.jpeg   # Itália Econômica
│   ├── WhatsApp Image 2026-02-13 at 16.18.19.jpeg   # Patagônia
│   ├── WhatsApp Image 2026-02-17 at 08.40.13.jpeg   # Porto de Galinhas
│   ├── WhatsApp Image 2026-02-17 at 08.41.25.jpeg   # Fortaleza
│   ├── WhatsApp Image 2026-02-17 at 08.42.24.jpeg   # Porto Seguro
│   ├── WhatsApp Image 2026-02-18 at 20.57.16.jpeg   # Punta Cana
│   ├── WhatsApp Image 2026-02-18 at 20.58.12.jpeg   # Santiago
│   └── WhatsApp Image 2026-02-19 at 17.08.53.jpeg   # Curaçao
└── postagens/                                         # Imagens de referência visual
```

---

## Seções do site

| # | Seção | Descrição |
|---|---|---|
| 1 | **Hero** | Logo, tagline animada, botões CTA para WhatsApp e Instagram |
| 2 | **Sobre** | Foto da Babi, apresentação e diferenciais da agência |
| 3 | **Pacotes** | Grid de 8 cards com imagem, detalhes e botão "Quero esse pacote" |
| 4 | **Depoimentos** | Testemunhos de clientes (placeholders iniciais) |
| 5 | **Contato / Footer** | Links sociais, navegação e FAB WhatsApp fixo |

---

## Contatos da empresa

| Canal | Valor |
|---|---|
| WhatsApp | +55 21 92006-4617 |
| Instagram | [@viajandocomababi_](https://www.instagram.com/viajandocomababi_/) |

---

## Funcionalidades técnicas

- **Design responsivo** (mobile-first): layouts para 320 px, 640 px, 1024 px e 1280 px+
- **Paleta de cores** extraída da identidade visual do logo (teal `#3AAFA9`)
- **Favicon** usando o logo oficial da empresa
- **Meta tags SEO completas**: title, description, keywords, canonical
- **Open Graph** para prévia rica ao compartilhar no WhatsApp/Instagram/Facebook
- **Twitter Card** configurada
- **FAB WhatsApp** fixo no canto inferior direito com animação de pulso e tooltip
- **Scroll-reveal** suave nos cards de pacotes e depoimentos via `IntersectionObserver`
- **Menu hamburguer** para mobile com travamento de scroll
- **Smooth scroll** para âncoras com offset dinâmico da navbar
- **Destaque de link ativo** na navbar conforme seção visível
- **Acessibilidade**: respeita `prefers-reduced-motion`
- **Mensagens WhatsApp pré-preenchidas** por pacote (URL encoded)
- **Google Analytics 4** (`G-WGDNTSY8WM`) com rastreamento de pacotes, categorias e leads

---

## Manutenção, analytics e regras

| Tema | Onde consultar |
|------|----------------|
| Regras do projeto (Cursor) | [`.cursor/rules/`](.cursor/rules/) |
| Relatórios GA4 por pacote | [`docs/analytics-pacotes.md`](docs/analytics-pacotes.md) |
| Funil comercial offline | [`docs/funil-offline.md`](docs/funil-offline.md) |

### Ao adicionar ou alterar um pacote

Os destaques da home vêm do sync (até 30). Para atualizar:

1. `python _sync_operator.py --apply` (ou `--from-json --apply` se o JSON já estiver atualizado)
2. Imagens ausentes: `--download-images` na coleta
3. **Regenerar o catálogo:** `python _build_ofertas.py` e `python _build_pacotes.py`
4. Validar no GA4 DebugView: `view_item`, `purchase` ("Quero esse pacote!") e `generate_lead`

### Sincronização mensal da operadora

```bash
python _sync_operator.py --download-images --apply
python _build_ofertas.py
python _build_pacotes.py
```

Isso atualiza a home (top 30 do sync), `promo-voos.html`, `campanhas.html` e o catálogo unificado em `pacotes.html`.

### Ao alterar eventos GA4

1. Editar apenas `analytics.js` (eventos) ou `script.js` (hooks de UI).
2. Atualizar `docs/analytics-pacotes.md` e bump `analytics.js?v=N` no `index.html`.
3. **Nunca** enviar dados pessoais do formulário ao GA4.

---

## Como executar localmente

Nenhuma dependência de servidor é necessária. Basta abrir o arquivo `index.html` em qualquer navegador moderno.

Para um servidor local rápido (recomendado para evitar problemas de CORS com imagens):

```bash
# Python 3
python -m http.server 8000

# Node.js (npx)
npx serve .
```

Acesse em `http://localhost:8000`.

---

## Deploy — GitHub Pages

O site é publicado automaticamente via GitHub Pages. Qualquer `push` para a branch `main` atualiza o site em produção.

**Configuração inicial (já realizada):**

```bash
git init
git add .
git commit -m "feat: cria site estático Viajando com a Babi"
git branch -M main
git remote add origin https://github.com/caio2121/viajando-com-a-babi.git
git push -u origin main
```

Ative o GitHub Pages em: **Settings → Pages → Branch: main / Folder: / (root)**.

---

## Como adicionar novos pacotes

1. Adicione a imagem do pacote na pasta `pacotes/` (e o `.webp`, se aplicável)
2. No `index.html`, dentro do `<div class="pacotes__grid">` da categoria correta, copie um bloco `<article class="card reveal">` existente
3. Atualize: `id` (slug), imagem (`src` / `picture`), destino (`alt`, `data-destino`, título), datas (`card__badge`), features, preço e link do WhatsApp
4. Execute `python _build_pacotes.py` para atualizar `pacotes.html`
5. Revise a página `/pacotes.html` no browser antes do deploy

---

## Licença

Todos os direitos reservados — Viajando com a Babi © 2026
