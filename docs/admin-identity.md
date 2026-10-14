# Identidade administrativa e RBAC

## Estado implementado

- contas são armazenadas em `users`, com papel em `user_roles`;
- senha persistida usa hash salgado PBKDF2-SHA256, nunca texto claro;
- `ADMIN_USERNAME` + `ADMIN_PASSWORD` servem somente para bootstrap local quando
  o banco ainda não possui usuários; depois disso a autenticação consulta a
  identidade persistida;
- papéis `viewer`, `editor` e `admin` são avaliados no servidor;
- `viewer` consulta, `editor` cria/edita rascunhos e `admin` publica, arquiva,
  cria usuários e remove ofertas;
- sessão verifica o status atual do usuário em cada requisição, portanto conta
  desativada perde acesso mesmo com cookie assinado ainda válido.

## Recuperação e troca

O fluxo de troca exige a senha atual. O fluxo de recuperação grava somente hash
do token, expira em 15 minutos, invalida token usado e responde de forma
indistinguível para usuário existente ou inexistente. A entrega do token deve
ser conectada a canal operacional aprovado; o endpoint não retorna o token.

## Limites atuais

- convite por e-mail, MFA, rate limit, auditoria completa e gestão de
  desativação pela UI permanecem tasks separadas;
- o bootstrap por variável de ambiente é aceitável somente no laboratório local
  e não torna o perfil production-ready;
- usuários e roles não devem ser expostos à API pública.

## Verificações obrigatórias

1. Login exige username e senha válidos.
2. Hashes diferentes para a mesma senha usam salts diferentes.
3. Viewer não publica nem arquiva.
4. Conta desativada recebe `401` no próximo request.
5. Token expirado/usado não troca senha.
6. Reset não revela se o username existe.
