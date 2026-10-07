# Dados, Autenticacao e Auditoria

## Objetivo

Reduzir os dados pessoais enviados ao navegador e fortalecer autenticacao, encerramento de sessoes, protecao contra tentativas de login e rastreabilidade das operacoes, preservando os fluxos e a aparencia atuais do sistema.

## Escopo

Esta mudanca cobre:

- listagens paginadas de alunos, registros e ocorrencias;
- respostas resumidas para listagens e seletores;
- detalhes pessoais de aluno carregados somente em endpoint autorizado de detalhe;
- bloqueio persistente de tentativas de login;
- invalidacao de tokens apos troca ou redefinicao de senha;
- auditoria de eventos de autenticacao e administracao de usuarios;
- atualizacao do PyJWT para uma versao sem as vulnerabilidades identificadas.

Nao fazem parte desta etapa MFA, integracao com provedor externo de identidade, Redis, alteracoes de proxy reverso, HTTPS ou configuracao do Ubuntu Server.

## Dados enviados ao navegador

### Contratos de listagem

As rotas de listagem de alunos, registros e ocorrencias aceitarao `page`, `page_size`, busca e filtros proprios de cada tela. `page` inicia em 1 e `page_size` aceita somente 10, 25, 50 ou 100, com padrao 25.

As respostas terao o formato:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 25,
  "pages": 1
}
```

Filtros de perfil continuam sendo aplicados antes de contagem e paginacao. O frontend nao recebe linhas fora do escopo do usuario.

### Minimizacao

A listagem de alunos enviara apenas identificador, nome, matricula, turma e status. As colunas de responsavel e contato serao removidas da tabela geral. Data de nascimento, responsavel e contato serao carregados somente ao abrir a ficha ou a edicao individual de um aluno.

Seletores de alunos usados em registros e ocorrencias terao uma rota resumida com `id`, `nome`, `matricula` e `turma_id`. A busca exigira pelo menos dois caracteres e retornara no maximo 20 resultados.

Dados pessoais completos continuarao disponiveis no endpoint de detalhe do aluno, depois da verificacao de permissao existente.

A exportacao completa de alunos deixara de montar o CSV a partir da listagem no navegador. Ela sera gerada pelo servidor somente apos acao explicita de usuario autorizado e sera registrada na auditoria. Assim, a listagem permanece minima sem eliminar a funcao administrativa de exportacao.

As listagens de registros e ocorrencias enviarao somente os campos exibidos nas respectivas tabelas e os identificadores necessarios para navegacao e edicao. A edicao continuara usando o registro retornado na pagina atual.

### Frontend

Busca, filtros, quantidade por pagina e botoes anterior/proximo passarao parametros ao servidor. Mudanca de filtro volta para a primeira pagina. Criacao, edicao ou exclusao recarrega somente a pagina atual; se ela ficar vazia, o frontend volta uma pagina.

O estilo e a navegacao atuais serao preservados. A unica reducao visual intencional sera a retirada de responsavel e contato da tabela geral; esses dados permanecerao na ficha e no formulario individual. Estados de carregamento, ausencia de resultados e erros continuarao visiveis nas tabelas.

## Autenticacao

### Tentativas persistentes

Uma tabela `tentativas_login` armazenara chave derivada de IP e e-mail normalizado, quantidade de falhas, ultima tentativa e instante de bloqueio. O limite permanece em cinco falhas, com bloqueio de dez minutos.

Uma autenticacao bem-sucedida remove as falhas daquela chave. Registros expirados poderao ser reutilizados ou removidos durante novas tentativas, sem tarefa agendada.

As respostas de falha nao revelarao se o e-mail existe. Contas inativas usarao a mesma resposta publica de credencial invalida, mas o motivo real sera registrado na auditoria.

### Invalidacao de sessao

`usuarios` recebera `versao_token`, iniciada em zero. O JWT carregara `sub`, `ver`, `iat`, `exp` e `jti`. A autenticacao rejeitara o token quando `ver` for diferente da versao atual do usuario.

Troca de senha, redefinicao administrativa de senha, inativacao e alteracao de perfil ou vinculos de acesso incrementarao `versao_token`. Assim, tokens emitidos anteriormente deixam de funcionar imediatamente.

O cookie de acesso tera duracao alinhada ao tempo real do JWT, atualmente 60 minutos. Logout remove os cookies locais. Encerrar uma sessao individual antes da expiracao, sem alterar senha, permanece fora do escopo por exigir uma lista de revogacao ou sessoes persistentes.

## Auditoria

Eventos de autenticacao serao registrados com data, IP e user agent:

- login bem-sucedido;
- login negado por credencial invalida, usuario inativo ou bloqueio;
- logout;
- troca da propria senha;
- redefinicao administrativa de senha;
- criacao, edicao, inativacao e alteracao de perfil/permissoes de usuario.

Falhas anteriores a identificacao do usuario terao `usuario_id` nulo e o e-mail normalizado nos detalhes. Senhas, hashes, tokens e cookies nunca serao gravados na auditoria.

Os detalhes administrativos registrarao valores anteriores e novos apenas para perfil, status e vinculos de acesso. Nomes e e-mails podem aparecer quando necessarios para identificar a conta, mas dados de alunos e credenciais nao serao adicionados.

## Banco e compatibilidade

As novas tabelas serao criadas pelo mecanismo existente de `Base.metadata.create_all`. A coluna `versao_token` sera adicionada pelo mecanismo de compatibilidade usado em `app/main.py`, permitindo atualizar a base existente sem apagar dados.

As rotas de detalhe, criacao, edicao, exclusao, importacao, relatorios e dashboard permanecerao compativeis. Os contratos das tres listagens, da busca resumida de alunos e da exportacao de alunos serao alterados junto com seus consumidores no frontend.

## Tratamento de erros

Parametros de pagina invalidos retornarao erro de validacao. Paginas acima do total retornarao `items` vazio e metadados consistentes. Falhas de autenticacao permanecerao com mensagens genericas para o usuario.

Falha ao registrar auditoria durante uma operacao de seguranca impedira o commit dessa operacao quando ambos estiverem na mesma transacao. Uma tentativa de login invalida tera seu contador e sua auditoria confirmados antes da resposta de erro.

## Testes e criterios de aceite

- listagens retornam apenas a pagina solicitada e os metadados corretos;
- respostas resumidas nao incluem nascimento, responsavel ou contato;
- edicao individual carrega os dados completos somente depois da autorizacao do aluno;
- exportacao completa e gerada sob demanda e registrada na auditoria;
- filtros de perfil sao aplicados antes da paginacao;
- busca resumida exige dois caracteres e limita a 20 resultados;
- cinco falhas persistentes bloqueiam novas tentativas durante dez minutos;
- reiniciar o processo nao limpa o bloqueio salvo no banco;
- login bem-sucedido limpa as falhas da mesma chave;
- token anterior a troca/reset de senha e alteracao de acesso e rejeitado;
- cookies expiram junto com o JWT;
- auditoria registra eventos previstos com IP e user agent e nunca inclui senha ou token;
- telas de alunos, registros e ocorrencias continuam pesquisando, filtrando e paginando;
- toda a suite atual permanece verde.
