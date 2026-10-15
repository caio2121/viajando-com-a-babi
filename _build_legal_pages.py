"""Gera as páginas institucionais legais a partir dos partials públicos do site.

As páginas são HTML estático para GitHub Pages. O conteúdo abaixo usa somente
informações observadas no repositório e deixa decisões comerciais específicas
para a oferta/contrato correspondente.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

from _site_config import load_public_config, render_public_template


ROOT = Path(__file__).resolve().parent
CONFIG = load_public_config()
HEAD_ASSETS = render_public_template((ROOT / "_partials" / "head-assets.html").read_text(encoding="utf-8"), CONFIG)
GA4 = render_public_template((ROOT / "_partials" / "ga4.html").read_text(encoding="utf-8"), CONFIG)
HEADER = render_public_template((ROOT / "_partials" / "hub-header.html").read_text(encoding="utf-8"), CONFIG)
FOOTER = render_public_template((ROOT / "_partials" / "hub-footer.html").read_text(encoding="utf-8"), CONFIG)


PAGES = {
    "condicoes-comerciais.html": {
        "title": "Condições Comerciais",
        "description": "Como funcionam as cotações, ofertas, reservas e pagamentos da Viajando com a Babi.",
        "content": """
<p class="legal-page__eyebrow">Informações para contratar com clareza</p>
<h1>Condições Comerciais</h1>
<p class="legal-page__lead">Esta página explica o fluxo comercial observado no site. Cada oferta pode ter condições específicas, que prevalecem quando apresentadas antes da confirmação da contratação.</p>

<h2>1. O que a Viajando com a Babi oferece</h2>
<p>O site apresenta pacotes de viagem, promoções de voos, campanhas de hospedagem e serviços de consultoria e roteiros personalizados. A Viajando com a Babi atua no atendimento e na organização da viagem conforme a solução escolhida e os fornecedores envolvidos.</p>
<p>O site é uma vitrine e um canal de solicitação de atendimento. Não há checkout ou contratação automática nas páginas públicas: o visitante inicia o contato pelo WhatsApp, e-mail ou formulário que abre uma mensagem no WhatsApp.</p>

<h2>2. Cotação e confirmação</h2>
<ol>
  <li>Você informa destino, datas ou período, cidade de saída, número de viajantes e orçamento aproximado.</li>
  <li>A equipe consulta as opções disponíveis e pode apresentar pacote, voo, hospedagem, serviços ou roteiro compatíveis com o pedido.</li>
  <li>As opções podem ser ajustadas conforme o perfil da viagem e a disponibilidade encontrada.</li>
  <li>A reserva somente é considerada confirmada após a aceitação da proposta aplicável, o cumprimento das instruções de pagamento e a confirmação do fornecedor, quando exigida.</li>
</ol>

<h2>3. Preços, disponibilidade e validade</h2>
<p>As ofertas públicas podem exibir preço total, parcelas, taxas e datas. Os próprios cards informam quando taxas estão sujeitas a alteração. Assim, preço, disponibilidade, câmbio, regras tarifárias, hotel, voo e serviços incluídos devem ser reconfirmados na cotação.</p>
<p>A validade de uma oferta é a indicada na própria oferta ou na proposta enviada ao cliente. Se a oferta não informar uma validade, a equipe deve confirmar esse prazo antes da contratação. Uma solicitação pelo WhatsApp não congela preço ou disponibilidade.</p>

<h2>4. Pagamento</h2>
<p>O site informa a possibilidade de boleto sem análise de crédito e de parcelamento no cartão, conforme disponibilidade. A forma disponível, o número de parcelas, o valor total, eventuais encargos e as instruções de pagamento serão informados na proposta ou pelos canais de atendimento antes da confirmação.</p>
<p>Não envie dados completos de cartão, senhas ou documentos por um canal que não tenha sido indicado para esse fim. Em caso de dúvida, confirme a instrução pelo WhatsApp ou pelo e-mail oficial.</p>

<h2>5. O que está incluído e responsabilidades</h2>
<p>A composição da viagem varia por oferta. Verifique na proposta o que está incluído e o que não está incluído, como aéreo, hospedagem, alimentação, traslados, passeios, seguro, bagagem e taxas.</p>
<p>Quando um serviço é executado por companhia aérea, hotel, seguradora, operadora ou outro fornecedor, aplicam-se também as condições informadas por esse fornecedor. Isso não elimina os direitos previstos na legislação aplicável nem impede o atendimento da Viajando com a Babi para encaminhar dúvidas e solicitações.</p>

<h2>6. Documentos e requisitos de viagem</h2>
<p>O viajante deve conferir, antes da compra e do embarque, a validade de documentos, passaporte, vistos, autorizações, vacinas e demais requisitos do destino. As exigências podem mudar; consulte as fontes oficiais do país, da companhia aérea e dos fornecedores indicados na proposta.</p>

<h2>7. Atendimento</h2>
<p>Para orçamento e dúvidas comerciais, use o <a href="https://wa.me/5521920064617" target="_blank" rel="noopener noreferrer">WhatsApp +55 21 92006-4617</a> ou <a href="mailto:contato@viajandocomababi.com.br">contato@viajandocomababi.com.br</a>. Para cancelamento ou reembolso, consulte também a <a href="cancelamento-reembolso.html">política de cancelamento e reembolso</a>.</p>

<aside class="legal-callout"><strong>Importante:</strong> estas são condições gerais. A oferta, o contrato e as regras do fornecedor devem ser lidos antes do pagamento.</aside>
""",
    },
    "cancelamento-reembolso.html": {
        "title": "Cancelamento e Reembolso",
        "description": "Orientações para solicitar cancelamento, alteração, remarcação e reembolso de serviços de viagem.",
        "content": """
<p class="legal-page__eyebrow">Orientações para solicitações pós-venda</p>
<h1>Cancelamento, alteração e reembolso</h1>
<p class="legal-page__lead">O resultado de um cancelamento depende do produto contratado, do momento da solicitação e das regras da oferta, do contrato e dos fornecedores envolvidos.</p>

<h2>1. Como solicitar</h2>
<p>Envie a solicitação pelo <a href="https://wa.me/5521920064617" target="_blank" rel="noopener noreferrer">WhatsApp +55 21 92006-4617</a> ou pelo e-mail <a href="mailto:contato@viajandocomababi.com.br">contato@viajandocomababi.com.br</a>. Informe o nome do passageiro responsável, os dados da reserva ou proposta e o que deseja solicitar. Evite enviar dados sensíveis desnecessários.</p>
<p>A solicitação será encaminhada para análise. Peça e guarde a confirmação de recebimento pelo canal utilizado. O pedido não deve ser considerado aprovado apenas pelo envio da mensagem.</p>

<h2>2. Regras aplicáveis</h2>
<p>Cada serviço pode ter regras próprias: passagem aérea, hospedagem, pacote, passeio, seguro e demais itens podem ter prazos, condições de alteração e valores diferentes. As regras específicas devem estar na oferta, na proposta ou no contrato apresentado antes da contratação.</p>
<p>Taxas, multas ou retenções só devem ser aplicadas quando previstas nas condições aplicáveis e permitidas pela legislação. Não há um percentual único de cancelamento para todas as viagens.</p>

<h2>3. Alteração e remarcação</h2>
<p>Pedidos de alteração ou remarcação dependem de disponibilidade e das regras do fornecedor. Antes de qualquer mudança, será necessário confirmar diferença de preço, taxas eventualmente previstas e os novos dados da viagem.</p>

<h2>4. Reembolso</h2>
<p>Quando houver direito a reembolso, o valor e a forma de devolução serão apurados conforme o item contratado, o pagamento realizado, as regras do fornecedor e a legislação aplicável. O prazo efetivo deve ser informado no retorno da solicitação; esta página não cria prazo ou percentual que não tenha sido confirmado.</p>
<p>Se o pagamento tiver sido processado por fornecedor ou instituição financeira, o procedimento pode depender da confirmação e do processamento desse terceiro. A Viajando com a Babi deve informar o andamento disponível ao cliente.</p>

<h2>5. Direitos do consumidor</h2>
<p>Esta política não limita direitos previstos no Código de Defesa do Consumidor ou em outras normas aplicáveis. Em contratações realizadas fora do estabelecimento comercial, o direito de arrependimento pode incidir nas hipóteses legais; a aplicação ao caso concreto deve ser analisada considerando o serviço, o momento da contratação e a legislação vigente.</p>

<h2>6. Dúvidas</h2>
<p>Para dúvidas antes do pagamento, consulte as <a href="condicoes-comerciais.html">condições comerciais</a>. Para solicitações relacionadas a dados pessoais, acesse <a href="contato-lgpd.html">Contato LGPD</a>.</p>

<aside class="legal-callout"><strong>Não deixe para depois:</strong> solicite alterações e cancelamentos assim que souber da necessidade, pois fornecedores podem ter prazos próprios.</aside>
""",
    },
    "contato-lgpd.html": {
        "title": "Contato LGPD",
        "description": "Canal de contato para solicitações relacionadas aos dados pessoais tratados pela Viajando com a Babi.",
        "content": """
<p class="legal-page__eyebrow">Privacidade e direitos do titular</p>
<h1>Contato LGPD</h1>
<p class="legal-page__lead">Use este canal para pedir informações sobre o tratamento de seus dados pessoais ou exercer direitos previstos na legislação aplicável.</p>

<h2>1. Canal de atendimento</h2>
<p>Envie sua solicitação para <a href="mailto:contato@viajandocomababi.com.br">contato@viajandocomababi.com.br</a>. Também é possível iniciar contato pelo <a href="https://wa.me/5521920064617" target="_blank" rel="noopener noreferrer">WhatsApp +55 21 92006-4617</a>; para assuntos de privacidade, prefira o e-mail para facilitar o registro do pedido.</p>
<p>O site não possui formulário próprio ou backend para pedidos LGPD. Não envie documentos, senhas ou dados sensíveis além do necessário para localizar e atender a solicitação. A empresa pode precisar confirmar a identidade do solicitante por meio adequado antes de fornecer informações.</p>

<h2>2. O que informar</h2>
<ul>
  <li>nome e canal seguro para retorno;</li>
  <li>qual direito deseja exercer;</li>
  <li>contexto em que os dados foram fornecidos, como orçamento, e-mail ou WhatsApp;</li>
  <li>descrição objetiva do pedido e, se possível, período aproximado do contato.</li>
</ul>

<h2>3. Direitos</h2>
<p>Você pode solicitar confirmação da existência de tratamento, acesso, correção, informações sobre compartilhamento, eliminação ou anonimização quando aplicável, revogação de consentimento e outros direitos previstos na LGPD. A análise respeita hipóteses legais de conservação, direitos de terceiros, segurança e obrigações aplicáveis.</p>

<h2>4. Segurança e retorno</h2>
<p>Não use este canal para enviar dados de cartão ou credenciais. A resposta será encaminhada pelo canal informado, observadas as verificações necessárias e os prazos legais aplicáveis ao pedido. A confirmação de recebimento não significa atendimento automático ou deferimento imediato.</p>

<p>Consulte a <a href="privacidade.html">Política de Privacidade</a> para conhecer as categorias de dados, finalidades, compartilhamentos e o funcionamento do consentimento de analytics e publicidade.</p>
""",
    },
    "termos-de-uso.html": {
        "title": "Termos de Uso",
        "description": "Termos para utilização do site Viajando com a Babi, suas ofertas, conteúdos e canais de atendimento.",
        "content": """
<p class="legal-page__eyebrow">Regras de utilização do site</p>
<h1>Termos de Uso</h1>
<p class="legal-page__lead">Ao acessar o site Viajando com a Babi, você concorda em utilizá-lo de forma lícita, cuidadosa e compatível com estes termos.</p>

<h2>1. Objetivo do site</h2>
<p>O site apresenta informações institucionais, serviços, pacotes, promoções, campanhas e canais para solicitar atendimento de viagens. O conteúdo ajuda na decisão, mas não substitui a proposta, o contrato ou as condições específicas do serviço contratado.</p>

<h2>2. Ofertas e conteúdo</h2>
<p>Preços, datas, disponibilidade, imagens, hotéis, voos, taxas e serviços podem variar conforme atualização do catálogo e confirmação dos fornecedores. A informação válida para a contratação é a apresentada na proposta ou no contrato aplicável, antes do pagamento.</p>
<p>A equipe busca manter o conteúdo atualizado, mas não garante que uma oferta permaneça disponível após sua publicação. Se encontrar erro ou informação desatualizada, comunique pelo <a href="mailto:contato@viajandocomababi.com.br">e-mail oficial</a>.</p>

<h2>3. Uso permitido</h2>
<ul>
  <li>usar o site para consultar informações e solicitar atendimento legítimo;</li>
  <li>não copiar, alterar, explorar ou redistribuir o conteúdo comercial e visual sem autorização;</li>
  <li>não tentar interromper, sobrecarregar, invadir ou contornar mecanismos de segurança;</li>
  <li>não enviar informações falsas, conteúdo ilícito ou dados de terceiros sem autorização.</li>
</ul>

<h2>4. Links e serviços de terceiros</h2>
<p>O site pode direcionar para WhatsApp, Instagram, Google, seguradora, operadora, hotel ou outro fornecedor. Esses ambientes possuem termos e políticas próprios. A navegação para um terceiro não significa que o site controle suas práticas, disponibilidade ou conteúdo.</p>

<h2>5. Propriedade intelectual</h2>
<p>Marcas, textos, imagens, identidade visual, código e demais elementos do site pertencem à Viajando com a Babi ou são utilizados com autorização, quando aplicável. Nenhuma licença é concedida além do uso normal da página e dos materiais disponibilizados para consulta.</p>

<h2>6. Responsabilidades</h2>
<p>O usuário deve conferir os dados da proposta e fornecer informações corretas para o atendimento. As responsabilidades da agência, do cliente e dos fornecedores são definidas pela oferta, pelo contrato e pela legislação aplicável. Nada nestes termos afasta direitos obrigatórios do consumidor ou limita responsabilidade que não possa ser excluída por lei.</p>

<h2>7. Contato e atualizações</h2>
<p>Para falar com a equipe, use o <a href="https://wa.me/5521920064617" target="_blank" rel="noopener noreferrer">WhatsApp +55 21 92006-4617</a> ou <a href="mailto:contato@viajandocomababi.com.br">contato@viajandocomababi.com.br</a>. Estes termos podem ser atualizados para refletir mudanças no site, nos serviços ou na legislação. A versão vigente será a publicada nesta página.</p>
""",
    },
    "cookies.html": {
        "title": "Política de Cookies",
        "description": "Tecnologias de armazenamento, analytics, publicidade e gerenciamento de consentimento no site Viajando com a Babi.",
        "content": """
<p class="legal-page__eyebrow">Transparência sobre tecnologias de armazenamento</p>
<h1>Política de Cookies</h1>
<p class="legal-page__lead">Esta política descreve o que foi identificado no código público do site. A disponibilidade e a duração de cookies criados por terceiros podem mudar conforme as configurações desses fornecedores.</p>

<h2>1. Preferência de consentimento</h2>
<p>O site salva no navegador a escolha do visitante em <code>localStorage</code>, usando a chave <code>vcb_consent_analytics</code>. Os valores observados são <code>granted</code> e <code>denied</code>. Esse registro é necessário para lembrar a escolha e não é um cookie de publicidade.</p>

<h2>2. Categorias identificadas</h2>
<div class="legal-table-wrap"><table class="legal-table"><thead><tr><th>Categoria</th><th>Fornecedor</th><th>Finalidade</th><th>Quando é ativada</th><th>Retenção</th></tr></thead><tbody>
<tr><td>Preferência</td><td>Site</td><td>Guardar a escolha do banner</td><td>Ao aceitar ou recusar</td><td>Até a remoção ou alteração do armazenamento local</td></tr>
<tr><td>Analytics</td><td>Google Analytics 4</td><td>Medir visitas, navegação e interações</td><td>Após aceite</td><td>Definida pelo Google e pela configuração da conta; não confirmada no site</td></tr>
<tr><td>Publicidade</td><td>Google Ads</td><td>Medir campanhas e conversões</td><td>Após aceite</td><td>Definida pelo Google e pela configuração da conta; não confirmada no site</td></tr>
</tbody></table></div>
<p>Antes do aceite, o código define os sinais de consentimento do Google como negados e não carrega o script remoto do Google. Após o aceite, o site atualiza <code>analytics_storage</code>, <code>ad_storage</code>, <code>ad_user_data</code> e <code>ad_personalization</code> para concedidos e agenda o carregamento das tags configuradas.</p>

<h2>3. Como escolher</h2>
<p>Na primeira visita, o banner oferece <strong>Aceitar cookies</strong> e <strong>Recusar</strong>. Recusar impede o carregamento das tags do Google enquanto a preferência permanecer negada. A escolha não impede o uso do catálogo, do conteúdo ou do contato comercial.</p>

<h2 id="gerenciar-cookies">4. Como revogar ou alterar</h2>
<p>Você pode revogar o consentimento de analytics e publicidade a qualquer momento. A ação atualiza a preferência para <code>denied</code> e informa o Google sobre a mudança para as próximas medições.</p>
<button type="button" class="btn btn--outline btn--md" id="revokeConsent">Revogar consentimento de analytics e publicidade</button>
<p id="consentStatus" class="legal-status" role="status" aria-live="polite"></p>
<p>Também é possível apagar o armazenamento local e os cookies nas configurações do navegador. A exclusão de dados já recebidos por Google ou outros terceiros deve ser solicitada conforme os canais e políticas desses fornecedores.</p>

<h2>5. Mais informações</h2>
<p>Consulte a <a href="privacidade.html">Política de Privacidade</a> para saber quais dados podem ser tratados, para quais finalidades e como exercer direitos. O uso de Consent Mode v2 foi verificado no código pelos quatro sinais de consentimento exigidos pelo Google, mas isso não constitui declaração de conformidade jurídica ou certificação.</p>
""",
    },
    "privacidade.html": {
        "title": "Política de Privacidade",
        "description": "Como a Viajando com a Babi coleta, utiliza, compartilha e protege dados pessoais no site e no atendimento.",
        "content": """
<p class="legal-page__eyebrow">Transparência sobre dados pessoais</p>
<h1>Política de Privacidade</h1>
<p class="legal-page__lead">A Viajando com a Babi (CNPJ 60.536.280/0001-89) apresenta nesta política as práticas observadas no site e no atendimento iniciado por seus canais oficiais.</p>

<h2>1. Quem trata os dados</h2>
<p>A operação do site identifica como responsável pelo atendimento <strong>Bárbara Cristina Machado Valente Costa de Abreu | Viajando com a Babi</strong>. Para dúvidas sobre privacidade ou solicitações de titulares, use <a href="contato-lgpd.html">Contato LGPD</a>, <a href="mailto:contato@viajandocomababi.com.br">contato@viajandocomababi.com.br</a> ou o WhatsApp informado no site.</p>

<h2>2. Dados tratados</h2>
<ul>
  <li>dados informados no formulário de viagem: destino, datas ou período, número de adultos, idades de crianças, cidade de saída e orçamento;</li>
  <li>nome, telefone, e-mail e mensagem quando a pessoa decide informá-los no atendimento;</li>
  <li>conteúdo e metadados da conversa quando o contato é enviado ao WhatsApp ou ao e-mail, sob as regras desses canais;</li>
  <li>informações de navegação e interações de analytics e publicidade somente conforme a escolha de consentimento descrita em <a href="cookies.html">Cookies</a>.</li>
</ul>
<p>O formulário público não envia os campos para um backend próprio: o JavaScript monta uma mensagem e abre o WhatsApp. O site não mantém, no código observado, um banco de dados de solicitações do formulário.</p>

<h2>3. Finalidades e bases legais</h2>
<ul>
  <li><strong>Atendimento, cotação e planejamento:</strong> responder ao pedido e realizar procedimentos preliminares relacionados a uma contratação, quando solicitados pela pessoa;</li>
  <li><strong>Execução da viagem:</strong> usar dados necessários para organizar serviços, reservas e comunicação com fornecedores, quando a pessoa prosseguir com a contratação;</li>
  <li><strong>Obrigações e defesa de direitos:</strong> conservar ou utilizar informações quando houver obrigação legal ou necessidade de exercício regular de direitos;</li>
  <li><strong>Analytics e publicidade:</strong> medir navegação e conversões somente após o consentimento registrado no navegador.</li>
</ul>
<p>A base legal adequada para cada tratamento depende do contexto concreto. Esta página não transforma uma hipótese legal em autorização genérica para qualquer finalidade.</p>

<h2>4. Compartilhamento</h2>
<p>Quando necessário para a cotação ou execução de uma viagem, dados podem ser compartilhados com operadoras, companhias aéreas, hotéis, seguradoras e demais fornecedores da solução escolhida. O WhatsApp, o e-mail, o Google Analytics e o Google Ads também tratam dados conforme seus próprios serviços quando o visitante utiliza esses canais ou concede consentimento.</p>

<h2>5. Cookies e consentimento</h2>
<p>O site usa <code>localStorage</code> para registrar a preferência em <code>vcb_consent_analytics</code>. Com preferência não definida ou negada, o código mantém sinais de consentimento Google negados e não carrega as tags remotas do Google. Com aceite, as tags configuradas podem tratar informações de analytics e publicidade. Consulte a <a href="cookies.html">Política de Cookies</a> para detalhes e para revogar a escolha.</p>

<h2>6. Retenção</h2>
<p>O código público não define um prazo único para mensagens recebidas no WhatsApp, e-mail ou por fornecedores. A retenção deve ocorrer somente pelo tempo necessário à finalidade, às obrigações legais e à defesa de direitos, conforme o contexto. A definição operacional de prazos por categoria é uma pendência de governança da empresa.</p>

<h2>7. Direitos do titular</h2>
<p>Você pode solicitar confirmação, acesso, correção, informações sobre compartilhamento, anonimização, bloqueio ou eliminação quando aplicável, portabilidade e revogação de consentimento, além de outros direitos previstos na LGPD. Os pedidos são tratados conforme as hipóteses legais, a proteção de terceiros e a necessidade de confirmação de identidade.</p>

<h2>8. Segurança</h2>
<p>O site utiliza HTTPS quando publicado, não solicita dados de cartão no formulário e envia a mensagem escolhida para o WhatsApp em nova aba. Nenhuma transmissão pela internet ou por serviço de terceiro é isenta de riscos; não compartilhe senhas ou dados desnecessários.</p>

<h2>9. Atualizações e contato</h2>
<p>Esta política pode ser atualizada quando o site, os serviços, os fornecedores ou a legislação mudarem. A data da versão publicada aparece abaixo do título. Para exercer direitos, acesse <a href="contato-lgpd.html">Contato LGPD</a>.</p>
""",
    },
}


def render_page(filename: str, page: dict[str, str]) -> str:
    title = escape(page["title"])
    description = escape(page["description"])
    canonical = f'{CONFIG["public_base_url"]}/{filename}'
    cookie_controls = ""
    if filename == "cookies.html":
        cookie_controls = """
  <script>
    (function initConsentControls() {
      var button = document.getElementById('revokeConsent');
      var status = document.getElementById('consentStatus');
      if (!button) return;
      button.addEventListener('click', function () {
        if (window.VCBConsent && typeof window.VCBConsent.revoke === 'function') {
          window.VCBConsent.revoke();
        } else {
          try { localStorage.setItem('vcb_consent_analytics', 'denied'); } catch (e) {}
        }
        if (status) status.textContent = 'Consentimento revogado para as próximas medições neste navegador.';
      });
    })();
  </script>
"""
    return f'''<!doctype html>
<html lang="pt-BR">
<head>
  {HEAD_ASSETS}
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="style.css?v=31">
  <link rel="icon" type="image/png" href="assets/logo-vcb.png">
  <meta name="description" content="{description}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{title} | {escape(CONFIG["brand_name"])}">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="{CONFIG["public_base_url"]}/assets/og-share.jpeg">
  <meta property="og:locale" content="pt_BR">
  <meta property="og:site_name" content="{escape(CONFIG["brand_name"])}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title} | {escape(CONFIG["brand_name"])}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{CONFIG["public_base_url"]}/assets/og-share.jpeg">
  <title>{title} | {escape(CONFIG["brand_name"])}</title>
  {GA4}
</head>
<body>
  <a class="skip-link" href="#main-content">Pular para o conteúdo principal</a>
{HEADER}
  <main id="main-content" class="container legal-page" data-legal-status="published-with-pending-validation" data-legal-version="2026-10-14">
    <nav class="breadcrumb" aria-label="Navegação estrutural"><a href="/">Início</a> <span aria-hidden="true">/</span> {title}</nav>
    <article class="legal-page__content">
      {page["content"]}
      <p class="legal-page__updated"><strong>Última atualização:</strong> 14 de outubro de 2026</p>
      <nav class="legal-page__related" aria-label="Documentos relacionados">
        <a href="privacidade.html">Privacidade</a>
        <a href="cookies.html">Cookies</a>
        <a href="termos-de-uso.html">Termos de uso</a>
        <a href="condicoes-comerciais.html">Condições comerciais</a>
        <a href="cancelamento-reembolso.html">Cancelamento e reembolso</a>
        <a href="contato-lgpd.html">Contato LGPD</a>
      </nav>
    </article>
  </main>
{cookie_controls}
{FOOTER}
'''


if __name__ == "__main__":
    for filename, page in PAGES.items():
        (ROOT / filename).write_text(render_page(filename, page), encoding="utf-8")
        print(f"Gerado: {filename}")
