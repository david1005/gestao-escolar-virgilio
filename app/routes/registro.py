from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.auditoria import Auditoria
from app.models.registro import Registro
from app.models.aluno import Aluno, Turma
from app.schemas.registro import RegistroCreate, RegistroUpdate
from app.schemas import registro as schemas
from app.auth import get_curso_ids_usuario, get_usuario_atual, tem_permissao
from app.models.usuario import Usuario

router = APIRouter()

def exigir_registros(db: Session, usuario: Usuario):
    if not tem_permissao(db, usuario, "registros"):
        raise HTTPException(status_code=403, detail="Acesso negado")

def registrar_auditoria(db: Session, usuario: Usuario, acao: str, entidade: str, entidade_id: int | None = None, detalhes: str | None = None):
    db.add(Auditoria(
        usuario_id=usuario.id,
        usuario_nome=usuario.nome,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        detalhes=detalhes,
    ))

@router.post("/registros/", response_model=schemas.Registro)
def criar_registro(registro: RegistroCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_registros(db, usuario)
    db_registro = Registro(**registro.model_dump())
    db.add(db_registro)
    db.flush()
    registrar_auditoria(db, usuario, "criou", "registro", db_registro.id, f"aluno_id={db_registro.aluno_id}; tipo={db_registro.tipo}")
    db.commit()
    db.refresh(db_registro)
    return db_registro

@router.get("/registros/")
def listar_registros(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_registros(db, usuario)
    if usuario.perfil == "diretor_turma":
        alunos = db.query(Aluno).filter(Aluno.turma_id == usuario.turma_id).all()
        aluno_ids = [a.id for a in alunos]
        return db.query(Registro).filter(Registro.aluno_id.in_(aluno_ids)).order_by(Registro.data.desc()).all()
    elif usuario.perfil == "coordenador":
        turmas = db.query(Turma).filter(Turma.curso_id.in_(get_curso_ids_usuario(usuario))).all()
        turma_ids = [t.id for t in turmas]
        alunos = db.query(Aluno).filter(Aluno.turma_id.in_(turma_ids)).all()
        aluno_ids = [a.id for a in alunos]
        return db.query(Registro).filter(Registro.aluno_id.in_(aluno_ids)).order_by(Registro.data.desc()).all()
    return db.query(Registro).order_by(Registro.data.desc()).all()

@router.get("/registros/aluno/{aluno_id}")
def registros_por_aluno(aluno_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_registros(db, usuario)
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")
    if usuario.perfil == "diretor_turma" and aluno.turma_id != usuario.turma_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    if usuario.perfil == "coordenador":
        turmas = db.query(Turma).filter(Turma.curso_id.in_(get_curso_ids_usuario(usuario))).all()
        turma_ids = [t.id for t in turmas]
        if aluno.turma_id not in turma_ids:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return db.query(Registro).filter(Registro.aluno_id == aluno_id).order_by(Registro.data.desc()).all()

@router.put("/registros/{registro_id}")
def editar_registro(registro_id: int, dados: RegistroUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_registros(db, usuario)
    registro = db.query(Registro).filter(Registro.id == registro_id).first()
    if not registro:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    registro.tipo = dados.tipo
    registro.aula = dados.aula
    registro.motivo = dados.motivo
    registro.tem_documento = dados.tem_documento
    registro.observacoes = dados.observacoes
    registrar_auditoria(db, usuario, "editou", "registro", registro.id, f"aluno_id={registro.aluno_id}; tipo={registro.tipo}")
    db.commit()
    db.refresh(registro)
    return registro

@router.delete("/registros/{registro_id}")
def excluir_registro(registro_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_registros(db, usuario)
    registro = db.query(Registro).filter(Registro.id == registro_id).first()
    if not registro:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    registrar_auditoria(db, usuario, "excluiu", "registro", registro.id, f"aluno_id={registro.aluno_id}; tipo={registro.tipo}")
    db.delete(registro)
    db.commit()
    return {"mensagem": "Registro excluído com sucesso"}
