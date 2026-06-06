# Documentacao do Projeto - Sistema de Gestao Escolar

Versao: 0.1  
Data: 05/06/2026  
Projeto: Gestao Escolar Virgilio  
Repositorio: david1005/gestao-escolar-virgilio

## 1. Visao geral

O Sistema de Gestao Escolar e uma aplicacao web desenvolvida para apoiar a rotina administrativa, pedagogica e disciplinar de uma escola profissional de tempo integral.

O sistema centraliza o cadastro de alunos, cursos, turmas, registros de atrasos e saidas antecipadas, ocorrencias disciplinares, anexos, relatorios, dashboards, usuarios, permissoes, backups e configuracoes institucionais.

A solucao foi pensada inicialmente para a realidade da EEEP Governador Virgilio Tavora, contemplando cursos tecnicos como Enfermagem, Informatica, Redes de Computadores e Regencia, com turmas organizadas por ano, letra e curso.

## 2. Objetivos

### 2.1 Objetivo geral

Desenvolver um sistema web para auxiliar a escola no controle de alunos, registros administrativos, ocorrencias, relatorios e permissoes de acesso, reduzindo controles manuais e melhorando a rastreabilidade das informacoes.

### 2.2 Objetivos especificos

- Manter cadastro centralizado de alunos, cursos e turmas.
- Registrar atrasos e saidas antecipadas.
- Registrar ocorrencias escolares com historico por aluno.
- Emitir autorizacoes e termos para impressao.
- Controlar acesso por perfil de usuario.
- Permitir importacao e exportacao de alunos.
- Permitir anexar documentos relacionados a alunos, registros e ocorrencias.
- Gerar relatorios oficiais e indicadores gerenciais.
- Registrar auditoria das principais acoes.
- Permitir backup do banco de dados.
- Facilitar a implantacao em ambiente local ou hospedado.

## 3. Escopo do sistema

### 3.1 Dentro do escopo

- Autenticacao de usuarios.
- Cadastro e manutencao de alunos.
- Cadastro e manutencao de cursos e turmas.
- Importacao de alunos por CSV.
- Exportacao de alunos em CSV.
- Registro de atrasos.
- Registro de saidas antecipadas.
- Registro de ocorrencias.
- Consulta individual do historico do aluno.
- Impressao de autorizacao de entrada/saida.
- Impressao de termo de ocorrencia.
- Dashboard com indicadores.
- Controle de usuarios, perfis e permissoes.
- Configuracoes da escola.
- Ano letivo.
- Backup manual.
- Anexos.
- Auditoria.
- Deploy em Railway com PostgreSQL.

### 3.2 Fora do escopo atual

- Integracao oficial com sistemas externos da Secretaria de Educacao.
- Envio automatico de e-mail ou WhatsApp.
- Assinatura digital juridicamente validada.
- Aplicativo mobile nativo.
- Controle de notas, frequencia diaria completa ou boletim.
- Pagamento, financeiro ou estoque.

## 4. Publico-alvo

- Gestao escolar.
- Coordenacao pedagogica.
- Coordenadores de curso.
- Diretores de turma.
- Professores responsaveis por acompanhamento.
- Biblioteca ou setor responsavel por registros de entrada/saida.
- Secretaria escolar.

## 5. Perfis de usuario

| Perfil | Descricao | Acesso esperado |
|---|---|---|
| admin | Administrador geral do sistema | Acesso total |
| ppdt | Perfil pedagogico com permissao operacional ampla | Alunos, registros, ocorrencias, dashboard e relatorios |
| coordenador | Coordenador de um ou mais cursos | Acesso restrito aos cursos vinculados |
| diretor_turma | Diretor responsavel por uma turma especifica | Acesso restrito a sua turma |
| biblioteca | Usuario de apoio para registros | Registros e dashboard |

## 6. Requisitos funcionais

### RF01 - Autenticacao

O sistema deve permitir login de usuarios cadastrados por e-mail e senha.

### RF02 - Logout

O sistema deve permitir encerramento da sessao do usuario autenticado.

### RF03 - Criacao automatica do administrador inicial

Quando o banco estiver vazio, o sistema deve criar automaticamente um usuario administrador inicial com dados definidos por variaveis de ambiente.

### RF04 - Cadastro de usuarios

O administrador deve poder cadastrar usuarios informando nome, e-mail, senha, perfil, turma ou cursos vinculados, conforme o perfil.

### RF05 - Edicao de usuarios

O administrador deve poder editar dados, perfil, vinculos e status de usuarios.

### RF06 - Inativacao de usuarios

O administrador deve poder inativar usuarios sem remover obrigatoriamente seu historico.

### RF07 - Reset de senha

O administrador deve poder redefinir a senha de um usuario.

### RF08 - Troca de senha

O usuario autenticado deve poder trocar sua propria senha.

### RF09 - Cadastro de cursos

Usuarios autorizados devem poder cadastrar cursos informando nome e sigla.

### RF10 - Edicao de cursos

Usuarios autorizados devem poder editar nome e sigla de cursos cadastrados.

### RF11 - Cadastro de turmas

Usuarios autorizados devem poder cadastrar turmas informando curso, ano e letra.

### RF12 - Edicao de turmas

Usuarios autorizados devem poder editar curso, ano e letra de turmas cadastradas.

### RF13 - Cadastro de alunos

Usuarios autorizados devem poder cadastrar alunos informando nome, matricula, data de nascimento, responsavel, contato, turma e status.

### RF14 - Edicao de alunos

Usuarios autorizados devem poder editar dados cadastrais dos alunos.

### RF15 - Consulta de alunos

O sistema deve listar alunos com filtros por nome, turma, ano, curso e status.

### RF16 - Perfil individual do aluno

O sistema deve possuir uma pagina individual do aluno com dados, historico de registros, ocorrencias e anexos.

### RF17 - Importacao de alunos

O sistema deve importar alunos por arquivo CSV, permitindo selecionar curso e ano para definir a turma de importacao.

### RF18 - Validacao de datas na importacao

O sistema deve aceitar datas de nascimento em formato brasileiro DD/MM/AAAA e ISO AAAA-MM-DD.

### RF19 - Exportacao de alunos

O sistema deve exportar alunos filtrados em arquivo CSV.

### RF20 - Virada de ano

O sistema deve promover alunos ativos do 1o para o 2o ano, do 2o para o 3o ano e marcar alunos do 3o ano como concluidos.

Na virada de ano, as turmas cadastradas representam a estrutura fixa da escola. Assim, os alunos mudam de turma, mas a turma em si permanece cadastrada. Exemplo: alunos do 1o B de Informatica passam para o 2o B de Informatica; alunos do 2o B passam para o 3o B; alunos do 3o B ficam com status concluido; o 1o B fica vazio para receber novos alunos.

### RF21 - Previa da virada de ano

Antes da virada, o sistema deve mostrar uma previa com quantidade de alunos promovidos, concluidos e sem destino.

### RF22 - Registro de atraso

O sistema deve permitir registrar atraso de aluno, informando data, aula, motivo, documento e observacoes.

### RF23 - Registro de saida antecipada

O sistema deve permitir registrar saida antecipada de aluno, informando data, aula, motivo, documento e observacoes.

### RF24 - Edicao de registros

Usuarios autorizados devem poder editar registros de atraso e saida antecipada.

### RF25 - Exclusao de registros

Usuarios autorizados devem poder excluir registros, respeitando permissoes.

### RF26 - Impressao de autorizacao

O sistema deve permitir imprimir autorizacao de entrada ou saida para entrega ao professor ou vigilancia.

### RF27 - Cadastro de ocorrencias

O sistema deve permitir registrar ocorrencias com data, tipo, descricao, medida, gravidade, status, acoes tomadas, responsavel notificado e usuario registrador.

### RF28 - Numeracao de ocorrencias

O sistema deve numerar ocorrencias por aluno, permitindo identificar se e 1a, 2a, 3a ocorrencia etc.

### RF29 - Edicao de ocorrencias

Usuarios autorizados devem poder editar ocorrencias.

### RF30 - Exclusao de ocorrencias

Usuarios autorizados devem poder excluir ocorrencias, respeitando permissoes.

### RF31 - Impressao de termo de ocorrencia

O sistema deve permitir gerar termo de ocorrencia para impressao, contendo dados do aluno, turma, responsavel, descricao, medida, acoes e assinaturas.

### RF32 - Anexos

O sistema deve permitir anexar arquivos a alunos, registros e ocorrencias.

### RF33 - Consulta geral de anexos

O sistema deve permitir consultar anexos cadastrados na tela de configuracoes.

### RF34 - Dashboard gerencial

O sistema deve exibir indicadores de alunos, atrasos, saidas, ocorrencias, ranking e dados por turma.

### RF35 - Relatorios oficiais

O sistema deve gerar relatorios oficiais em formato imprimivel para alunos, ocorrencias e resumo por turma.

### RF36 - Configuracoes da escola

O sistema deve permitir configurar nome da escola, endereco, telefone e responsavel exibido nos documentos.

### RF37 - Ano letivo

O sistema deve permitir cadastrar e ativar anos letivos.

### RF37.1 - Encerramento de ano letivo

O sistema deve permitir encerrar um ano letivo, impedindo que ele continue como ano ativo.

### RF37.2 - Vinculo de dados ao ano letivo

O sistema deve vincular alunos, registros e ocorrencias ao ano letivo ativo no momento do cadastro.

### RF38 - Permissoes por perfil

O sistema deve permitir configurar quais modulos cada perfil pode acessar.

### RF39 - Backup manual

O administrador deve poder gerar e baixar backup manual do banco.

### RF40 - Auditoria

O sistema deve registrar acoes relevantes como criar, editar, excluir, importar, gerar backup, alterar permissoes e enviar anexos.

## 7. Requisitos nao funcionais

### RNF01 - Usabilidade

O sistema deve possuir interface web responsiva, simples e adequada ao uso frequente em ambiente escolar.

### RNF02 - Desempenho

O sistema deve responder rapidamente para consultas comuns de alunos, registros, ocorrencias e dashboard em volumes escolares moderados.

### RNF03 - Seguranca

O sistema deve exigir autenticacao, controlar permissoes, proteger rotas sensiveis e evitar operacoes sem permissao.

### RNF04 - Integridade dos dados

O sistema deve impedir duplicidade de matricula, curso e turma no mesmo contexto.

### RNF05 - Rastreabilidade

O sistema deve registrar auditoria das acoes administrativas e operacionais relevantes.

### RNF06 - Portabilidade

O sistema deve poder rodar localmente ou em hospedagem com suporte a Python/FastAPI e PostgreSQL.

### RNF07 - Manutenibilidade

O codigo deve ser organizado por rotas, modelos, schemas, templates e arquivos estaticos.

### RNF08 - Configurabilidade

Dados sensiveis e parametros de implantacao devem ser configurados por variaveis de ambiente.

### RNF09 - Disponibilidade

Em ambiente de producao, o sistema deve ser hospedado em servidor com disponibilidade adequada ao horario de funcionamento da escola.

### RNF10 - Backup

O sistema deve oferecer rotina manual de backup e permitir armazenamento externo dos arquivos gerados.

## 8. Regras de negocio

| Codigo | Regra |
|---|---|
| RN01 | Todo aluno deve pertencer a uma turma cadastrada. |
| RN02 | Toda turma pertence a um curso. |
| RN03 | Uma turma e identificada por ano, letra e curso. |
| RN04 | Nao deve existir turma duplicada com mesmo ano, letra e curso. |
| RN05 | A matricula do aluno deve ser unica. |
| RN06 | A chave interna do aluno e o id, nao a matricula. |
| RN07 | Alunos podem ter status ativo, concluido, transferido ou desistente. |
| RN08 | Alunos com historico nao devem ser removidos fisicamente sem criterio; podem ser arquivados por status. |
| RN09 | Na virada de ano, alunos do 3o ano passam para concluido. |
| RN10 | Na virada de ano, alunos do 1o e 2o ano so devem ser promovidos se existir turma destino. |
| RN10.1 | As turmas sao consideradas estrutura fixa da escola; a virada altera a turma dos alunos, nao recria as turmas. |
| RN10.2 | Apos a virada, as turmas de 1o ano ficam disponiveis para receber os novos alunos ingressantes. |
| RN10.3 | Para promover uma turma, deve existir a turma equivalente no proximo ano, com mesma letra e curso. |
| RN10.4 | Alunos, registros e ocorrencias novos devem ser vinculados automaticamente ao ano letivo ativo. |
| RN10.5 | Um ano letivo encerrado nao deve permanecer ativo para novos lancamentos. |
| RN11 | Coordenadores devem visualizar apenas alunos, turmas e cursos vinculados ao seu perfil. |
| RN12 | Diretores de turma devem visualizar apenas dados da sua turma. |
| RN13 | O administrador tem acesso total ao sistema. |
| RN14 | Registros podem ser dos tipos Atraso ou Saida antecipada. |
| RN15 | A autorizacao impressa deve refletir o tipo do registro. |
| RN16 | Ocorrencias devem possuir numero sequencial por aluno. |
| RN17 | Ocorrencias podem ser classificadas por tipo, gravidade e status. |
| RN18 | Anexos devem estar vinculados a uma entidade e a um identificador. |
| RN19 | Backups so podem ser gerados por administrador. |
| RN20 | Alteracoes sensiveis devem gerar log de auditoria. |
| RN21 | Senhas devem ter pelo menos 8 caracteres, com letras e numeros. |
| RN22 | Em producao, SECRET_KEY deve ser uma chave forte e configurada por variavel de ambiente. |
| RN23 | Importacao de alunos deve aceitar data em DD/MM/AAAA e AAAA-MM-DD. |
| RN24 | O curso e o ano escolhidos no modal de importacao definem a turma para todos os alunos importados. |

## 9. Casos de uso

### UC01 - Login no sistema

Ator principal: Usuario cadastrado  
Pre-condicao: Usuario ativo no sistema  
Fluxo principal:

1. Usuario acessa a tela de login.
2. Usuario informa e-mail e senha.
3. Sistema valida as credenciais.
4. Sistema cria sessao segura.
5. Usuario e redirecionado para a tela inicial conforme seu perfil.

### UC02 - Cadastrar aluno

Ator principal: Administrador ou PPDT  
Pre-condicao: Curso e turma cadastrados  
Fluxo principal:

1. Usuario acessa Alunos.
2. Clica em Novo Aluno.
3. Preenche dados do aluno.
4. Seleciona a turma.
5. Salva o cadastro.
6. Sistema registra o aluno e gera auditoria.

### UC03 - Importar alunos

Ator principal: Administrador ou PPDT  
Pre-condicao: Curso e turma cadastrados  
Fluxo principal:

1. Usuario baixa o modelo de importacao.
2. Preenche os dados no arquivo CSV.
3. Seleciona curso e ano no modal de importacao.
4. Envia o arquivo.
5. Sistema valida matricula, data e campos obrigatorios.
6. Sistema cria os alunos validos e informa ignorados.

### UC04 - Registrar atraso ou saida antecipada

Ator principal: Usuario autorizado  
Pre-condicao: Aluno cadastrado  
Fluxo principal:

1. Usuario acessa Registros.
2. Clica em Novo Registro.
3. Busca o aluno pelo nome.
4. Seleciona tipo, data, aula, motivo e documento.
5. Salva o registro.
6. Sistema registra auditoria.
7. Usuario pode imprimir autorizacao.

### UC05 - Registrar ocorrencia

Ator principal: Usuario autorizado  
Pre-condicao: Aluno cadastrado  
Fluxo principal:

1. Usuario acessa Ocorrencias.
2. Clica em Nova Ocorrencia.
3. Busca o aluno pelo nome.
4. Informa tipo, gravidade, descricao, medida e acoes.
5. Indica se responsavel foi notificado.
6. Sistema calcula numero da ocorrencia do aluno.
7. Salva a ocorrencia e registra auditoria.
8. Usuario pode imprimir termo.

### UC06 - Gerar backup

Ator principal: Administrador  
Pre-condicao: Usuario autenticado como admin  
Fluxo principal:

1. Usuario acessa Configuracoes.
2. Abre a aba Backup.
3. Clica em Gerar backup agora.
4. Sistema gera arquivo de backup.
5. Usuario pode baixar o arquivo.

## 10. Fluxos principais

### 10.1 Fluxo de importacao de alunos

```mermaid
flowchart TD
    A["Usuario abre modal de importacao"] --> B["Seleciona curso e ano"]
    B --> C["Seleciona arquivo CSV"]
    C --> D["Sistema le linhas do arquivo"]
    D --> E["Valida matricula e campos obrigatorios"]
    E --> F["Converte data de nascimento"]
    F --> G["Localiza turma pelo curso e ano"]
    G --> H{"Dados validos?"}
    H -- "Sim" --> I["Cria aluno"]
    H -- "Nao" --> J["Ignora linha e registra erro"]
    I --> K["Retorna resumo da importacao"]
    J --> K
```

### 10.2 Fluxo da virada de ano

```mermaid
flowchart TD
    A["Admin solicita previa"] --> B["Sistema conta alunos ativos por ano"]
    B --> C["Sistema verifica turmas destino"]
    C --> D["Admin confirma digitando VIRADA"]
    D --> E{"Aluno esta no 3o ano?"}
    E -- "Sim" --> F["Marca como concluido"]
    E -- "Nao" --> G{"Existe turma destino?"}
    G -- "Sim" --> H["Promove para proximo ano"]
    G -- "Nao" --> I["Mantem aluno sem alteracao"]
    F --> J["Registra auditoria"]
    H --> J
    I --> J
```

### 10.3 Fluxo de permissao de acesso

```mermaid
flowchart TD
    A["Usuario acessa pagina"] --> B{"Esta autenticado?"}
    B -- "Nao" --> C["Redireciona para login"]
    B -- "Sim" --> D["Consulta perfil e permissoes"]
    D --> E{"Tem permissao para modulo?"}
    E -- "Nao" --> F["Redireciona para inicio"]
    E -- "Sim" --> G["Renderiza pagina"]
```

## 11. Arquitetura do sistema

### 11.1 Visao geral

O sistema utiliza arquitetura web monolitica, com backend em FastAPI, templates HTML renderizados no servidor com Jinja2, JavaScript no cliente e banco de dados PostgreSQL.

```mermaid
flowchart LR
    U["Usuario no navegador"] --> F["FastAPI"]
    F --> T["Templates Jinja2"]
    F --> API["Rotas REST /api"]
    API --> S["SQLAlchemy ORM"]
    S --> DB["PostgreSQL"]
    F --> ST["Arquivos static: CSS, JS, imagens"]
    API --> UP["Uploads e anexos"]
    API --> BK["Backups"]
```

### 11.2 Camadas

| Camada | Responsabilidade | Local |
|---|---|---|
| Apresentacao | Telas HTML, CSS e JS | templates, static |
| API | Rotas de negocio e endpoints REST | app/routes |
| Dominio/Dados | Modelos SQLAlchemy | app/models |
| Validacao | Schemas Pydantic | app/schemas |
| Infraestrutura | Banco, sessao, variaveis de ambiente | app/database.py |
| Seguranca | Login, JWT, permissoes, senha | app/auth.py |

## 12. Modelo de dados

### 12.1 Entidades principais

```mermaid
erDiagram
    CURSO ||--o{ TURMA : possui
    TURMA ||--o{ ALUNO : possui
    ALUNO ||--o{ REGISTRO : possui
    ALUNO ||--o{ OCORRENCIA : possui
    USUARIO }o--|| TURMA : "diretor_turma"
    USUARIO }o--o{ CURSO : "coordenador"
    ANEXO }o--|| ALUNO : "pode referenciar"
    ANEXO }o--|| REGISTRO : "pode referenciar"
    ANEXO }o--|| OCORRENCIA : "pode referenciar"
    USUARIO ||--o{ AUDITORIA : gera

    CURSO {
        int id PK
        string nome
        string sigla
    }

    TURMA {
        int id PK
        int ano
        string letra
        int curso_id
    }

    ALUNO {
        int id PK
        string nome
        string matricula UK
        date data_nascimento
        string responsavel
        string contato_responsavel
        int turma_id
        string status
    }

    REGISTRO {
        int id PK
        int aluno_id FK
        date data
        string tipo
        int aula
        string motivo
        boolean tem_documento
        string observacoes
    }

    OCORRENCIA {
        int id PK
        int aluno_id FK
        date data
        string tipo
        string descricao
        string medida
        string gravidade
        string status
        string acoes_tomadas
        string registrado_por
        boolean responsavel_notificado
        int numero_ocorrencia
    }

    USUARIO {
        int id PK
        string nome
        string email UK
        string senha_hash
        string perfil
        int turma_id
        int curso_id
        string curso_ids
        datetime ultimo_login
        int ativo
    }

    ANEXO {
        int id PK
        string entidade
        int entidade_id
        string nome_original
        string caminho
        string content_type
        int tamanho
        int enviado_por_id
        datetime criado_em
    }

    AUDITORIA {
        int id PK
        int usuario_id
        string usuario_nome
        string acao
        string entidade
        int entidade_id
        string detalhes
        string ip
        string user_agent
        datetime criado_em
    }
```

### 12.2 Observacoes sobre chaves

- Aluno usa `id` como chave primaria.
- Matricula do aluno e unica, mas nao e chave primaria.
- Usuario usa `id` como chave primaria e e-mail unico.
- Anexos usam referencia generica por `entidade` e `entidade_id`.
- Curso e turma possuem validacao de duplicidade via regras de negocio.

## 13. Modulos do sistema

### 13.1 Modulo Alunos

Responsavel pelo cadastro, consulta, edicao, exclusao logica por status, importacao, exportacao, historico individual e virada de ano.

### 13.2 Modulo Registros

Responsavel pelo controle de atrasos e saidas antecipadas, incluindo documento, motivo, aula, observacoes e impressao de autorizacao.

### 13.3 Modulo Ocorrencias

Responsavel pelo registro de ocorrencias escolares, classificacao, medidas, acoes, status, responsavel notificado e termo de ocorrencia.

### 13.4 Modulo Dashboard

Responsavel pela exibicao de indicadores gerais, rankings, dados por turma, alunos com maior quantidade de atrasos/ocorrencias e filtros gerenciais.

### 13.5 Modulo Usuarios

Responsavel pelo cadastro e manutencao de usuarios, perfis, vinculo a turma ou cursos e reset de senha.

### 13.6 Modulo Configuracoes

Responsavel por dados da escola, ano letivo, cursos, turmas, permissoes, relatorios, backups, anexos e auditoria.

## 14. Principais rotas

### 14.1 Paginas

| Rota | Tela |
|---|---|
| `/login` | Login |
| `/` | Inicio ou redirecionamento por perfil |
| `/alunos` | Listagem e gestao de alunos |
| `/aluno/{id}` | Perfil individual do aluno |
| `/registros` | Atrasos e saidas antecipadas |
| `/ocorrencias` | Ocorrencias |
| `/dashboard` | Painel gerencial |
| `/usuarios` | Usuarios |
| `/configuracoes` | Configuracoes do sistema |

### 14.2 APIs

| Grupo | Rotas principais |
|---|---|
| Auth | `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`, `/api/auth/trocar-senha` |
| Usuarios | `/api/usuarios/`, `/api/usuarios/{id}`, `/api/usuarios/{id}/resetar-senha` |
| Cursos | `/api/cursos/`, `/api/cursos/{id}` |
| Turmas | `/api/turmas/`, `/api/turmas/{id}` |
| Alunos | `/api/alunos/`, `/api/alunos/{id}`, `/api/alunos/importar-csv`, `/api/alunos/virada-ano` |
| Registros | `/api/registros/`, `/api/registros/{id}`, `/api/registros/aluno/{aluno_id}` |
| Ocorrencias | `/api/ocorrencias/`, `/api/ocorrencias/{id}`, `/api/ocorrencias/aluno/{aluno_id}` |
| Dashboard | `/api/dashboard/gerencial`, `/api/dashboard/resumo`, rankings e graficos |
| Sistema | configuracoes, anos letivos, permissoes, auditoria, backups, anexos e relatorios |

## 15. Seguranca

### 15.1 Autenticacao

- Login por e-mail e senha.
- Senhas armazenadas com hash bcrypt.
- Sessao baseada em token JWT salvo em cookie.
- Token com expiracao de 60 minutos.

### 15.2 Autorizacao

- Controle por perfil.
- Permissoes configuraveis por modulo.
- Restricao de dados por curso para coordenadores.
- Restricao de dados por turma para diretores de turma.

### 15.3 Protecao contra CSRF

- Rotas sensiveis da API exigem token CSRF em operacoes POST, PUT, PATCH e DELETE.
- Login e excecao controlada.

### 15.4 Senhas

- Minimo de 8 caracteres.
- Obrigatorio conter letras e numeros.
- Limite de 72 bytes por restricao tecnica do bcrypt.

### 15.5 Auditoria

O sistema registra acoes relevantes, usuario, entidade, detalhes, data, IP e user agent quando aplicavel.

## 16. Backup e recuperacao

O sistema possui funcionalidade de backup manual, acessivel apenas pelo administrador.

Fluxo:

1. Admin acessa Configuracoes.
2. Abre a aba Backup.
3. Clica em Gerar backup.
4. Sistema gera arquivo de backup.
5. Admin baixa e armazena o arquivo em local seguro.

Recomendacao operacional:

- Gerar backup antes de importacoes grandes.
- Gerar backup antes da virada de ano.
- Guardar copias em mais de um local.
- Em producao, avaliar backup automatico externo.

## 17. Implantacao

### 17.1 Ambiente local

Requisitos:

- Python 3.
- PostgreSQL.
- Dependencias listadas em `requirements.txt`.
- Arquivo `.env` com variaveis de ambiente.

Comando de execucao:

```bash
uvicorn app.main:app --reload
```

### 17.2 Railway

O projeto possui `railway.json` com comando de inicializacao:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Variaveis necessarias:

```env
DATABASE_URL=postgresql://usuario:senha@host:porta/banco
SECRET_KEY=chave_forte_e_aleatoria
APP_ENV=production
ADMIN_EMAIL=admin@teste.com
ADMIN_PASSWORD=admin123
ADMIN_NAME=Administrador
```

Observacao: `ADMIN_PASSWORD` cria a senha inicial apenas quando o banco ainda nao possui nenhum usuario.

## 18. Tecnologias utilizadas

| Tecnologia | Uso |
|---|---|
| Python | Linguagem principal |
| FastAPI | Framework backend |
| SQLAlchemy | ORM e acesso ao banco |
| PostgreSQL | Banco de dados |
| Jinja2 | Templates HTML |
| Bootstrap | Interface e componentes |
| Bootstrap Icons | Icones |
| JavaScript | Interacoes no cliente |
| JWT | Sessao/autenticacao |
| bcrypt | Hash de senhas |
| Railway | Hospedagem de teste/producao |

## 19. Criterios de aceite

- Usuario admin consegue entrar no sistema.
- Admin consegue cadastrar cursos e turmas.
- Admin/PPDT consegue cadastrar aluno em turma existente.
- Sistema impede matricula duplicada.
- Importacao aceita arquivo CSV do modelo.
- Importacao aceita datas em DD/MM/AAAA.
- Coordenador visualiza apenas cursos vinculados.
- Diretor de turma visualiza apenas sua turma.
- Registro de atraso e saida pode ser criado e impresso.
- Ocorrencia pode ser criada e termo pode ser impresso.
- Anexos podem ser vinculados a aluno, registro ou ocorrencia.
- Dashboard carrega indicadores.
- Backup pode ser gerado pelo admin.
- Auditoria registra acoes principais.

## 20. Riscos e pontos de atencao

| Risco | Impacto | Mitigacao |
|---|---|---|
| Falta de backup antes de grandes mudancas | Perda de dados | Gerar backup antes de importacao e virada |
| Erro em planilha de importacao | Alunos ignorados | Validar modelo e revisar erros retornados |
| Permissoes mal configuradas | Usuario acessa mais ou menos do que deveria | Revisar perfis antes do uso oficial |
| Uso de senha fraca | Risco de acesso indevido | Exigir senha forte e troca periodica |
| Hospedagem sem backup automatico | Risco operacional | Manter backup manual e avaliar backup externo |
| Falta de treinamento | Uso incorreto | Criar manual de usuario e treinamento rapido |

## 21. Limitacoes atuais

- Nao ha envio automatico de notificacoes por e-mail ou WhatsApp.
- Nao ha assinatura digital integrada.
- Os relatorios sao gerados como HTML imprimivel.
- O sistema ainda nao possui rotina automatica de backup agendada.
- O controle de anexos depende do armazenamento local da aplicacao/hospedagem.
- Nao ha integracao com sistemas oficiais externos.

## 22. Sugestoes de evolucao

- Envio de notificacoes para responsaveis.
- Historico de comunicacao com responsavel.
- Backup automatico agendado.
- Exportacao PDF mais refinada.
- Painel inicial personalizado por perfil.
- Configuracao dinamica de motivos, medidas e tipos.
- Aprimoramento do ciclo do ano letivo com historico de matriculas por turma em anos anteriores.
- Logs de auditoria com filtros avancados.
- Tela de restauracao de backup.
- Manual do usuario dentro do proprio sistema.

## 23. Glossario

| Termo | Definicao |
|---|---|
| PPDT | Perfil pedagogico com acesso operacional amplo no sistema |
| Registro | Lancamento de atraso ou saida antecipada |
| Ocorrencia | Registro disciplinar ou pedagogico de acompanhamento |
| Anexo | Arquivo vinculado a aluno, registro ou ocorrencia |
| Virada de ano | Processo de promocao de alunos para a serie seguinte |
| Auditoria | Historico das acoes executadas por usuarios |
| Turma destino | Turma para onde o aluno sera promovido na virada de ano |

## 24. Controle de versao da documentacao

| Versao | Data | Descricao |
|---|---|---|
| 0.1 | 05/06/2026 | Criacao inicial da documentacao do projeto |
