from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from app.database import engine, Base
from sqlalchemy import inspect, text
from app.models import aluno, registro, ocorrencia, usuario, auditoria, sistema
from app.routes import aluno as aluno_routes
from app.routes import registro as registro_routes
from app.routes import ocorrencia as ocorrencia_routes
from app.routes import dashboard as dashboard_routes
from app.routes import auth as auth_routes
from app.routes import sistema as sistema_routes
from app.auth import get_usuario_atual, tem_permissao, hash_senha
from app.models.usuario import Usuario
from app.database import SessionLocal
from datetime import date
import os

Base.metadata.create_all(bind=engine)

def garantir_colunas_ocorrencias():
    inspector = inspect(engine)
    if not inspector.has_table("ocorrencias"):
        return

    colunas = {coluna["name"] for coluna in inspector.get_columns("ocorrencias")}
    comandos = []
    if "gravidade" not in colunas:
        comandos.append("ALTER TABLE ocorrencias ADD COLUMN gravidade VARCHAR DEFAULT 'Leve' NOT NULL")
    if "status" not in colunas:
        comandos.append("ALTER TABLE ocorrencias ADD COLUMN status VARCHAR DEFAULT 'Aberta' NOT NULL")
    if "acoes_tomadas" not in colunas:
        comandos.append("ALTER TABLE ocorrencias ADD COLUMN acoes_tomadas VARCHAR")

    if comandos:
        with engine.begin() as conn:
            for comando in comandos:
                conn.execute(text(comando))

garantir_colunas_ocorrencias()

def garantir_colunas_usuarios():
    inspector = inspect(engine)
    if not inspector.has_table("usuarios"):
        return

    colunas = {coluna["name"] for coluna in inspector.get_columns("usuarios")}
    comandos = []
    if "curso_ids" not in colunas:
        comandos.append("ALTER TABLE usuarios ADD COLUMN curso_ids VARCHAR")
    if "ultimo_login" not in colunas:
        comandos.append("ALTER TABLE usuarios ADD COLUMN ultimo_login TIMESTAMP")

    if comandos:
        with engine.begin() as conn:
            for comando in comandos:
                conn.execute(text(comando))
            if "curso_ids" not in colunas:
                conn.execute(text("UPDATE usuarios SET curso_ids = CAST(curso_id AS VARCHAR) WHERE curso_id IS NOT NULL"))

garantir_colunas_usuarios()

def garantir_colunas_auditoria():
    inspector = inspect(engine)
    if not inspector.has_table("auditoria"):
        return

    colunas = {coluna["name"] for coluna in inspector.get_columns("auditoria")}
    comandos = []
    if "ip" not in colunas:
        comandos.append("ALTER TABLE auditoria ADD COLUMN ip VARCHAR")
    if "user_agent" not in colunas:
        comandos.append("ALTER TABLE auditoria ADD COLUMN user_agent VARCHAR")
    if comandos:
        with engine.begin() as conn:
            for comando in comandos:
                conn.execute(text(comando))

garantir_colunas_auditoria()

def garantir_colunas_ciclo_ano_letivo():
    inspector = inspect(engine)
    comandos = []

    tabelas_com_ano = ["alunos", "registros", "ocorrencias"]
    for tabela in tabelas_com_ano:
        if not inspector.has_table(tabela):
            continue
        colunas = {coluna["name"] for coluna in inspector.get_columns(tabela)}
        if "ano_letivo_id" not in colunas:
            comandos.append(f"ALTER TABLE {tabela} ADD COLUMN ano_letivo_id INTEGER")

    if inspector.has_table("anos_letivos"):
        colunas_ano = {coluna["name"] for coluna in inspector.get_columns("anos_letivos")}
        if "encerrado" not in colunas_ano:
            comandos.append("ALTER TABLE anos_letivos ADD COLUMN encerrado BOOLEAN DEFAULT FALSE NOT NULL")

    if comandos:
        with engine.begin() as conn:
            for comando in comandos:
                conn.execute(text(comando))

garantir_colunas_ciclo_ano_letivo()

def garantir_ano_letivo_atual_e_vinculos():
    db = SessionLocal()
    try:
        ano = db.query(sistema.AnoLetivo).filter(sistema.AnoLetivo.ativo == True).first()
        if not ano:
            hoje = date.today()
            ano = sistema.AnoLetivo(
                nome=f"Ano Letivo {hoje.year}",
                ano=hoje.year,
                data_inicio=date(hoje.year, 1, 1),
                data_fim=date(hoje.year, 12, 31),
                ativo=True,
            )
            db.add(ano)
            db.flush()
        db.query(aluno.Aluno).filter(aluno.Aluno.ano_letivo_id == None).update({aluno.Aluno.ano_letivo_id: ano.id})
        db.query(registro.Registro).filter(registro.Registro.ano_letivo_id == None).update({registro.Registro.ano_letivo_id: ano.id})
        db.query(ocorrencia.Ocorrencia).filter(ocorrencia.Ocorrencia.ano_letivo_id == None).update({ocorrencia.Ocorrencia.ano_letivo_id: ano.id})
        alunos_sem_historico = db.query(aluno.Aluno).filter(
            ~db.query(sistema.MatriculaHistorico)
                .filter(sistema.MatriculaHistorico.aluno_id == aluno.Aluno.id)
                .exists()
        ).all()
        for item in alunos_sem_historico:
            if item.turma_id:
                db.add(sistema.MatriculaHistorico(
                    aluno_id=item.id,
                    turma_id=item.turma_id,
                    ano_letivo_id=item.ano_letivo_id or ano.id,
                    status=item.status or "ativo",
                    data_inicio=ano.data_inicio,
                ))
        db.commit()
    finally:
        db.close()

garantir_ano_letivo_atual_e_vinculos()

def garantir_admin_inicial():
    db = SessionLocal()
    try:
        if db.query(Usuario).count() > 0:
            return
        email = os.getenv("ADMIN_EMAIL", "admin@teste.com")
        senha = os.getenv("ADMIN_PASSWORD", "Admin1234")
        if len(senha.encode("utf-8")) > 72:
            senha = senha.encode("utf-8")[:72].decode("utf-8", errors="ignore")
        nome = os.getenv("ADMIN_NAME", "Administrador")
        db.add(Usuario(
            nome=nome,
            email=email,
            senha_hash=hash_senha(senha),
            perfil="admin",
            ativo=1,
        ))
        db.commit()
    finally:
        db.close()

garantir_admin_inicial()

app = FastAPI(title="Sistema de Gestão Escolar")

@app.middleware("http")
async def proteger_csrf(request: Request, call_next):
    metodos_protegidos = {"POST", "PUT", "PATCH", "DELETE"}
    rotas_livres = {"/api/auth/login"}
    if request.method in metodos_protegidos and request.url.path.startswith("/api") and request.url.path not in rotas_livres:
        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("x-csrf-token")
        if not csrf_cookie or csrf_cookie != csrf_header:
            return JSONResponse({"detail": "Token de seguranca invalido"}, status_code=403)
    return await call_next(request)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(aluno_routes.router, prefix="/api", tags=["Alunos"])
app.include_router(registro_routes.router, prefix="/api", tags=["Registros"])
app.include_router(ocorrencia_routes.router, prefix="/api", tags=["Ocorrências"])
app.include_router(dashboard_routes.router, prefix="/api", tags=["Dashboard"])
app.include_router(auth_routes.router, prefix="/api", tags=["Auth"])
app.include_router(sistema_routes.router, prefix="/api", tags=["Sistema"])

def get_usuario_logado(request: Request):
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        return get_usuario_atual(request, db)
    except:
        return None

def pode_acessar(usuario: Usuario, modulo: str):
    db = None
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        return tem_permissao(db, usuario, modulo)
    except:
        return usuario.perfil == "admin"
    finally:
        if db:
            db.close()

def contexto_usuario(usuario: Usuario, extra: dict | None = None):
    permissoes = {
        "alunos": pode_acessar(usuario, "alunos"),
        "registros": pode_acessar(usuario, "registros"),
        "ocorrencias": pode_acessar(usuario, "ocorrencias"),
        "dashboard": pode_acessar(usuario, "dashboard"),
        "usuarios": pode_acessar(usuario, "usuarios"),
        "configuracoes": pode_acessar(usuario, "configuracoes"),
    }
    contexto = {"usuario": usuario.nome, "perfil": usuario.perfil, "permissoes": permissoes}
    if extra:
        contexto.update(extra)
    return contexto

@app.get("/login")
async def pagina_login(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.get("/")
async def root(request: Request):
    usuario = get_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "index.html", contexto_usuario(usuario))

@app.get("/manual")
async def pagina_manual(request: Request):
    usuario = get_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "manual.html", contexto_usuario(usuario))

@app.get("/alunos")
async def pagina_alunos(request: Request):
    usuario = get_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login")
    if not pode_acessar(usuario, "alunos"):
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "alunos.html", contexto_usuario(usuario))

@app.get("/registros")
async def pagina_registros(request: Request):
    usuario = get_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login")
    if not pode_acessar(usuario, "registros"):
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "registros.html", contexto_usuario(usuario))

@app.get("/ocorrencias")
async def pagina_ocorrencias(request: Request):
    usuario = get_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login")
    if not pode_acessar(usuario, "ocorrencias"):
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "ocorrencias.html", contexto_usuario(usuario))

@app.get("/dashboard")
async def pagina_dashboard(request: Request):
    usuario = get_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login")
    if not pode_acessar(usuario, "dashboard"):
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "dashboard.html", contexto_usuario(usuario))

@app.get("/aluno/{aluno_id}")
async def pagina_aluno(request: Request, aluno_id: int):
    usuario = get_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login")
    if not pode_acessar(usuario, "alunos"):
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "aluno.html", contexto_usuario(usuario, {"aluno_id": aluno_id}))

@app.get("/usuarios")
async def pagina_usuarios(request: Request):
    usuario = get_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login")
    if not pode_acessar(usuario, "usuarios"):
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "usuarios.html", contexto_usuario(usuario))

@app.get("/configuracoes")
async def pagina_configuracoes(request: Request):
    usuario = get_usuario_logado(request)
    if not usuario:
        return RedirectResponse(url="/login")
    if not pode_acessar(usuario, "configuracoes"):
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "configuracoes.html", contexto_usuario(usuario))
