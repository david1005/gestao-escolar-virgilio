# Central de Notificacoes

## Objetivo

Adicionar notificacoes internas persistentes ao Sistema de Gestao Escolar, com um sino no menu superior, contador de nao lidas, historico e links para os itens relacionados. A primeira versao cobre pendencias operacionais, alteracoes feitas por outros usuarios e bloqueios por excesso de falhas de login.

## Dependencia

Esta funcionalidade integra-se ao desenho de seguranca em `docs/superpowers/specs/2026-10-07-dados-autenticacao-auditoria-design.md`. O alerta de falhas de login consumira o evento produzido pelo bloqueio persistente previsto naquele documento. A implementacao deve concluir primeiro a base de autenticacao e auditoria da qual esse evento depende.

## Escopo inicial

O sistema notificara:

- ocorrencia nao resolvida com mais de 15 dias completos;
- saida temporaria com retorno ainda marcado como pendente;
- registro ou ocorrencia alterado por usuario diferente de seu criador;
- inicio de bloqueio causado por cinco falhas de login dentro da janela de dez minutos.

Nao fazem parte desta versao e-mail, WhatsApp, push do navegador, notificacoes para dispositivos moveis, configuracao individual de preferencias ou um processo agendador externo.

## Destinatarios

### Ocorrencia com mais de 15 dias

Recebem o alerta usuarios ativos com permissao de ocorrencias e acesso ao aluno relacionado:

- administrador;
- PPDT;
- coordenador vinculado ao curso do aluno;
- diretor da turma do aluno.

Os estados `Aberta` e `Em acompanhamento` sao considerados nao resolvidos. O alerta torna-se ativo quando a diferenca entre a data atual e a data da ocorrencia ultrapassa 15 dias.

### Retorno nao confirmado

Recebem o alerta usuarios ativos com permissao de registros e acesso ao aluno relacionado:

- administrador;
- PPDT;
- biblioteca;
- coordenador vinculado ao curso do aluno;
- diretor da turma do aluno.

O alerta fica ativo quando o registro representa saida temporaria e `status_retorno` permanece `Pendente`, independentemente de o registro ser do dia atual ou anterior.

### Alteracao por outro usuario

Somente o criador do registro ou da ocorrencia recebe o alerta, desde que esteja ativo, ainda tenha acesso ao aluno e nao seja o autor da alteracao.

Registros e ocorrencias receberao a coluna `criado_por_id`. Novos itens usarao sempre o usuario autenticado. Para itens existentes, a migracao tentara recuperar o criador pela primeira auditoria de acao `criou` para a mesma entidade e identificador. Quando nao houver evidencia suficiente, o campo permanecera nulo e nenhuma identidade sera presumida.

### Falhas de login

Somente administradores ativos recebem o alerta quando uma chave de tentativa entra em bloqueio. A notificacao informa e-mail parcialmente mascarado, IP de origem e duracao do bloqueio. Senha, hash, token e cookie nunca entram na notificacao.

## Persistencia

Uma tabela `notificacoes` armazenara:

- `id`;
- `usuario_id` destinatario;
- `tipo`;
- `titulo`;
- `mensagem` curta;
- `entidade` e `entidade_id` opcionais;
- `url` interna opcional;
- `chave_deduplicacao`;
- `ativa`;
- `lida_em` opcional;
- `criada_em`;
- `atualizada_em`.

A combinacao de destinatario e chave de deduplicacao sera unica. As chaves automaticas incluirao o tipo, a entidade e seu identificador. Alertas de alteracao poderao consolidar novas edicoes no mesmo item enquanto a notificacao anterior estiver ativa e nao lida. Depois de lida, uma nova edicao feita por terceiro cria um novo ciclo de alerta.

As novas tabelas e colunas serao criadas pelo mecanismo existente de `Base.metadata.create_all` e pelas funcoes de compatibilidade de `app/main.py`, sem apagar dados existentes.

## Geracao e sincronizacao

### Eventos imediatos

Edicoes de registros e ocorrencias criam ou atualizam a notificacao do criador dentro da mesma transacao da alteracao. O bloqueio por falhas de login cria notificacoes para administradores dentro da transacao que persiste a tentativa e a auditoria.

### Pendencias automaticas

Ocorrencias antigas e retornos pendentes serao sincronizados quando o usuario consultar o resumo ou a listagem de notificacoes. A consulta considera apenas registros que o proprio destinatario pode acessar.

O sincronizador e idempotente:

- cria o alerta quando a condicao passa a existir;
- mantem um unico alerta ativo enquanto a condicao continua;
- marca o alerta como inativo e lido quando a ocorrencia e resolvida ou o retorno e confirmado;
- reativa o alerta como nao lido quando a mesma condicao volta a existir.

Essa abordagem dispensa cron, agendador em memoria ou um segundo servico no Ubuntu. Os alertas sao atualizados quando algum usuario abre o sistema ou quando o navegador realiza a proxima consulta periodica.

## API

Todas as rotas exigem usuario autenticado:

- `GET /api/notificacoes/resumo`: sincroniza pendencias do usuario e retorna quantidade nao lida e as cinco notificacoes ativas mais recentes;
- `GET /api/notificacoes/`: lista o historico paginado do usuario, com filtro por leitura e tipo;
- `PUT /api/notificacoes/{id}/ler`: marca uma notificacao pertencente ao usuario como lida;
- `PUT /api/notificacoes/ler-todas`: marca todas as notificacoes do usuario como lidas.

O backend ignora qualquer tentativa do navegador de informar ou alterar o destinatario. Um usuario nunca lista nem modifica notificacoes de outra conta.

URLs armazenadas aceitam apenas caminhos internos iniciados por `/`. Antes de navegar para a entidade relacionada, as rotas normais de aluno, registro ou ocorrencia repetem as verificacoes de permissao existentes.

## Interface

Um arquivo `static/js/notificacoes.js` montara o sino na barra superior de todas as paginas autenticadas, antes do menu do usuario. Cada template autenticado carregara esse arquivo.

O sino tera dimensoes estaveis e mostrara um contador apenas quando houver notificacoes nao lidas. O dropdown apresentara as cinco mais recentes, com icone, titulo, resumo, horario e indicacao visual de leitura.

As acoes disponiveis serao:

- abrir a entidade relacionada;
- marcar uma notificacao como lida;
- marcar todas como lidas;
- acessar `/notificacoes` para consultar o historico completo.

A pagina de historico usara paginacao no servidor e filtros por estado e tipo. O navegador consultara o resumo ao carregar a pagina, ao abrir o dropdown e a cada cinco minutos enquanto a pagina estiver visivel.

As mensagens nao exibirao descricao de ocorrencia, observacoes, motivo, contato de responsavel ou outros dados pessoais detalhados. O nome do aluno podera aparecer somente para destinatarios que ja passaram pela verificacao de acesso correspondente.

## Seguranca e falhas

- usuarios inativos nao recebem novos alertas;
- alteracoes feitas pelo proprio criador nao geram notificacao;
- falha ao persistir uma notificacao imediata reverte a operacao principal da mesma transacao;
- falha temporaria ao sincronizar pendencias retorna erro sem criar duplicatas parciais;
- notificacao de entidade removida ou inacessivel ainda pode ser marcada como lida, mas nao concede acesso ao destino;
- textos exibidos sao escapados no frontend pelo utilitario de seguranca existente;
- nenhuma rota retorna notificacoes de outro usuario, mesmo que seu identificador seja informado manualmente.

## Auditoria

Marcar notificacoes como lidas nao gera auditoria para evitar volume sem valor operacional. A origem do alerta continua rastreavel pelas auditorias da entidade ou da autenticacao que provocou sua criacao.

## Testes e criterios de aceite

- ocorrencia nao resolvida ultrapassando 15 dias gera um unico alerta por destinatario autorizado;
- ocorrencia resolvida desativa o alerta e reabertura o reativa como nao lido;
- saida temporaria pendente gera alerta e confirmacao do retorno o desativa;
- diretor e coordenador nao recebem alertas de alunos fora de seu escopo;
- biblioteca recebe retorno pendente, mas nao ocorrencia antiga sem permissao correspondente;
- edicao pelo proprio criador nao gera alerta;
- edicao por terceiro alerta somente o criador com acesso atual;
- item antigo sem criador comprovado nao gera alerta de alteracao;
- inicio de bloqueio por falhas de login alerta somente administradores e nao inclui segredo;
- consultas e marcacao de leitura ficam isoladas por `usuario_id`;
- sincronizacoes repetidas nao duplicam notificacoes;
- dropdown, contador, leitura e historico funcionam em tema claro e escuro;
- toda a suite de seguranca e as verificacoes de sintaxe JavaScript permanecem verdes.
