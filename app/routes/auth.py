from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import os
import secrets
from app.database import get_db
from app.models.auditoria import Auditoria
from app.models.usuario import Usuario
from app.auth import verificar_senha, hash_senha, criar_token, get_usuario_atual, get_curso_ids_usuario, validar_senha_forte
from pydantic import BaseModel
from typing import Optional
from app.services.login_seguro import verificar_bloqueio, falhar, limpar

router = APIRouter()
MAX_TENTATIVAS_LOGIN = 5
BLOQUEIO_LOGIN_MINUTOS = 10

class LoginForm(BaseModel):
    email: str
    senha: str

class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str
    perfil: str
    turma_id: Optional[int] = None
    curso_id: Optional[int] = None
    curso_ids: Optional[list[int]] = None

class UsuarioUpdate(BaseModel):
    nome: str
    perfil: str
    turma_id: Optional[int] = None
    curso_id: Optional[int] = None
    curso_ids: Optional[list[int]] = None
    ativo: int

class ResetSenha(BaseModel):
    nova_senha: str

def serializar_curso_ids(curso_ids: Optional[list[int]], curso_id: Optional[int] = None) -> Optional[str]:
    ids = []
    for valor in curso_ids or []:
        if valor and valor not in ids:
            ids.append(valor)
    if curso_id and curso_id not in ids:
        ids.append(curso_id)
    return ",".join(str(valor) for valor in ids) if ids else None

def usuario_dict(usuario: Usuario):
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "perfil": usuario.perfil,
        "turma_id": usuario.turma_id,
        "curso_id": usuario.curso_id,
        "curso_ids": get_curso_ids_usuario(usuario),
        "ultimo_login": usuario.ultimo_login,
        "ativo": usuario.ativo
    }

def registrar_auditoria(db: Session, usuario: Usuario, acao: str, entidade: str, entidade_id: int | None = None, detalhes: str | None = None):
    db.add(Auditoria(
        usuario_id=usuario.id,
        usuario_nome=usuario.nome,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        detalhes=detalhes,
    ))

def cookie_seguro(request: Request) -> bool:
    if os.getenv("APP_ENV", "").lower() == "production":
        return True
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"

def auditar_login(db, request, acao, usuario=None):
    db.add(Auditoria(usuario_id=usuario.id if usuario else None,
        usuario_nome=usuario.nome if usuario else None, acao=acao, entidade='autenticacao',
        ip=request.client.host if request.client else 'desconhecido',
        user_agent=request.headers.get('user-agent', '')[:512]))

@router.post("/auth/login")
def login(form: LoginForm, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else 'desconhecido'
    email = form.email.strip().lower()
    try:
        verificar_bloqueio(db, email, ip)
    except HTTPException:
        auditar_login(db, request, 'login_bloqueado')
        db.commit()
        raise
    usuario = db.query(Usuario).filter(func.lower(Usuario.email) == email).first()
    if not usuario or not usuario.ativo or not verificar_senha(form.senha, usuario.senha_hash):
        falhar(db, email, ip)
        auditar_login(db, request, 'login_negado')
        db.commit()
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    limpar(db, email, ip)
    auditar_login(db, request, 'login', usuario)
    usuario.ultimo_login = datetime.now()
    db.commit()
    token = criar_token({"sub": usuario.email})
    csrf_token = secrets.token_urlsafe(32)
    seguro = cookie_seguro(request)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=28800, secure=seguro, samesite="lax")
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=False, max_age=28800, secure=seguro, samesite="lax")
    return {"mensagem": "Login realizado com sucesso", "perfil": usuario.perfil, "nome": usuario.nome}

@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("csrf_token")
    return {"mensagem": "Logout realizado"}

@router.get("/auth/me")
def me(usuario: Usuario = Depends(get_usuario_atual)):
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "perfil": usuario.perfil,
        "turma_id": usuario.turma_id,
        "curso_id": usuario.curso_id,
        "curso_ids": get_curso_ids_usuario(usuario),
        "ultimo_login": usuario.ultimo_login
    }

@router.get("/usuarios/")
def listar_usuarios(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    if usuario.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    return [usuario_dict(u) for u in db.query(Usuario).all()]

@router.post("/usuarios/")
def criar_usuario(dados: UsuarioCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    if usuario.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    validar_senha_forte(dados.senha)
    existente = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    curso_ids_texto = serializar_curso_ids(dados.curso_ids, dados.curso_id)
    novo = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        perfil=dados.perfil,
        turma_id=dados.turma_id,
        curso_id=(dados.curso_ids[0] if dados.curso_ids else dados.curso_id),
        curso_ids=curso_ids_texto
    )
    db.add(novo)
    db.flush()
    registrar_auditoria(db, usuario, "criou", "usuario", novo.id, f"email={novo.email}; perfil={novo.perfil}")
    db.commit()
    db.refresh(novo)
    return usuario_dict(novo)

@router.put("/usuarios/{usuario_id}")
def editar_usuario(usuario_id: int, dados: UsuarioUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    if usuario.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if u.id == usuario.id and dados.ativo == 0:
        raise HTTPException(status_code=400, detail="Você não pode inativar seu próprio usuário")
    u.nome = dados.nome
    u.perfil = dados.perfil
    u.turma_id = dados.turma_id
    u.curso_id = (dados.curso_ids[0] if dados.curso_ids else dados.curso_id)
    u.curso_ids = serializar_curso_ids(dados.curso_ids, dados.curso_id)
    u.ativo = dados.ativo
    registrar_auditoria(db, usuario, "editou", "usuario", u.id, f"email={u.email}; perfil={u.perfil}; ativo={u.ativo}")
    db.commit()
    db.refresh(u)
    return usuario_dict(u)

@router.delete("/usuarios/{usuario_id}")
def excluir_usuario(usuario_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    if usuario.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if u.id == usuario.id:
        raise HTTPException(status_code=400, detail="Você não pode inativar seu próprio usuário")
    u.ativo = 0
    registrar_auditoria(db, usuario, "inativou", "usuario", u.id, f"email={u.email}")
    db.commit()
    return {"mensagem": "Usuário inativado"}

@router.put("/usuarios/{usuario_id}/resetar-senha")
def resetar_senha_usuario(usuario_id: int, dados: ResetSenha, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    if usuario.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    validar_senha_forte(dados.nova_senha)
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    u.senha_hash = hash_senha(dados.nova_senha)
    registrar_auditoria(db, usuario, "resetou_senha", "usuario", u.id, f"email={u.email}")
    db.commit()
    return {"mensagem": "Senha redefinida com sucesso"}

class TrocaSenha(BaseModel):
    senha_atual: str
    nova_senha: str

@router.put("/auth/trocar-senha")
def trocar_senha(dados: TrocaSenha, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    if not verificar_senha(dados.senha_atual, usuario.senha_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    validar_senha_forte(dados.nova_senha)
    usuario.senha_hash = hash_senha(dados.nova_senha)
    db.commit()
    return {"mensagem": "Senha alterada com sucesso"}
