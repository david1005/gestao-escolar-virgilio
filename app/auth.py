from datetime import datetime, timedelta
import json
import re
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import SECRET_KEY
from app.models.aluno import Aluno, Turma
from app.models.usuario import Usuario
from app.models.sistema import PermissaoPerfil

PERMISSOES_PADRAO = {
    "admin": ["*"],
    "ppdt": ["alunos", "registros", "ocorrencias", "dashboard", "relatorios"],
    "biblioteca": ["registros", "dashboard"],
    "coordenador": ["alunos", "registros", "ocorrencias", "dashboard", "relatorios"],
    "diretor_turma": ["alunos", "registros", "ocorrencias", "dashboard", "relatorios"],
}

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hora

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def verificar_senha(senha, hash):
    return pwd_context.verify(senha, hash)

def hash_senha(senha):
    if len((senha or "").encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="A senha nao pode ter mais de 72 bytes")
    return pwd_context.hash(senha)

def validar_senha_forte(senha: str):
    if len(senha or "") < 8:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 8 caracteres")
    if len((senha or "").encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="A senha nao pode ter mais de 72 bytes")
    if not re.search(r"[A-Za-z]", senha) or not re.search(r"\d", senha):
        raise HTTPException(status_code=400, detail="A senha deve conter letras e numeros")

def criar_token(data: dict):
    dados = data.copy()
    expira = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    dados.update({"exp": expira})
    return jwt.encode(dados, SECRET_KEY, algorithm=ALGORITHM)

def get_usuario_atual(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado")
    if not usuario.ativo:
        raise HTTPException(status_code=401, detail="Usuario inativo")
    return usuario

def requer_admin(usuario: Usuario = Depends(get_usuario_atual)):
    if usuario.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    return usuario

def requer_admin_ou_ppdt(usuario: Usuario = Depends(get_usuario_atual)):
    if usuario.perfil not in ["admin", "ppdt"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    return usuario

def get_curso_ids_usuario(usuario: Usuario) -> list[int]:
    ids = []
    if getattr(usuario, "curso_ids", None):
        for valor in usuario.curso_ids.split(","):
            valor = valor.strip()
            if valor.isdigit():
                ids.append(int(valor))
    if usuario.curso_id and usuario.curso_id not in ids:
        ids.append(usuario.curso_id)
    return ids

def usuario_pode_acessar_aluno(db: Session, usuario: Usuario, aluno: Aluno) -> bool:
    if usuario.perfil == "diretor_turma":
        return aluno.turma_id == usuario.turma_id
    if usuario.perfil == "coordenador":
        curso_ids = get_curso_ids_usuario(usuario)
        turma = db.query(Turma).filter(
            Turma.id == aluno.turma_id,
            Turma.curso_id.in_(curso_ids),
        ).first()
        return turma is not None
    return True

def exigir_acesso_aluno(db: Session, usuario: Usuario, aluno_id: int) -> Aluno:
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")
    if not usuario_pode_acessar_aluno(db, usuario, aluno):
        raise HTTPException(status_code=403, detail="Acesso negado")
    return aluno

def tem_permissao(db: Session, usuario: Usuario, modulo: str) -> bool:
    if usuario.perfil == "admin":
        return True
    registro = db.query(PermissaoPerfil).filter(PermissaoPerfil.perfil == usuario.perfil).first()
    if registro:
        permissoes = json.loads(registro.permissoes)
    else:
        permissoes = PERMISSOES_PADRAO.get(usuario.perfil, [])
    return "*" in permissoes or modulo in permissoes
