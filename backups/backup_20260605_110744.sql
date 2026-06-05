--
-- PostgreSQL database dump
--

\restrict u9wHjj1IQuiqRbHfJWJ1ojFISw3geU0GIhYmUVHgJKr5PRXv7imee4nd1M3aTX4

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.registros DROP CONSTRAINT IF EXISTS registros_aluno_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ocorrencias DROP CONSTRAINT IF EXISTS ocorrencias_aluno_id_fkey;
DROP INDEX IF EXISTS public.ix_usuarios_id;
DROP INDEX IF EXISTS public.ix_turmas_id;
DROP INDEX IF EXISTS public.ix_registros_id;
DROP INDEX IF EXISTS public.ix_permissoes_perfil_id;
DROP INDEX IF EXISTS public.ix_ocorrencias_id;
DROP INDEX IF EXISTS public.ix_cursos_id;
DROP INDEX IF EXISTS public.ix_configuracoes_sistema_id;
DROP INDEX IF EXISTS public.ix_auditoria_id;
DROP INDEX IF EXISTS public.ix_anos_letivos_id;
DROP INDEX IF EXISTS public.ix_anexos_id;
DROP INDEX IF EXISTS public.ix_alunos_id;
ALTER TABLE IF EXISTS ONLY public.usuarios DROP CONSTRAINT IF EXISTS usuarios_pkey;
ALTER TABLE IF EXISTS ONLY public.usuarios DROP CONSTRAINT IF EXISTS usuarios_email_key;
ALTER TABLE IF EXISTS ONLY public.turmas DROP CONSTRAINT IF EXISTS turmas_pkey;
ALTER TABLE IF EXISTS ONLY public.registros DROP CONSTRAINT IF EXISTS registros_pkey;
ALTER TABLE IF EXISTS ONLY public.permissoes_perfil DROP CONSTRAINT IF EXISTS permissoes_perfil_pkey;
ALTER TABLE IF EXISTS ONLY public.permissoes_perfil DROP CONSTRAINT IF EXISTS permissoes_perfil_perfil_key;
ALTER TABLE IF EXISTS ONLY public.ocorrencias DROP CONSTRAINT IF EXISTS ocorrencias_pkey;
ALTER TABLE IF EXISTS ONLY public.cursos DROP CONSTRAINT IF EXISTS cursos_pkey;
ALTER TABLE IF EXISTS ONLY public.configuracoes_sistema DROP CONSTRAINT IF EXISTS configuracoes_sistema_pkey;
ALTER TABLE IF EXISTS ONLY public.configuracoes_sistema DROP CONSTRAINT IF EXISTS configuracoes_sistema_chave_key;
ALTER TABLE IF EXISTS ONLY public.auditoria DROP CONSTRAINT IF EXISTS auditoria_pkey;
ALTER TABLE IF EXISTS ONLY public.anos_letivos DROP CONSTRAINT IF EXISTS anos_letivos_pkey;
ALTER TABLE IF EXISTS ONLY public.anexos DROP CONSTRAINT IF EXISTS anexos_pkey;
ALTER TABLE IF EXISTS ONLY public.alunos DROP CONSTRAINT IF EXISTS alunos_pkey;
ALTER TABLE IF EXISTS ONLY public.alunos DROP CONSTRAINT IF EXISTS alunos_matricula_key;
ALTER TABLE IF EXISTS public.usuarios ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.turmas ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.registros ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.permissoes_perfil ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.ocorrencias ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.cursos ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.configuracoes_sistema ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.auditoria ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.anos_letivos ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.anexos ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.alunos ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.usuarios_id_seq;
DROP TABLE IF EXISTS public.usuarios;
DROP SEQUENCE IF EXISTS public.turmas_id_seq;
DROP TABLE IF EXISTS public.turmas;
DROP SEQUENCE IF EXISTS public.registros_id_seq;
DROP TABLE IF EXISTS public.registros;
DROP SEQUENCE IF EXISTS public.permissoes_perfil_id_seq;
DROP TABLE IF EXISTS public.permissoes_perfil;
DROP SEQUENCE IF EXISTS public.ocorrencias_id_seq;
DROP TABLE IF EXISTS public.ocorrencias;
DROP SEQUENCE IF EXISTS public.cursos_id_seq;
DROP TABLE IF EXISTS public.cursos;
DROP SEQUENCE IF EXISTS public.configuracoes_sistema_id_seq;
DROP TABLE IF EXISTS public.configuracoes_sistema;
DROP SEQUENCE IF EXISTS public.auditoria_id_seq;
DROP TABLE IF EXISTS public.auditoria;
DROP SEQUENCE IF EXISTS public.anos_letivos_id_seq;
DROP TABLE IF EXISTS public.anos_letivos;
DROP SEQUENCE IF EXISTS public.anexos_id_seq;
DROP TABLE IF EXISTS public.anexos;
DROP SEQUENCE IF EXISTS public.alunos_id_seq;
DROP TABLE IF EXISTS public.alunos;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alunos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alunos (
    id integer NOT NULL,
    nome character varying NOT NULL,
    matricula character varying NOT NULL,
    data_nascimento date NOT NULL,
    responsavel character varying NOT NULL,
    contato_responsavel character varying NOT NULL,
    turma_id integer NOT NULL,
    status character varying DEFAULT 'ativo'::character varying NOT NULL
);


ALTER TABLE public.alunos OWNER TO postgres;

--
-- Name: alunos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.alunos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alunos_id_seq OWNER TO postgres;

--
-- Name: alunos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.alunos_id_seq OWNED BY public.alunos.id;


--
-- Name: anexos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.anexos (
    id integer NOT NULL,
    entidade character varying NOT NULL,
    entidade_id integer NOT NULL,
    nome_original character varying NOT NULL,
    nome_arquivo character varying NOT NULL,
    caminho character varying NOT NULL,
    content_type character varying,
    tamanho integer,
    enviado_por_id integer,
    enviado_por_nome character varying,
    criado_em timestamp without time zone NOT NULL
);


ALTER TABLE public.anexos OWNER TO postgres;

--
-- Name: anexos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.anexos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.anexos_id_seq OWNER TO postgres;

--
-- Name: anexos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.anexos_id_seq OWNED BY public.anexos.id;


--
-- Name: anos_letivos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.anos_letivos (
    id integer NOT NULL,
    nome character varying NOT NULL,
    ano integer NOT NULL,
    data_inicio date NOT NULL,
    data_fim date NOT NULL,
    ativo boolean,
    criado_em timestamp without time zone NOT NULL
);


ALTER TABLE public.anos_letivos OWNER TO postgres;

--
-- Name: anos_letivos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.anos_letivos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.anos_letivos_id_seq OWNER TO postgres;

--
-- Name: anos_letivos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.anos_letivos_id_seq OWNED BY public.anos_letivos.id;


--
-- Name: auditoria; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auditoria (
    id integer NOT NULL,
    usuario_id integer,
    usuario_nome character varying,
    acao character varying NOT NULL,
    entidade character varying NOT NULL,
    entidade_id integer,
    detalhes character varying,
    criado_em timestamp without time zone NOT NULL,
    ip character varying,
    user_agent character varying
);


ALTER TABLE public.auditoria OWNER TO postgres;

--
-- Name: auditoria_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.auditoria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auditoria_id_seq OWNER TO postgres;

--
-- Name: auditoria_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.auditoria_id_seq OWNED BY public.auditoria.id;


--
-- Name: configuracoes_sistema; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.configuracoes_sistema (
    id integer NOT NULL,
    chave character varying NOT NULL,
    valor text,
    atualizado_em timestamp without time zone NOT NULL
);


ALTER TABLE public.configuracoes_sistema OWNER TO postgres;

--
-- Name: configuracoes_sistema_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.configuracoes_sistema_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.configuracoes_sistema_id_seq OWNER TO postgres;

--
-- Name: configuracoes_sistema_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.configuracoes_sistema_id_seq OWNED BY public.configuracoes_sistema.id;


--
-- Name: cursos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cursos (
    id integer NOT NULL,
    nome character varying NOT NULL,
    sigla character varying NOT NULL
);


ALTER TABLE public.cursos OWNER TO postgres;

--
-- Name: cursos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.cursos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cursos_id_seq OWNER TO postgres;

--
-- Name: cursos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.cursos_id_seq OWNED BY public.cursos.id;


--
-- Name: ocorrencias; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ocorrencias (
    id integer NOT NULL,
    aluno_id integer NOT NULL,
    data date NOT NULL,
    tipo character varying NOT NULL,
    descricao character varying NOT NULL,
    medida character varying NOT NULL,
    registrado_por character varying NOT NULL,
    responsavel_notificado boolean,
    numero_ocorrencia integer NOT NULL,
    editado_por character varying,
    editado_em timestamp without time zone,
    gravidade character varying DEFAULT 'Leve'::character varying NOT NULL,
    status character varying DEFAULT 'Aberta'::character varying NOT NULL,
    acoes_tomadas character varying
);


ALTER TABLE public.ocorrencias OWNER TO postgres;

--
-- Name: ocorrencias_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ocorrencias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ocorrencias_id_seq OWNER TO postgres;

--
-- Name: ocorrencias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ocorrencias_id_seq OWNED BY public.ocorrencias.id;


--
-- Name: permissoes_perfil; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.permissoes_perfil (
    id integer NOT NULL,
    perfil character varying NOT NULL,
    permissoes text NOT NULL,
    atualizado_em timestamp without time zone NOT NULL
);


ALTER TABLE public.permissoes_perfil OWNER TO postgres;

--
-- Name: permissoes_perfil_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.permissoes_perfil_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.permissoes_perfil_id_seq OWNER TO postgres;

--
-- Name: permissoes_perfil_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.permissoes_perfil_id_seq OWNED BY public.permissoes_perfil.id;


--
-- Name: registros; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.registros (
    id integer NOT NULL,
    aluno_id integer NOT NULL,
    data date NOT NULL,
    tipo character varying NOT NULL,
    aula integer NOT NULL,
    motivo character varying NOT NULL,
    tem_documento boolean,
    observacoes character varying
);


ALTER TABLE public.registros OWNER TO postgres;

--
-- Name: registros_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.registros_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.registros_id_seq OWNER TO postgres;

--
-- Name: registros_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.registros_id_seq OWNED BY public.registros.id;


--
-- Name: turmas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.turmas (
    id integer NOT NULL,
    ano integer NOT NULL,
    letra character varying NOT NULL,
    curso_id integer NOT NULL
);


ALTER TABLE public.turmas OWNER TO postgres;

--
-- Name: turmas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.turmas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.turmas_id_seq OWNER TO postgres;

--
-- Name: turmas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.turmas_id_seq OWNED BY public.turmas.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    nome character varying NOT NULL,
    email character varying NOT NULL,
    senha_hash character varying NOT NULL,
    perfil character varying NOT NULL,
    turma_id integer,
    curso_id integer,
    ativo integer,
    curso_ids character varying,
    ultimo_login timestamp without time zone
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO postgres;

--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: alunos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alunos ALTER COLUMN id SET DEFAULT nextval('public.alunos_id_seq'::regclass);


--
-- Name: anexos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anexos ALTER COLUMN id SET DEFAULT nextval('public.anexos_id_seq'::regclass);


--
-- Name: anos_letivos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anos_letivos ALTER COLUMN id SET DEFAULT nextval('public.anos_letivos_id_seq'::regclass);


--
-- Name: auditoria id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditoria ALTER COLUMN id SET DEFAULT nextval('public.auditoria_id_seq'::regclass);


--
-- Name: configuracoes_sistema id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configuracoes_sistema ALTER COLUMN id SET DEFAULT nextval('public.configuracoes_sistema_id_seq'::regclass);


--
-- Name: cursos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cursos ALTER COLUMN id SET DEFAULT nextval('public.cursos_id_seq'::regclass);


--
-- Name: ocorrencias id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ocorrencias ALTER COLUMN id SET DEFAULT nextval('public.ocorrencias_id_seq'::regclass);


--
-- Name: permissoes_perfil id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permissoes_perfil ALTER COLUMN id SET DEFAULT nextval('public.permissoes_perfil_id_seq'::regclass);


--
-- Name: registros id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.registros ALTER COLUMN id SET DEFAULT nextval('public.registros_id_seq'::regclass);


--
-- Name: turmas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turmas ALTER COLUMN id SET DEFAULT nextval('public.turmas_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Data for Name: alunos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alunos (id, nome, matricula, data_nascimento, responsavel, contato_responsavel, turma_id, status) FROM stdin;
2	Bruno Henrique Oliveira	T1A02	2008-02-06	Responsável Costa	(88) 91651001	1	ativo
3	Camila Vitória Souza	T1A03	2008-03-07	Responsável Lima	(88) 91651002	1	ativo
4	Daniel Souza Pereira	T1A04	2008-04-08	Responsável Almeida	(88) 91651003	1	ativo
5	Eduarda Lima Costa	T1A05	2008-05-09	Responsável Ferreira	(88) 91651004	1	ativo
6	Felipe Alves Lima	T1A06	2008-06-10	Responsável Rodrigues	(88) 91651005	1	ativo
7	Gabriela Rocha Almeida	T1A07	2008-07-11	Responsável Silva	(88) 91651006	1	ativo
8	Henrique Moura Ferreira	T1A08	2008-08-12	Responsável Santos	(88) 91651007	1	ativo
9	Isabela Martins Rodrigues	T1A09	2008-09-13	Responsável Oliveira	(88) 91651008	1	ativo
10	João Pedro Silva	T1A10	2008-10-14	Responsável Souza	(88) 91651009	1	ativo
11	Ana Clara Pereira	T1B01	2008-01-05	Responsável Almeida	(88) 91661000	4	ativo
12	Bruno Henrique Costa	T1B02	2008-02-06	Responsável Ferreira	(88) 91661001	4	ativo
13	Camila Vitória Lima	T1B03	2008-03-07	Responsável Rodrigues	(88) 91661002	4	ativo
14	Daniel Souza Almeida	T1B04	2008-04-08	Responsável Silva	(88) 91661003	4	ativo
15	Eduarda Lima Ferreira	T1B05	2008-05-09	Responsável Santos	(88) 91661004	4	ativo
16	Felipe Alves Rodrigues	T1B06	2008-06-10	Responsável Oliveira	(88) 91661005	4	ativo
17	Gabriela Rocha Silva	T1B07	2008-07-11	Responsável Souza	(88) 91661006	4	ativo
18	Henrique Moura Santos	T1B08	2008-08-12	Responsável Pereira	(88) 91661007	4	ativo
19	Isabela Martins Oliveira	T1B09	2008-09-13	Responsável Costa	(88) 91661008	4	ativo
20	João Pedro Souza	T1B10	2008-10-14	Responsável Lima	(88) 91661009	4	ativo
21	Ana Clara Almeida	T1C01	2008-01-05	Responsável Silva	(88) 91671000	7	ativo
22	Bruno Henrique Ferreira	T1C02	2008-02-06	Responsável Santos	(88) 91671001	7	ativo
23	Camila Vitória Rodrigues	T1C03	2008-03-07	Responsável Oliveira	(88) 91671002	7	ativo
24	Daniel Souza Silva	T1C04	2008-04-08	Responsável Souza	(88) 91671003	7	ativo
25	Eduarda Lima Santos	T1C05	2008-05-09	Responsável Pereira	(88) 91671004	7	ativo
26	Felipe Alves Oliveira	T1C06	2008-06-10	Responsável Costa	(88) 91671005	7	ativo
27	Gabriela Rocha Souza	T1C07	2008-07-11	Responsável Lima	(88) 91671006	7	ativo
28	Henrique Moura Pereira	T1C08	2008-08-12	Responsável Almeida	(88) 91671007	7	ativo
29	Isabela Martins Costa	T1C09	2008-09-13	Responsável Ferreira	(88) 91671008	7	ativo
30	João Pedro Lima	T1C10	2008-10-14	Responsável Rodrigues	(88) 91671009	7	ativo
31	Ana Clara Silva	T1D01	2008-01-05	Responsável Souza	(88) 91681000	10	ativo
32	Bruno Henrique Santos	T1D02	2008-02-06	Responsável Pereira	(88) 91681001	10	ativo
33	Camila Vitória Oliveira	T1D03	2008-03-07	Responsável Costa	(88) 91681002	10	ativo
34	Daniel Souza Souza	T1D04	2008-04-08	Responsável Lima	(88) 91681003	10	ativo
35	Eduarda Lima Pereira	T1D05	2008-05-09	Responsável Almeida	(88) 91681004	10	ativo
36	Felipe Alves Costa	T1D06	2008-06-10	Responsável Ferreira	(88) 91681005	10	ativo
37	Gabriela Rocha Lima	T1D07	2008-07-11	Responsável Rodrigues	(88) 91681006	10	ativo
38	Henrique Moura Almeida	T1D08	2008-08-12	Responsável Silva	(88) 91681007	10	ativo
39	Isabela Martins Ferreira	T1D09	2008-09-13	Responsável Santos	(88) 91681008	10	ativo
40	João Pedro Rodrigues	T1D10	2008-10-14	Responsável Oliveira	(88) 91681009	10	ativo
41	Ana Clara Oliveira	T2A01	2007-01-05	Responsável Costa	(88) 92651000	2	ativo
42	Bruno Henrique Souza	T2A02	2007-02-06	Responsável Lima	(88) 92651001	2	ativo
43	Camila Vitória Pereira	T2A03	2007-03-07	Responsável Almeida	(88) 92651002	2	ativo
44	Daniel Souza Costa	T2A04	2007-04-08	Responsável Ferreira	(88) 92651003	2	ativo
45	Eduarda Lima Lima	T2A05	2007-05-09	Responsável Rodrigues	(88) 92651004	2	ativo
46	Felipe Alves Almeida	T2A06	2007-06-10	Responsável Silva	(88) 92651005	2	ativo
47	Gabriela Rocha Ferreira	T2A07	2007-07-11	Responsável Santos	(88) 92651006	2	ativo
48	Henrique Moura Rodrigues	T2A08	2007-08-12	Responsável Oliveira	(88) 92651007	2	ativo
49	Isabela Martins Silva	T2A09	2007-09-13	Responsável Souza	(88) 92651008	2	ativo
50	João Pedro Santos	T2A10	2007-10-14	Responsável Pereira	(88) 92651009	2	ativo
51	Ana Clara Costa	T2B01	2007-01-05	Responsável Ferreira	(88) 92661000	5	ativo
52	Bruno Henrique Lima	T2B02	2007-02-06	Responsável Rodrigues	(88) 92661001	5	ativo
53	Camila Vitória Almeida	T2B03	2007-03-07	Responsável Silva	(88) 92661002	5	ativo
54	Daniel Souza Ferreira	T2B04	2007-04-08	Responsável Santos	(88) 92661003	5	ativo
55	Eduarda Lima Rodrigues	T2B05	2007-05-09	Responsável Oliveira	(88) 92661004	5	ativo
56	Felipe Alves Silva	T2B06	2007-06-10	Responsável Souza	(88) 92661005	5	ativo
57	Gabriela Rocha Santos	T2B07	2007-07-11	Responsável Pereira	(88) 92661006	5	ativo
58	Henrique Moura Oliveira	T2B08	2007-08-12	Responsável Costa	(88) 92661007	5	ativo
59	Isabela Martins Souza	T2B09	2007-09-13	Responsável Lima	(88) 92661008	5	ativo
60	João Pedro Pereira	T2B10	2007-10-14	Responsável Almeida	(88) 92661009	5	ativo
61	Ana Clara Ferreira	T2C01	2007-01-05	Responsável Santos	(88) 92671000	8	ativo
62	Bruno Henrique Rodrigues	T2C02	2007-02-06	Responsável Oliveira	(88) 92671001	8	ativo
63	Camila Vitória Silva	T2C03	2007-03-07	Responsável Souza	(88) 92671002	8	ativo
64	Daniel Souza Santos	T2C04	2007-04-08	Responsável Pereira	(88) 92671003	8	ativo
65	Eduarda Lima Oliveira	T2C05	2007-05-09	Responsável Costa	(88) 92671004	8	ativo
66	Felipe Alves Souza	T2C06	2007-06-10	Responsável Lima	(88) 92671005	8	ativo
67	Gabriela Rocha Pereira	T2C07	2007-07-11	Responsável Almeida	(88) 92671006	8	ativo
68	Henrique Moura Costa	T2C08	2007-08-12	Responsável Ferreira	(88) 92671007	8	ativo
69	Isabela Martins Lima	T2C09	2007-09-13	Responsável Rodrigues	(88) 92671008	8	ativo
70	João Pedro Almeida	T2C10	2007-10-14	Responsável Silva	(88) 92671009	8	ativo
71	Ana Clara Santos	T2D01	2007-01-05	Responsável Pereira	(88) 92681000	11	ativo
72	Bruno Henrique Oliveira	T2D02	2007-02-06	Responsável Costa	(88) 92681001	11	ativo
73	Camila Vitória Souza	T2D03	2007-03-07	Responsável Lima	(88) 92681002	11	ativo
74	Daniel Souza Pereira	T2D04	2007-04-08	Responsável Almeida	(88) 92681003	11	ativo
75	Eduarda Lima Costa	T2D05	2007-05-09	Responsável Ferreira	(88) 92681004	11	ativo
76	Felipe Alves Lima	T2D06	2007-06-10	Responsável Rodrigues	(88) 92681005	11	ativo
77	Gabriela Rocha Almeida	T2D07	2007-07-11	Responsável Silva	(88) 92681006	11	ativo
78	Henrique Moura Ferreira	T2D08	2007-08-12	Responsável Santos	(88) 92681007	11	ativo
79	Isabela Martins Rodrigues	T2D09	2007-09-13	Responsável Oliveira	(88) 92681008	11	ativo
80	João Pedro Silva	T2D10	2007-10-14	Responsável Souza	(88) 92681009	11	ativo
81	Ana Clara Souza	T3A01	2006-01-05	Responsável Lima	(88) 93651000	3	ativo
82	Bruno Henrique Pereira	T3A02	2006-02-06	Responsável Almeida	(88) 93651001	3	ativo
83	Camila Vitória Costa	T3A03	2006-03-07	Responsável Ferreira	(88) 93651002	3	ativo
84	Daniel Souza Lima	T3A04	2006-04-08	Responsável Rodrigues	(88) 93651003	3	ativo
85	Eduarda Lima Almeida	T3A05	2006-05-09	Responsável Silva	(88) 93651004	3	ativo
86	Felipe Alves Ferreira	T3A06	2006-06-10	Responsável Santos	(88) 93651005	3	ativo
87	Gabriela Rocha Rodrigues	T3A07	2006-07-11	Responsável Oliveira	(88) 93651006	3	ativo
88	Henrique Moura Silva	T3A08	2006-08-12	Responsável Souza	(88) 93651007	3	ativo
89	Isabela Martins Santos	T3A09	2006-09-13	Responsável Pereira	(88) 93651008	3	ativo
90	João Pedro Oliveira	T3A10	2006-10-14	Responsável Costa	(88) 93651009	3	ativo
91	Ana Clara Lima	T3B01	2006-01-05	Responsável Rodrigues	(88) 93661000	6	ativo
92	Bruno Henrique Almeida	T3B02	2006-02-06	Responsável Silva	(88) 93661001	6	ativo
93	Camila Vitória Ferreira	T3B03	2006-03-07	Responsável Santos	(88) 93661002	6	ativo
94	Daniel Souza Rodrigues	T3B04	2006-04-08	Responsável Oliveira	(88) 93661003	6	ativo
95	Eduarda Lima Silva	T3B05	2006-05-09	Responsável Souza	(88) 93661004	6	ativo
96	Felipe Alves Santos	T3B06	2006-06-10	Responsável Pereira	(88) 93661005	6	ativo
97	Gabriela Rocha Oliveira	T3B07	2006-07-11	Responsável Costa	(88) 93661006	6	ativo
98	Henrique Moura Souza	T3B08	2006-08-12	Responsável Lima	(88) 93661007	6	ativo
99	Isabela Martins Pereira	T3B09	2006-09-13	Responsável Almeida	(88) 93661008	6	ativo
100	João Pedro Costa	T3B10	2006-10-14	Responsável Ferreira	(88) 93661009	6	ativo
101	Ana Clara Rodrigues	T3C01	2006-01-05	Responsável Oliveira	(88) 93671000	9	ativo
102	Bruno Henrique Silva	T3C02	2006-02-06	Responsável Souza	(88) 93671001	9	ativo
103	Camila Vitória Santos	T3C03	2006-03-07	Responsável Pereira	(88) 93671002	9	ativo
104	Daniel Souza Oliveira	T3C04	2006-04-08	Responsável Costa	(88) 93671003	9	ativo
105	Eduarda Lima Souza	T3C05	2006-05-09	Responsável Lima	(88) 93671004	9	ativo
106	Felipe Alves Pereira	T3C06	2006-06-10	Responsável Almeida	(88) 93671005	9	ativo
107	Gabriela Rocha Costa	T3C07	2006-07-11	Responsável Ferreira	(88) 93671006	9	ativo
108	Henrique Moura Lima	T3C08	2006-08-12	Responsável Rodrigues	(88) 93671007	9	ativo
109	Isabela Martins Almeida	T3C09	2006-09-13	Responsável Silva	(88) 93671008	9	ativo
110	João Pedro Ferreira	T3C10	2006-10-14	Responsável Santos	(88) 93671009	9	ativo
111	Ana Clara Oliveira	T3D01	2006-01-05	Responsável Costa	(88) 93681000	12	ativo
112	Bruno Henrique Souza	T3D02	2006-02-06	Responsável Lima	(88) 93681001	12	ativo
113	Camila Vitória Pereira	T3D03	2006-03-07	Responsável Almeida	(88) 93681002	12	ativo
114	Daniel Souza Costa	T3D04	2006-04-08	Responsável Ferreira	(88) 93681003	12	ativo
115	Eduarda Lima Lima	T3D05	2006-05-09	Responsável Rodrigues	(88) 93681004	12	ativo
116	Felipe Alves Almeida	T3D06	2006-06-10	Responsável Silva	(88) 93681005	12	ativo
117	Gabriela Rocha Ferreira	T3D07	2006-07-11	Responsável Santos	(88) 93681006	12	ativo
118	Henrique Moura Rodrigues	T3D08	2006-08-12	Responsável Oliveira	(88) 93681007	12	ativo
119	Isabela Martins Silva	T3D09	2006-09-13	Responsável Souza	(88) 93681008	12	ativo
120	João Pedro Santos	T3D10	2006-10-14	Responsável Pereira	(88) 93681009	12	ativo
1	Ana Clara Santos	T1A01	2008-01-05	Respons??vel Pereira	(88) 91651000	1	ativo
\.


--
-- Data for Name: anexos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.anexos (id, entidade, entidade_id, nome_original, nome_arquivo, caminho, content_type, tamanho, enviado_por_id, enviado_por_nome, criado_em) FROM stdin;
\.


--
-- Data for Name: anos_letivos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.anos_letivos (id, nome, ano, data_inicio, data_fim, ativo, criado_em) FROM stdin;
\.


--
-- Data for Name: auditoria; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auditoria (id, usuario_id, usuario_nome, acao, entidade, entidade_id, detalhes, criado_em, ip, user_agent) FROM stdin;
1	1	Administrador	importou_csv	aluno	\N	criados=1; ignorados=0	2026-06-04 14:09:10.865548	\N	\N
2	1	Administrador	excluiu	aluno	121	matricula=IMPORT-TESTE-001	2026-06-04 14:09:51.151963	\N	\N
3	1	Administrador	importou_csv	aluno	\N	criados=1; ignorados=0	2026-06-04 14:17:06.238612	\N	\N
4	1	Administrador	excluiu	aluno	122	matricula=IMPORT-EXCEL-001	2026-06-04 14:17:26.12943	\N	\N
5	1	Administrador	importou_csv	aluno	\N	criados=1; ignorados=0	2026-06-04 14:26:15.598042	\N	\N
6	1	Administrador	excluiu	aluno	123	matricula=IMPORT-MODAL-001	2026-06-04 14:26:34.456127	\N	\N
7	1	Administrador	gerou	backup	\N	backup_20260605_094151.sql	2026-06-05 09:41:52.296687	127.0.0.1	Mozilla/5.0 (Windows NT; Windows NT 10.0; pt-BR) WindowsPowerShell/5.1.26100.8521
8	1	Administrador	salvou	permissoes	\N	coordenador	2026-06-05 09:51:49.062116	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36
9	1	Administrador	salvou	permissoes	\N	coordenador	2026-06-05 10:03:25.102606	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36
10	1	Administrador	criou	usuario	4	email=camila@gmail.com; perfil=coordenador	2026-06-05 11:06:07.990048	\N	\N
\.


--
-- Data for Name: configuracoes_sistema; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.configuracoes_sistema (id, chave, valor, atualizado_em) FROM stdin;
1	escola_nome	EEEP Governador Virgilio Tavora	2026-06-05 09:25:44.582144
2	escola_endereco	R. Pergentino Silva, S/N - Seminario, Crato-CE	2026-06-05 09:25:44.582151
3	escola_telefone		2026-06-05 09:25:44.582153
4	responsavel_sistema	Secretaria / Coordenacao	2026-06-05 09:25:44.582154
\.


--
-- Data for Name: cursos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cursos (id, nome, sigla) FROM stdin;
1	Enfermagem	ENF
2	Informática	INF
3	Redes de Computadores	RED
4	Regência	REG
\.


--
-- Data for Name: ocorrencias; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ocorrencias (id, aluno_id, data, tipo, descricao, medida, registrado_por, responsavel_notificado, numero_ocorrencia, editado_por, editado_em, gravidade, status, acoes_tomadas) FROM stdin;
1	119	2026-06-04	Uso de celular indevido	aluna estava usando aparelho celular indeviddamente na aula do prof. pires	Só registro		f	1	\N	\N	Leve	Aberta	\N
2	29	2026-06-05	Dano ao patrimônio	o aluno querbrou a mesa do pário 	Só registro	David	f	1	\N	\N	Grave	Em acompanhamento	dkjdkfj dfja djfh sdf
\.


--
-- Data for Name: permissoes_perfil; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.permissoes_perfil (id, perfil, permissoes, atualizado_em) FROM stdin;
1	admin	["*"]	2026-06-05 09:25:44.627743
2	ppdt	["alunos", "registros", "ocorrencias", "dashboard", "relatorios"]	2026-06-05 09:25:44.627748
3	biblioteca	["registros", "dashboard"]	2026-06-05 09:25:44.627749
5	diretor_turma	["alunos", "registros", "ocorrencias", "dashboard", "relatorios"]	2026-06-05 09:25:44.627751
4	coordenador	["alunos", "registros", "ocorrencias", "dashboard", "relatorios"]	2026-06-05 10:03:25.100446
\.


--
-- Data for Name: registros; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.registros (id, aluno_id, data, tipo, aula, motivo, tem_documento, observacoes) FROM stdin;
1	20	2026-06-03	Atraso	2	Consulta médica	t	
2	9	2026-06-04	Saída antecipada	5	Consulta médica	f	
3	6	2026-06-04	Atraso	2	Compromisso familiar	f	
4	9	2026-06-05	Atraso	3	Exame médico	t	
\.


--
-- Data for Name: turmas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.turmas (id, ano, letra, curso_id) FROM stdin;
1	1	A	1
2	2	A	1
3	3	A	1
4	1	B	2
5	2	B	2
6	3	B	2
7	1	C	3
8	2	C	3
9	3	C	3
10	1	D	4
11	2	D	4
12	3	D	4
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (id, nome, email, senha_hash, perfil, turma_id, curso_id, ativo, curso_ids, ultimo_login) FROM stdin;
3	Josniel Pires da Silva	pires@gmail.com	$2b$12$H9ZiQg8YW9l2sfRV8qkkuOUAIbM3V0vYmw.qreAGYjVuCAyt8FG8S	coordenador	\N	2	1	2,3	\N
2	Josniel Pires da Silva	josniel@gmail.com	$2b$12$N48DzeQt6tzGl/1xSUCQ3eOLA0Hy/dalktgZWH6k.oIfr1PcHRyf6	coordenador	\N	2	1	2,3	2026-06-05 10:59:42.551182
1	Administrador	admin@teste.com	$2b$12$Iggwzoxu46qopdpFuswJzOgaRSfDqzKFyI1oV50tdVbf53blcLQFy	admin	\N	\N	1	\N	2026-06-05 11:05:12.532278
4	Camila 	camila@gmail.com	$2b$12$vgTxvbmTaWKkB4sBY3ZPquwLDHm0UwMM5FYmDcjAFHm7i8VSi7b/q	coordenador	\N	1	1	1	2026-06-05 11:06:31.001216
\.


--
-- Name: alunos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.alunos_id_seq', 123, true);


--
-- Name: anexos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.anexos_id_seq', 1, false);


--
-- Name: anos_letivos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.anos_letivos_id_seq', 1, false);


--
-- Name: auditoria_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auditoria_id_seq', 10, true);


--
-- Name: configuracoes_sistema_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.configuracoes_sistema_id_seq', 4, true);


--
-- Name: cursos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.cursos_id_seq', 4, true);


--
-- Name: ocorrencias_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ocorrencias_id_seq', 2, true);


--
-- Name: permissoes_perfil_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.permissoes_perfil_id_seq', 5, true);


--
-- Name: registros_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.registros_id_seq', 4, true);


--
-- Name: turmas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.turmas_id_seq', 12, true);


--
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 4, true);


--
-- Name: alunos alunos_matricula_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alunos
    ADD CONSTRAINT alunos_matricula_key UNIQUE (matricula);


--
-- Name: alunos alunos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alunos
    ADD CONSTRAINT alunos_pkey PRIMARY KEY (id);


--
-- Name: anexos anexos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anexos
    ADD CONSTRAINT anexos_pkey PRIMARY KEY (id);


--
-- Name: anos_letivos anos_letivos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anos_letivos
    ADD CONSTRAINT anos_letivos_pkey PRIMARY KEY (id);


--
-- Name: auditoria auditoria_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT auditoria_pkey PRIMARY KEY (id);


--
-- Name: configuracoes_sistema configuracoes_sistema_chave_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configuracoes_sistema
    ADD CONSTRAINT configuracoes_sistema_chave_key UNIQUE (chave);


--
-- Name: configuracoes_sistema configuracoes_sistema_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configuracoes_sistema
    ADD CONSTRAINT configuracoes_sistema_pkey PRIMARY KEY (id);


--
-- Name: cursos cursos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cursos
    ADD CONSTRAINT cursos_pkey PRIMARY KEY (id);


--
-- Name: ocorrencias ocorrencias_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ocorrencias
    ADD CONSTRAINT ocorrencias_pkey PRIMARY KEY (id);


--
-- Name: permissoes_perfil permissoes_perfil_perfil_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permissoes_perfil
    ADD CONSTRAINT permissoes_perfil_perfil_key UNIQUE (perfil);


--
-- Name: permissoes_perfil permissoes_perfil_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permissoes_perfil
    ADD CONSTRAINT permissoes_perfil_pkey PRIMARY KEY (id);


--
-- Name: registros registros_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.registros
    ADD CONSTRAINT registros_pkey PRIMARY KEY (id);


--
-- Name: turmas turmas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turmas
    ADD CONSTRAINT turmas_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: ix_alunos_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_alunos_id ON public.alunos USING btree (id);


--
-- Name: ix_anexos_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_anexos_id ON public.anexos USING btree (id);


--
-- Name: ix_anos_letivos_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_anos_letivos_id ON public.anos_letivos USING btree (id);


--
-- Name: ix_auditoria_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_auditoria_id ON public.auditoria USING btree (id);


--
-- Name: ix_configuracoes_sistema_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_configuracoes_sistema_id ON public.configuracoes_sistema USING btree (id);


--
-- Name: ix_cursos_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_cursos_id ON public.cursos USING btree (id);


--
-- Name: ix_ocorrencias_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ocorrencias_id ON public.ocorrencias USING btree (id);


--
-- Name: ix_permissoes_perfil_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_permissoes_perfil_id ON public.permissoes_perfil USING btree (id);


--
-- Name: ix_registros_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_registros_id ON public.registros USING btree (id);


--
-- Name: ix_turmas_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_turmas_id ON public.turmas USING btree (id);


--
-- Name: ix_usuarios_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_usuarios_id ON public.usuarios USING btree (id);


--
-- Name: ocorrencias ocorrencias_aluno_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ocorrencias
    ADD CONSTRAINT ocorrencias_aluno_id_fkey FOREIGN KEY (aluno_id) REFERENCES public.alunos(id);


--
-- Name: registros registros_aluno_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.registros
    ADD CONSTRAINT registros_aluno_id_fkey FOREIGN KEY (aluno_id) REFERENCES public.alunos(id);


--
-- PostgreSQL database dump complete
--

\unrestrict u9wHjj1IQuiqRbHfJWJ1ojFISw3geU0GIhYmUVHgJKr5PRXv7imee4nd1M3aTX4

