import json
import os
import shutil
import subprocess
import uuid
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_usuario_atual, tem_permissao
from app.database import get_db
from app.models.aluno import Aluno, Curso, Turma
from app.models.auditoria import Auditoria
from app.models.ocorrencia import Ocorrencia
from app.models.registro import Registro
from app.models.sistema import Anexo, AnoLetivo, ConfiguracaoSistema, PermissaoPerfil
from app.models.usuario import Usuario
from app.services.ano_letivo import obter_ano_letivo_ativo

router = APIRouter()

UPLOAD_DIR = Path("uploads/anexos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
EXTENSOES_ANEXO_PERMITIDAS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".doc", ".docx"}
TAMANHO_MAX_ANEXO = 10 * 1024 * 1024

PERMISSOES_PADRAO = {
    "admin": ["*"],
    "ppdt": ["alunos", "registros", "ocorrencias", "dashboard", "relatorios"],
    "biblioteca": ["registros", "dashboard"],
    "coordenador": ["alunos", "registros", "ocorrencias", "dashboard", "relatorios"],
    "diretor_turma": ["alunos", "registros", "ocorrencias", "dashboard", "relatorios"],
}

CONFIG_PADRAO = {
    "escola_nome": "EEEP Governador Virgilio Tavora",
    "escola_endereco": "R. Pergentino Silva, S/N - Seminario, Crato-CE",
    "escola_telefone": "",
    "responsavel_sistema": "Secretaria / Coordenacao",
}


class AnoLetivoCreate(BaseModel):
    nome: str
    ano: int
    data_inicio: date
    data_fim: date
    ativo: bool = False


class ConfiguracaoUpdate(BaseModel):
    configuracoes: dict[str, str]


class PermissaoUpdate(BaseModel):
    perfil: str
    permissoes: list[str]


def localizar_pg_dump():
    encontrado = shutil.which("pg_dump")
    if encontrado:
        return encontrado
    candidatos = [
        r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\13\bin\pg_dump.exe",
    ]
    return next((c for c in candidatos if Path(c).exists()), None)


def database_url():
    from app.database import DATABASE_URL
    return DATABASE_URL


def exigir_admin(usuario: Usuario):
    if usuario.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")


def exigir_configuracoes(db: Session, usuario: Usuario):
    if not tem_permissao(db, usuario, "configuracoes"):
        raise HTTPException(status_code=403, detail="Acesso negado")


def exigir_anexo(db: Session, usuario: Usuario, entidade: str | None = None):
    if tem_permissao(db, usuario, "configuracoes"):
        return
    modulo_por_entidade = {
        "aluno": "alunos",
        "registro": "registros",
        "ocorrencia": "ocorrencias",
    }
    modulo = modulo_por_entidade.get(entidade or "")
    if not modulo or not tem_permissao(db, usuario, modulo):
        raise HTTPException(status_code=403, detail="Acesso negado")


def registrar_auditoria_sistema(db: Session, usuario: Usuario, acao: str, entidade: str, entidade_id: int | None = None, detalhes: str | None = None, request: Request | None = None):
    auditoria = Auditoria(
        usuario_id=usuario.id,
        usuario_nome=usuario.nome,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        detalhes=detalhes,
    )
    if request and hasattr(auditoria, "ip"):
        auditoria.ip = request.client.host if request.client else None
        auditoria.user_agent = request.headers.get("user-agent")
    db.add(auditoria)


def get_configuracoes(db: Session):
    existentes = {c.chave: c.valor for c in db.query(ConfiguracaoSistema).all()}
    for chave, valor in CONFIG_PADRAO.items():
        if chave not in existentes:
            db.add(ConfiguracaoSistema(chave=chave, valor=valor))
            existentes[chave] = valor
    db.commit()
    return existentes


def get_permissoes(db: Session):
    existentes = {p.perfil: json.loads(p.permissoes) for p in db.query(PermissaoPerfil).all()}
    for perfil, permissoes in PERMISSOES_PADRAO.items():
        if perfil not in existentes:
            db.add(PermissaoPerfil(perfil=perfil, permissoes=json.dumps(permissoes)))
            existentes[perfil] = permissoes
    db.commit()
    return existentes


def turma_label(turma: Turma | None, cursos_por_id: dict[int, Curso]):
    if not turma:
        return "-"
    curso = cursos_por_id.get(turma.curso_id)
    return f"{turma.ano}º {turma.letra} - {curso.nome if curso else ''}"


@router.get("/sistema/configuracoes")
def obter_configuracoes(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_configuracoes(db, usuario)
    return get_configuracoes(db)


@router.put("/sistema/configuracoes")
def salvar_configuracoes(dados: ConfiguracaoUpdate, request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_configuracoes(db, usuario)
    for chave, valor in dados.configuracoes.items():
        item = db.query(ConfiguracaoSistema).filter(ConfiguracaoSistema.chave == chave).first()
        if not item:
            item = ConfiguracaoSistema(chave=chave, valor=valor)
            db.add(item)
        else:
            item.valor = valor
            item.atualizado_em = datetime.now()
    registrar_auditoria_sistema(db, usuario, "salvou", "configuracoes", None, "configuracoes gerais", request)
    db.commit()
    return {"mensagem": "Configuracoes salvas"}


@router.get("/sistema/anos-letivos")
def listar_anos_letivos(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_configuracoes(db, usuario)
    obter_ano_letivo_ativo(db)
    db.commit()
    return db.query(AnoLetivo).order_by(AnoLetivo.ano.desc()).all()


@router.post("/sistema/anos-letivos")
def criar_ano_letivo(dados: AnoLetivoCreate, request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_configuracoes(db, usuario)
    if dados.ativo:
        db.query(AnoLetivo).update({AnoLetivo.ativo: False})
    ano = AnoLetivo(**dados.model_dump())
    db.add(ano)
    db.flush()
    registrar_auditoria_sistema(db, usuario, "criou", "ano_letivo", ano.id, ano.nome, request)
    db.commit()
    db.refresh(ano)
    return ano


@router.put("/sistema/anos-letivos/{ano_id}/ativar")
def ativar_ano_letivo(ano_id: int, request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_configuracoes(db, usuario)
    ano = db.query(AnoLetivo).filter(AnoLetivo.id == ano_id).first()
    if not ano:
        raise HTTPException(status_code=404, detail="Ano letivo nao encontrado")
    if getattr(ano, "encerrado", False):
        raise HTTPException(status_code=400, detail="Ano letivo encerrado nao pode ser ativado")
    db.query(AnoLetivo).update({AnoLetivo.ativo: False})
    ano.ativo = True
    registrar_auditoria_sistema(db, usuario, "ativou", "ano_letivo", ano.id, ano.nome, request)
    db.commit()
    return {"mensagem": "Ano letivo ativado"}


@router.put("/sistema/anos-letivos/{ano_id}/encerrar")
def encerrar_ano_letivo(ano_id: int, request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_configuracoes(db, usuario)
    ano = db.query(AnoLetivo).filter(AnoLetivo.id == ano_id).first()
    if not ano:
        raise HTTPException(status_code=404, detail="Ano letivo nao encontrado")
    ano.encerrado = True
    ano.ativo = False
    registrar_auditoria_sistema(db, usuario, "encerrou", "ano_letivo", ano.id, ano.nome, request)
    db.commit()
    return {"mensagem": "Ano letivo encerrado"}


@router.get("/sistema/permissoes")
def listar_permissoes(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_configuracoes(db, usuario)
    return get_permissoes(db)


@router.put("/sistema/permissoes")
def salvar_permissoes(dados: PermissaoUpdate, request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_configuracoes(db, usuario)
    item = db.query(PermissaoPerfil).filter(PermissaoPerfil.perfil == dados.perfil).first()
    if not item:
        item = PermissaoPerfil(perfil=dados.perfil, permissoes=json.dumps(dados.permissoes))
        db.add(item)
    else:
        item.permissoes = json.dumps(dados.permissoes)
        item.atualizado_em = datetime.now()
    registrar_auditoria_sistema(db, usuario, "salvou", "permissoes", None, dados.perfil, request)
    db.commit()
    return {"mensagem": "Permissoes salvas"}


@router.get("/sistema/auditoria")
def listar_auditoria(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_configuracoes(db, usuario)
    return db.query(Auditoria).order_by(Auditoria.criado_em.desc()).limit(200).all()


@router.get("/sistema/backups")
def listar_backups(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_admin(usuario)
    arquivos = []
    for caminho in sorted(BACKUP_DIR.glob("backup_*"), key=lambda p: p.stat().st_mtime, reverse=True):
        arquivos.append({
            "nome": caminho.name,
            "tamanho": caminho.stat().st_size,
            "criado_em": datetime.fromtimestamp(caminho.stat().st_mtime),
            "url": f"/api/sistema/backups/{caminho.name}"
        })
    return arquivos


@router.post("/sistema/backups")
def gerar_backup(request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_admin(usuario)
    agora = datetime.now().strftime("%Y%m%d_%H%M%S")
    pg_dump = localizar_pg_dump()

    if pg_dump:
        url = urlparse(database_url())
        nome = f"backup_{agora}.sql"
        destino = BACKUP_DIR / nome
        env = os.environ.copy()
        env["PGPASSWORD"] = url.password or ""
        comando = [
            pg_dump,
            "-h", url.hostname or "localhost",
            "-p", str(url.port or 5432),
            "-U", url.username or "postgres",
            "-d", (url.path or "").lstrip("/"),
            "-f", str(destino),
            "--clean",
            "--if-exists",
        ]
        resultado = subprocess.run(comando, env=env, capture_output=True, text=True)
        if resultado.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Erro ao gerar backup: {resultado.stderr}")
    else:
        nome = f"backup_{agora}.json"
        destino = BACKUP_DIR / nome
        dados = {
            "gerado_em": datetime.now().isoformat(),
            "alunos": [vars(a) for a in db.query(Aluno).all()],
            "cursos": [vars(c) for c in db.query(Curso).all()],
            "turmas": [vars(t) for t in db.query(Turma).all()],
            "registros": [vars(r) for r in db.query(Registro).all()],
            "ocorrencias": [vars(o) for o in db.query(Ocorrencia).all()],
            "usuarios": [
                {k: v for k, v in vars(u).items() if k != "senha_hash"}
                for u in db.query(Usuario).all()
            ],
        }
        for lista in dados.values():
            if isinstance(lista, list):
                for item in lista:
                    item.pop("_sa_instance_state", None)
        destino.write_text(json.dumps(dados, default=str, ensure_ascii=False, indent=2), encoding="utf-8")

    registrar_auditoria_sistema(db, usuario, "gerou", "backup", None, nome, request)
    db.commit()
    return {
        "nome": nome,
        "tamanho": destino.stat().st_size,
        "url": f"/api/sistema/backups/{nome}",
        "tipo": "sql" if pg_dump else "json"
    }


@router.get("/sistema/backups/{nome}")
def baixar_backup(nome: str, request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_admin(usuario)
    caminho = (BACKUP_DIR / nome).resolve()
    pasta_backup = BACKUP_DIR.resolve()
    if not caminho.exists() or caminho.parent != pasta_backup:
        raise HTTPException(status_code=404, detail="Backup nao encontrado")
    registrar_auditoria_sistema(db, usuario, "baixou", "backup", None, nome, request)
    db.commit()
    return FileResponse(caminho, filename=nome, media_type="application/octet-stream")


@router.get("/sistema/anexos")
def listar_anexos(entidade: str | None = None, entidade_id: int | None = None, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_anexo(db, usuario, entidade)
    query = db.query(Anexo)
    if entidade:
        query = query.filter(Anexo.entidade == entidade)
    if entidade_id:
        query = query.filter(Anexo.entidade_id == entidade_id)
    anexos = query.order_by(Anexo.criado_em.desc()).limit(100).all()
    return [
        {
            "id": anexo.id,
            "entidade": anexo.entidade,
            "entidade_id": anexo.entidade_id,
            "nome_original": anexo.nome_original,
            "nome_arquivo": anexo.nome_arquivo,
            "content_type": anexo.content_type,
            "tamanho": anexo.tamanho,
            "enviado_por_nome": anexo.enviado_por_nome,
            "criado_em": anexo.criado_em,
            "url": f"/api/sistema/anexos/{anexo.id}/download",
        }
        for anexo in anexos
    ]


@router.post("/sistema/anexos")
async def enviar_anexo(
    request: Request,
    entidade: str = Form(...),
    entidade_id: int = Form(...),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    exigir_anexo(db, usuario, entidade)
    extensao = Path(arquivo.filename or "arquivo").suffix.lower()
    if extensao not in EXTENSOES_ANEXO_PERMITIDAS:
        raise HTTPException(status_code=400, detail="Tipo de arquivo nao permitido")
    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
    caminho = UPLOAD_DIR / nome_arquivo
    conteudo = await arquivo.read()
    if len(conteudo) > TAMANHO_MAX_ANEXO:
        raise HTTPException(status_code=400, detail="Arquivo maior que 10 MB")
    caminho.write_bytes(conteudo)

    anexo = Anexo(
        entidade=entidade,
        entidade_id=entidade_id,
        nome_original=arquivo.filename or nome_arquivo,
        nome_arquivo=nome_arquivo,
        caminho=str(caminho),
        content_type=arquivo.content_type,
        tamanho=len(conteudo),
        enviado_por_id=usuario.id,
        enviado_por_nome=usuario.nome,
    )
    db.add(anexo)
    db.flush()
    registrar_auditoria_sistema(db, usuario, "anexou", entidade, entidade_id, anexo.nome_original, request)
    db.commit()
    db.refresh(anexo)
    return {
        "id": anexo.id,
        "nome_original": anexo.nome_original,
        "url": f"/api/sistema/anexos/{anexo.id}/download",
    }


@router.get("/sistema/anexos/{anexo_id}/download")
def baixar_anexo(anexo_id: int, request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    anexo = db.query(Anexo).filter(Anexo.id == anexo_id).first()
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo nao encontrado")
    exigir_anexo(db, usuario, anexo.entidade)
    caminho = Path(anexo.caminho)
    if anexo.caminho.startswith("/static/uploads/"):
        caminho = Path(anexo.caminho.lstrip("/"))
    caminho = caminho.resolve()
    pasta_upload = UPLOAD_DIR.resolve()
    pasta_static_antiga = Path("static/uploads").resolve()
    if not caminho.exists() or (caminho.parent != pasta_upload and caminho.parent != pasta_static_antiga):
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado")
    registrar_auditoria_sistema(db, usuario, "baixou", "anexo", anexo.id, anexo.nome_original, request)
    db.commit()
    return FileResponse(caminho, filename=anexo.nome_original, media_type=anexo.content_type or "application/octet-stream")


@router.delete("/sistema/anexos/{anexo_id}")
def excluir_anexo(anexo_id: int, request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    anexo = db.query(Anexo).filter(Anexo.id == anexo_id).first()
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo nao encontrado")
    exigir_anexo(db, usuario, anexo.entidade)
    caminho = Path(anexo.caminho)
    if anexo.caminho.startswith("/static/uploads/"):
        caminho = Path(anexo.caminho.lstrip("/"))
    caminho = caminho.resolve()
    pasta_upload = UPLOAD_DIR.resolve()
    pasta_static_antiga = Path("static/uploads").resolve()
    if caminho.exists() and (caminho.parent == pasta_upload or caminho.parent == pasta_static_antiga):
        caminho.unlink()
    registrar_auditoria_sistema(db, usuario, "excluiu", "anexo", anexo.id, anexo.nome_original, request)
    db.delete(anexo)
    db.commit()
    return {"mensagem": "Anexo excluido"}


@router.get("/sistema/relatorios/oficial", response_class=HTMLResponse)
def relatorio_oficial(
    tipo: str = Query("turmas"),
    turma_id: int | None = Query(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    exigir_configuracoes(db, usuario)
    config = get_configuracoes(db)
    cursos = {c.id: c for c in db.query(Curso).all()}
    turmas = {t.id: t for t in db.query(Turma).all()}
    alunos = db.query(Aluno).all()
    if turma_id:
        alunos = [a for a in alunos if a.turma_id == turma_id]
    registros = db.query(Registro).all()
    ocorrencias = db.query(Ocorrencia).all()

    linhas = []
    titulo = "Relatorio por turma"
    if tipo == "alunos":
        titulo = "Relatorio de alunos"
        for aluno in alunos:
            linhas.append([aluno.nome, aluno.matricula, turma_label(turmas.get(aluno.turma_id), cursos), aluno.status])
        cabecalho = ["Aluno", "Matricula", "Turma", "Status"]
    elif tipo == "ocorrencias":
        titulo = "Relatorio de ocorrencias"
        for ocorrencia in ocorrencias:
            aluno = next((a for a in alunos if a.id == ocorrencia.aluno_id), None)
            if aluno:
                linhas.append([str(ocorrencia.data), aluno.nome, turma_label(turmas.get(aluno.turma_id), cursos), ocorrencia.tipo, ocorrencia.gravidade or "Leve", ocorrencia.status or "Aberta"])
        cabecalho = ["Data", "Aluno", "Turma", "Tipo", "Gravidade", "Status"]
    else:
        for turma in turmas.values():
            if turma_id and turma.id != turma_id:
                continue
            ids = [a.id for a in alunos if a.turma_id == turma.id]
            linhas.append([
                turma_label(turma, cursos),
                len(ids),
                sum(1 for r in registros if r.aluno_id in ids and r.tipo == "Atraso"),
                sum(1 for r in registros if r.aluno_id in ids and r.tipo != "Atraso"),
                sum(1 for o in ocorrencias if o.aluno_id in ids),
            ])
        cabecalho = ["Turma", "Alunos", "Atrasos", "Saidas", "Ocorrencias"]

    tabela = "".join("<tr>" + "".join(f"<td>{col}</td>" for col in linha) + "</tr>" for linha in linhas)
    head = "".join(f"<th>{col}</th>" for col in cabecalho)
    return f"""
    <!doctype html>
    <html lang="pt-BR">
    <head>
        <meta charset="utf-8">
        <title>{titulo}</title>
        <style>
            body {{ font-family: Arial, sans-serif; color: #111; margin: 32px; }}
            .topo {{ text-align: center; border-bottom: 2px solid #222; padding-bottom: 12px; margin-bottom: 20px; }}
            h1 {{ margin: 0; font-size: 22px; }}
            h2 {{ margin: 8px 0 0; font-size: 18px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 18px; font-size: 12px; }}
            th, td {{ border: 1px solid #999; padding: 7px; text-align: left; }}
            th {{ background: #eee; }}
            .rodape {{ margin-top: 32px; display: flex; justify-content: space-between; font-size: 12px; }}
            @media print {{ button {{ display: none; }} body {{ margin: 18px; }} }}
        </style>
    </head>
    <body>
        <button onclick="window.print()">Imprimir / salvar em PDF</button>
        <div class="topo">
            <h1>{config.get("escola_nome", "")}</h1>
            <div>{config.get("escola_endereco", "")}</div>
            <h2>{titulo}</h2>
        </div>
        <table><thead><tr>{head}</tr></thead><tbody>{tabela}</tbody></table>
        <div class="rodape">
            <div>Emitido por: {usuario.nome}</div>
            <div>{datetime.now().strftime("%d/%m/%Y %H:%M")}</div>
        </div>
    </body>
    </html>
    """
