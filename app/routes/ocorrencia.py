from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.auditoria import Auditoria
from app.models.ocorrencia import Ocorrencia
from app.models.aluno import Aluno, Turma
from app.schemas.ocorrencia import OcorrenciaCreate, OcorrenciaUpdate
from app.schemas import ocorrencia as schemas
from app.auth import get_curso_ids_usuario, get_usuario_atual, tem_permissao
from app.models.usuario import Usuario

router = APIRouter()

def exigir_ocorrencias(db: Session, usuario: Usuario):
    if not tem_permissao(db, usuario, "ocorrencias"):
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

@router.post("/ocorrencias/", response_model=schemas.Ocorrencia)
def criar_ocorrencia(ocorrencia: OcorrenciaCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_ocorrencias(db, usuario)
    db_ocorrencia = Ocorrencia(**ocorrencia.model_dump())
    db.add(db_ocorrencia)
    db.flush()
    registrar_auditoria(db, usuario, "criou", "ocorrencia", db_ocorrencia.id, f"aluno_id={db_ocorrencia.aluno_id}; tipo={db_ocorrencia.tipo}")
    db.commit()
    db.refresh(db_ocorrencia)
    return db_ocorrencia

@router.get("/ocorrencias/")
def listar_ocorrencias(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_ocorrencias(db, usuario)
    if usuario.perfil == "diretor_turma":
        alunos = db.query(Aluno).filter(Aluno.turma_id == usuario.turma_id).all()
        aluno_ids = [a.id for a in alunos]
        return db.query(Ocorrencia).filter(Ocorrencia.aluno_id.in_(aluno_ids)).order_by(Ocorrencia.data.desc()).all()
    elif usuario.perfil == "coordenador":
        turmas = db.query(Turma).filter(Turma.curso_id.in_(get_curso_ids_usuario(usuario))).all()
        turma_ids = [t.id for t in turmas]
        alunos = db.query(Aluno).filter(Aluno.turma_id.in_(turma_ids)).all()
        aluno_ids = [a.id for a in alunos]
        return db.query(Ocorrencia).filter(Ocorrencia.aluno_id.in_(aluno_ids)).order_by(Ocorrencia.data.desc()).all()
    return db.query(Ocorrencia).order_by(Ocorrencia.data.desc()).all()

@router.get("/ocorrencias/aluno/{aluno_id}")
def ocorrencias_por_aluno(aluno_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_ocorrencias(db, usuario)
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
    return db.query(Ocorrencia).filter(Ocorrencia.aluno_id == aluno_id).order_by(Ocorrencia.data.desc()).all()

@router.get("/ocorrencias/contar/{aluno_id}")
def contar_ocorrencias(aluno_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_ocorrencias(db, usuario)
    total = db.query(Ocorrencia).filter(Ocorrencia.aluno_id == aluno_id).count()
    if total == 0:
        medida = "Só registro"
    elif total == 1:
        medida = "Advertência + Notificação ao responsável"
    else:
        medida = "Suspensão + Notificação ao responsável"
    return {"total": total, "proxima_medida": medida}

@router.put("/ocorrencias/{ocorrencia_id}", response_model=schemas.Ocorrencia)
def editar_ocorrencia(ocorrencia_id: int, dados: OcorrenciaUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_ocorrencias(db, usuario)
    ocorrencia = db.query(Ocorrencia).filter(Ocorrencia.id == ocorrencia_id).first()
    if not ocorrencia:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    ocorrencia.tipo = dados.tipo
    ocorrencia.descricao = dados.descricao
    ocorrencia.medida = dados.medida
    ocorrencia.gravidade = dados.gravidade
    ocorrencia.status = dados.status
    ocorrencia.acoes_tomadas = dados.acoes_tomadas
    ocorrencia.responsavel_notificado = dados.responsavel_notificado
    ocorrencia.editado_por = dados.editado_por
    ocorrencia.editado_em = datetime.now()
    registrar_auditoria(db, usuario, "editou", "ocorrencia", ocorrencia.id, f"aluno_id={ocorrencia.aluno_id}; tipo={ocorrencia.tipo}")
    db.commit()
    db.refresh(ocorrencia)
    return ocorrencia

@router.delete("/ocorrencias/{ocorrencia_id}")
def excluir_ocorrencia(ocorrencia_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_ocorrencias(db, usuario)
    ocorrencia = db.query(Ocorrencia).filter(Ocorrencia.id == ocorrencia_id).first()
    if not ocorrencia:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    registrar_auditoria(db, usuario, "excluiu", "ocorrencia", ocorrencia.id, f"aluno_id={ocorrencia.aluno_id}; tipo={ocorrencia.tipo}")
    db.delete(ocorrencia)
    db.commit()
    return {"mensagem": "Ocorrência excluída com sucesso"}
