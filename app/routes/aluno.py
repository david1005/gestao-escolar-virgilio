import csv
import io
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_curso_ids_usuario, get_usuario_atual, tem_permissao
from app.database import get_db
from app.models.aluno import Aluno, Curso, Turma
from app.models.auditoria import Auditoria
from app.models.ocorrencia import Ocorrencia
from app.models.registro import Registro
from app.models.usuario import Usuario
from app.schemas import aluno as schemas
from app.schemas.aluno import AlunoCreate, AlunoUpdate, CursoCreate, TurmaCreate

router = APIRouter()


def exigir_alunos(db: Session, usuario: Usuario):
    if not tem_permissao(db, usuario, "alunos"):
        raise HTTPException(status_code=403, detail="Acesso negado")


def registrar_auditoria(
    db: Session,
    usuario: Usuario,
    acao: str,
    entidade: str,
    entidade_id: int | None = None,
    detalhes: str | None = None,
):
    db.add(Auditoria(
        usuario_id=usuario.id,
        usuario_nome=usuario.nome,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        detalhes=detalhes,
    ))


def contar_historico_aluno(db: Session, aluno_id: int):
    registros = db.query(Registro).filter(Registro.aluno_id == aluno_id).count()
    ocorrencias = db.query(Ocorrencia).filter(Ocorrencia.aluno_id == aluno_id).count()
    return registros, ocorrencias


def parse_data_nascimento(valor: str) -> date:
    texto = (valor or "").strip()
    if not texto:
        raise ValueError("data_nascimento obrigatoria")

    if " " in texto:
        texto = texto.split(" ", 1)[0]

    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            pass

    if texto.replace(".", "", 1).isdigit():
        numero = float(texto)
        if numero > 0:
            return date(1899, 12, 30) + timedelta(days=int(numero))

    raise ValueError("data_nascimento deve estar em DD/MM/AAAA ou AAAA-MM-DD")


def calcular_previa_virada(db: Session):
    turmas = db.query(Turma).all()
    alunos = db.query(Aluno).filter(Aluno.status == "ativo").all()
    turmas_por_id = {turma.id: turma for turma in turmas}
    destinos = {(turma.ano, turma.letra, turma.curso_id) for turma in turmas}
    por_ano = {1: 0, 2: 0, 3: 0}
    sem_destino = 0

    for aluno in alunos:
        turma = turmas_por_id.get(aluno.turma_id)
        if not turma:
            sem_destino += 1
            continue

        por_ano[turma.ano] = por_ano.get(turma.ano, 0) + 1
        if turma.ano in [1, 2] and (turma.ano + 1, turma.letra, turma.curso_id) not in destinos:
            sem_destino += 1

    return {
        "primeiro_para_segundo": por_ano.get(1, 0),
        "segundo_para_terceiro": por_ano.get(2, 0),
        "terceiro_concluido": por_ano.get(3, 0),
        "sem_destino": sem_destino,
    }


@router.post("/cursos/", response_model=schemas.Curso)
def criar_curso(curso: CursoCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    if usuario.perfil not in ["admin", "ppdt"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    existente = db.query(Curso).filter(Curso.nome == curso.nome).first()
    if existente:
        raise HTTPException(status_code=400, detail="Curso ja cadastrado")
    db_curso = Curso(**curso.model_dump())
    db.add(db_curso)
    registrar_auditoria(db, usuario, "criou", "curso", None, curso.nome)
    db.commit()
    db.refresh(db_curso)
    return db_curso


@router.get("/cursos/")
def listar_cursos(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    query = db.query(Curso)
    if usuario.perfil == "coordenador":
        query = query.filter(Curso.id.in_(get_curso_ids_usuario(usuario)))
    elif usuario.perfil == "diretor_turma":
        turma = db.query(Turma).filter(Turma.id == usuario.turma_id).first()
        if not turma:
            return []
        query = query.filter(Curso.id == turma.curso_id)
    return query.order_by(Curso.nome).all()


@router.put("/cursos/{curso_id}", response_model=schemas.Curso)
def editar_curso(curso_id: int, dados: CursoCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    if usuario.perfil not in ["admin", "ppdt"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    curso = db.query(Curso).filter(Curso.id == curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso nao encontrado")

    existente = db.query(Curso).filter(
        Curso.nome == dados.nome,
        Curso.id != curso_id,
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="Curso ja cadastrado")

    curso.nome = dados.nome
    curso.sigla = dados.sigla
    registrar_auditoria(db, usuario, "editou", "curso", curso.id, curso.nome)
    db.commit()
    db.refresh(curso)
    return curso


@router.post("/turmas/", response_model=schemas.Turma)
def criar_turma(turma: TurmaCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    if usuario.perfil not in ["admin", "ppdt"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    curso = db.query(Curso).filter(Curso.id == turma.curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso nao encontrado")
    existente = db.query(Turma).filter(
        Turma.ano == turma.ano,
        Turma.letra == turma.letra,
        Turma.curso_id == turma.curso_id,
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="Turma ja cadastrada para este curso")
    db_turma = Turma(**turma.model_dump())
    db.add(db_turma)
    registrar_auditoria(db, usuario, "criou", "turma", None, f"{turma.ano}{turma.letra}")
    db.commit()
    db.refresh(db_turma)
    return db_turma


@router.get("/turmas/")
def listar_turmas(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    query = db.query(Turma)
    if usuario.perfil == "coordenador":
        query = query.filter(Turma.curso_id.in_(get_curso_ids_usuario(usuario)))
    elif usuario.perfil == "diretor_turma":
        query = query.filter(Turma.id == usuario.turma_id)
    return query.order_by(Turma.ano, Turma.letra).all()


@router.put("/turmas/{turma_id}", response_model=schemas.Turma)
def editar_turma(turma_id: int, dados: TurmaCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    if usuario.perfil not in ["admin", "ppdt"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    turma = db.query(Turma).filter(Turma.id == turma_id).first()
    if not turma:
        raise HTTPException(status_code=404, detail="Turma nao encontrada")

    curso = db.query(Curso).filter(Curso.id == dados.curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso nao encontrado")

    existente = db.query(Turma).filter(
        Turma.ano == dados.ano,
        Turma.letra == dados.letra,
        Turma.curso_id == dados.curso_id,
        Turma.id != turma_id,
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="Turma ja cadastrada para este curso")

    turma.ano = dados.ano
    turma.letra = dados.letra
    turma.curso_id = dados.curso_id
    registrar_auditoria(db, usuario, "editou", "turma", turma.id, f"{turma.ano}{turma.letra}")
    db.commit()
    db.refresh(turma)
    return turma


@router.post("/alunos/", response_model=schemas.Aluno)
def criar_aluno(aluno: AlunoCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_alunos(db, usuario)
    if usuario.perfil not in ["admin", "ppdt"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    db_aluno = Aluno(**aluno.model_dump())
    db.add(db_aluno)
    db.flush()
    registrar_auditoria(db, usuario, "criou", "aluno", db_aluno.id, f"matricula={aluno.matricula}")
    db.commit()
    db.refresh(db_aluno)
    return db_aluno


@router.get("/alunos/")
def listar_alunos(status: str = Query("ativo"), db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_alunos(db, usuario)
    query = db.query(Aluno)

    if status != "todos":
        query = query.filter(Aluno.status == status)

    if usuario.perfil == "diretor_turma":
        alunos = query.filter(Aluno.turma_id == usuario.turma_id).all()
    elif usuario.perfil == "coordenador":
        turmas = db.query(Turma).filter(Turma.curso_id.in_(get_curso_ids_usuario(usuario))).all()
        turma_ids = [t.id for t in turmas]
        alunos = query.filter(Aluno.turma_id.in_(turma_ids)).all()
    else:
        alunos = query.all()
    return alunos


@router.get("/alunos/virada-ano/previa")
def previa_virada_ano(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_alunos(db, usuario)
    if usuario.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    return calcular_previa_virada(db)


@router.post("/alunos/virada-ano")
def realizar_virada_ano(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_alunos(db, usuario)
    if usuario.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")

    turmas = db.query(Turma).all()
    turmas_por_id = {turma.id: turma for turma in turmas}
    proxima_turma = {(turma.ano, turma.letra, turma.curso_id): turma.id for turma in turmas}

    concluidos = 0
    promovidos = 0

    alunos = db.query(Aluno).filter(Aluno.status == "ativo").all()
    for aluno in alunos:
        turma_atual = turmas_por_id.get(aluno.turma_id)
        if not turma_atual:
            continue

        if turma_atual.ano == 3:
            aluno.status = "concluido"
            concluidos += 1
            continue

        destino_id = proxima_turma.get((turma_atual.ano + 1, turma_atual.letra, turma_atual.curso_id))
        if destino_id:
            aluno.turma_id = destino_id
            promovidos += 1

    registrar_auditoria(db, usuario, "virada_ano", "aluno", None, f"promovidos={promovidos}; concluidos={concluidos}")
    db.commit()
    return {
        "mensagem": "Virada de ano letivo realizada com sucesso",
        "promovidos": promovidos,
        "concluidos": concluidos,
    }


@router.get("/alunos/{aluno_id}")
def buscar_aluno(aluno_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_alunos(db, usuario)
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
    return aluno


@router.put("/alunos/{aluno_id}", response_model=schemas.Aluno)
def editar_aluno(aluno_id: int, dados: AlunoUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_alunos(db, usuario)
    if usuario.perfil not in ["admin", "ppdt"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")

    matricula_existente = db.query(Aluno).filter(
        Aluno.matricula == dados.matricula,
        Aluno.id != aluno_id,
    ).first()
    if matricula_existente:
        raise HTTPException(status_code=400, detail="Matricula ja cadastrada")

    for campo, valor in dados.model_dump().items():
        setattr(aluno, campo, valor)

    registrar_auditoria(db, usuario, "editou", "aluno", aluno.id, f"matricula={aluno.matricula}")
    db.commit()
    db.refresh(aluno)
    return aluno


@router.delete("/alunos/{aluno_id}")
def excluir_aluno(aluno_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_alunos(db, usuario)
    if usuario.perfil not in ["admin", "ppdt"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")

    registros, ocorrencias = contar_historico_aluno(db, aluno.id)
    if registros or ocorrencias:
        aluno.status = "transferido"
        registrar_auditoria(
            db,
            usuario,
            "arquivou_por_historico",
            "aluno",
            aluno.id,
            f"registros={registros}; ocorrencias={ocorrencias}",
        )
        db.commit()
        return {
            "mensagem": "Aluno possui historico e foi marcado como transferido.",
            "status": "transferido",
        }

    registrar_auditoria(db, usuario, "excluiu", "aluno", aluno.id, f"matricula={aluno.matricula}")
    db.delete(aluno)
    db.commit()
    return {"mensagem": "Aluno excluido com sucesso"}


@router.post("/alunos/importar-csv")
def importar_alunos_csv(
    arquivo: UploadFile = File(...),
    curso_id: int | None = Form(None),
    ano: int | None = Form(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    exigir_alunos(db, usuario)
    if usuario.perfil not in ["admin", "ppdt"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    conteudo = arquivo.file.read().decode("utf-8-sig")
    linhas_conteudo = conteudo.splitlines()
    delimitador = ","
    if linhas_conteudo and linhas_conteudo[0].lower().startswith("sep="):
        delimitador = linhas_conteudo[0].split("=", 1)[1] or ";"
        conteudo = "\n".join(linhas_conteudo[1:])
    elif linhas_conteudo and ";" in linhas_conteudo[0]:
        delimitador = ";"

    leitor = csv.DictReader(io.StringIO(conteudo), delimiter=delimitador)

    criados = 0
    ignorados = 0
    erros = []
    turma_importacao = None

    if curso_id and ano:
        turma_importacao = db.query(Turma).filter(Turma.curso_id == curso_id, Turma.ano == ano).first()
        if not turma_importacao:
            raise HTTPException(status_code=400, detail="Turma nao encontrada para o curso e ano selecionados")

    for indice, linha in enumerate(leitor, start=2):
        try:
            matricula = (linha.get("matricula") or "").strip()
            if not matricula or db.query(Aluno).filter(Aluno.matricula == matricula).first():
                ignorados += 1
                continue

            turma_id = (linha.get("turma_id") or "").strip()
            if turma_importacao:
                turma_id = turma_importacao.id
            elif turma_id:
                turma_id = int(turma_id)
            else:
                ano = int((linha.get("ano") or "").strip())
                letra = (linha.get("letra") or "").strip().upper()
                curso_nome = (linha.get("curso") or "").strip().lower()
                turmas = db.query(Turma).filter(Turma.ano == ano, Turma.letra == letra).all()
                if curso_nome:
                    cursos = {c.id: c for c in db.query(Curso).all()}
                    turmas = [t for t in turmas if cursos.get(t.curso_id) and cursos[t.curso_id].nome.lower() == curso_nome]
                if not turmas:
                    raise ValueError("turma nao encontrada")
                turma_id = turmas[0].id

            aluno = Aluno(
                nome=(linha.get("nome") or "").strip(),
                matricula=matricula,
                data_nascimento=parse_data_nascimento(linha.get("data_nascimento") or ""),
                responsavel=(linha.get("responsavel") or "").strip(),
                contato_responsavel=(linha.get("contato_responsavel") or "").strip(),
                turma_id=turma_id,
                status=(linha.get("status") or "ativo").strip() or "ativo",
            )
            if not aluno.nome or not aluno.responsavel or not aluno.contato_responsavel:
                raise ValueError("campos obrigatorios ausentes")
            db.add(aluno)
            criados += 1
        except Exception as erro:
            ignorados += 1
            erros.append(f"Linha {indice}: {erro}")

    registrar_auditoria(db, usuario, "importou_csv", "aluno", None, f"criados={criados}; ignorados={ignorados}")
    db.commit()

    return {
        "criados": criados,
        "ignorados": ignorados,
        "erros": erros[:10],
    }
