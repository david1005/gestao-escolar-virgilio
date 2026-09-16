import csv
import io
import re
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_curso_ids_usuario, get_usuario_atual, tem_permissao
from app.database import get_db
from app.models.aluno import Aluno, Curso, Turma
from app.models.auditoria import Auditoria
from app.models.ocorrencia import Ocorrencia
from app.models.registro import Registro
from app.models.sistema import AnoLetivo, MatriculaHistorico
from app.models.usuario import Usuario
from app.schemas import aluno as schemas
from app.schemas.aluno import AlunoCreate, AlunoUpdate, CursoCreate, TurmaCreate
from app.services.ano_letivo import obter_ano_letivo_ativo

router = APIRouter()


def limpar_prefixo_nome_aluno(nome: str | None):
    return re.sub(r"^\s*\d+\s*[-.)]\s*", "", nome or "").strip()


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


def preparar_csv_importacao(arquivo: UploadFile):
    conteudo = arquivo.file.read().decode("utf-8-sig")
    linhas_conteudo = conteudo.splitlines()
    delimitador = ","
    if linhas_conteudo and linhas_conteudo[0].lower().startswith("sep="):
        delimitador = linhas_conteudo[0].split("=", 1)[1] or ";"
        conteudo = "\n".join(linhas_conteudo[1:])
    elif linhas_conteudo and ";" in linhas_conteudo[0]:
        delimitador = ";"
    return csv.DictReader(io.StringIO(conteudo), delimiter=delimitador)


def resolver_turma_importacao(db: Session, linha: dict, turma_importacao: Turma | None):
    if turma_importacao:
        return turma_importacao

    turma_id = (linha.get("turma_id") or "").strip()
    if turma_id:
        turma = db.query(Turma).filter(Turma.id == int(turma_id)).first()
        if not turma:
            raise ValueError("turma nao encontrada")
        return turma

    ano = int((linha.get("ano") or "").strip())
    letra = (linha.get("letra") or "").strip().upper()
    curso_nome = (linha.get("curso") or "").strip().lower()
    turmas = db.query(Turma).filter(Turma.ano == ano, Turma.letra == letra).all()
    if curso_nome:
        cursos = {c.id: c for c in db.query(Curso).all()}
        turmas = [t for t in turmas if cursos.get(t.curso_id) and cursos[t.curso_id].nome.lower() == curso_nome]
    if not turmas:
        raise ValueError("turma nao encontrada")
    return turmas[0]


def label_turma_importacao(db: Session, turma: Turma | None):
    if not turma:
        return "-"
    curso = db.query(Curso).filter(Curso.id == turma.curso_id).first()
    return f"{turma.ano}º {turma.letra} - {curso.nome if curso else ''}"


def analisar_linhas_importacao(db: Session, leitor, turma_importacao: Turma | None):
    previa = []
    totais = {"criar": 0, "ignorar": 0, "erro": 0}

    for indice, linha in enumerate(leitor, start=2):
        matricula = (linha.get("matricula") or "").strip()
        item = {
            "linha": indice,
            "nome": limpar_prefixo_nome_aluno(linha.get("nome")),
            "matricula": matricula,
            "turma": "-",
            "status": "criar",
            "mensagem": "Pronto para importar",
        }
        try:
            if not matricula:
                item["status"] = "erro"
                item["mensagem"] = "Matricula obrigatoria"
            elif db.query(Aluno).filter(Aluno.matricula == matricula).first():
                item["status"] = "ignorar"
                item["mensagem"] = "Matricula ja cadastrada"
            else:
                turma = resolver_turma_importacao(db, linha, turma_importacao)
                item["turma"] = label_turma_importacao(db, turma)
                parse_data_nascimento(linha.get("data_nascimento") or "")
                if not item["nome"] or not (linha.get("responsavel") or "").strip() or not (linha.get("contato_responsavel") or "").strip():
                    raise ValueError("campos obrigatorios ausentes")
        except Exception as erro:
            item["status"] = "erro"
            item["mensagem"] = str(erro)

        totais[item["status"]] += 1
        previa.append(item)

    return {"totais": totais, "linhas": previa}


def calcular_previa_virada(db: Session):
    turmas = db.query(Turma).all()
    alunos = db.query(Aluno).filter(Aluno.status == "ativo").all()
    cursos = {curso.id: curso for curso in db.query(Curso).all()}
    turmas_por_id = {turma.id: turma for turma in turmas}
    destinos = {(turma.ano, turma.letra, turma.curso_id): turma for turma in turmas}
    por_ano = {1: 0, 2: 0, 3: 0}
    sem_destino = 0
    alunos_por_turma = {}

    def label_turma(turma: Turma | None):
        if not turma:
            return "Sem turma"
        curso = cursos.get(turma.curso_id)
        return f"{turma.ano}º {turma.letra} - {curso.nome if curso else ''}"

    for aluno in alunos:
        turma = turmas_por_id.get(aluno.turma_id)
        if not turma:
            sem_destino += 1
            alunos_por_turma.setdefault(None, 0)
            alunos_por_turma[None] += 1
            continue

        por_ano[turma.ano] = por_ano.get(turma.ano, 0) + 1
        alunos_por_turma[turma.id] = alunos_por_turma.get(turma.id, 0) + 1
        if turma.ano in [1, 2] and (turma.ano + 1, turma.letra, turma.curso_id) not in destinos:
            sem_destino += 1

    movimentos = []
    for turma_id, total in sorted(
        alunos_por_turma.items(),
        key=lambda item: (
            99 if item[0] is None else turmas_por_id[item[0]].ano,
            "" if item[0] is None else turmas_por_id[item[0]].letra,
        ),
    ):
        turma = turmas_por_id.get(turma_id) if turma_id is not None else None
        if not turma:
            movimentos.append({
                "origem": "Sem turma",
                "destino": "-",
                "total": total,
                "resultado": "Sem turma de origem",
                "status": "erro",
            })
            continue

        if turma.ano == 3:
            movimentos.append({
                "origem": label_turma(turma),
                "destino": "Concluido",
                "total": total,
                "resultado": "Alunos serao marcados como concluidos",
                "status": "concluir",
            })
            continue

        destino = destinos.get((turma.ano + 1, turma.letra, turma.curso_id))
        movimentos.append({
            "origem": label_turma(turma),
            "destino": label_turma(destino) if destino else "Turma de destino nao encontrada",
            "total": total,
            "resultado": "Promocao preparada" if destino else "Crie a turma de destino antes da virada",
            "status": "promover" if destino else "erro",
        })

    ano_letivo = obter_ano_letivo_ativo(db)
    proximo_ano = db.query(AnoLetivo).filter(AnoLetivo.ano == ano_letivo.ano + 1).first()
    return {
        "ano_letivo": {
            "id": ano_letivo.id,
            "nome": ano_letivo.nome,
            "ano": ano_letivo.ano,
        },
        "proximo_ano_letivo": {
            "id": proximo_ano.id if proximo_ano else None,
            "nome": proximo_ano.nome if proximo_ano else f"Ano Letivo {ano_letivo.ano + 1}",
            "ano": ano_letivo.ano + 1,
            "sera_criado": proximo_ano is None,
            "encerrado": bool(proximo_ano.encerrado) if proximo_ano else False,
        },
        "primeiro_para_segundo": por_ano.get(1, 0),
        "segundo_para_terceiro": por_ano.get(2, 0),
        "terceiro_concluido": por_ano.get(3, 0),
        "sem_destino": sem_destino,
        "movimentos": movimentos,
    }


def preencher_ano_letivo_em_historico(db: Session, ano_letivo_id: int):
    db.query(Aluno).filter(Aluno.ano_letivo_id == None).update({Aluno.ano_letivo_id: ano_letivo_id})
    db.query(Registro).filter(Registro.ano_letivo_id == None).update({Registro.ano_letivo_id: ano_letivo_id})
    db.query(Ocorrencia).filter(Ocorrencia.ano_letivo_id == None).update({Ocorrencia.ano_letivo_id: ano_letivo_id})


def registrar_matricula_historico(db: Session, aluno: Aluno, ano_letivo_id: int, status: str = "ativo"):
    existente = db.query(MatriculaHistorico).filter(
        MatriculaHistorico.aluno_id == aluno.id,
        MatriculaHistorico.turma_id == aluno.turma_id,
        MatriculaHistorico.ano_letivo_id == ano_letivo_id,
        MatriculaHistorico.data_fim == None,
    ).first()
    if existente:
        existente.status = status
        return existente
    historico_aberto = db.query(MatriculaHistorico).filter(
        MatriculaHistorico.aluno_id == aluno.id,
        MatriculaHistorico.data_fim == None,
    ).first()
    if historico_aberto:
        historico_aberto.data_fim = date.today()
        historico_aberto.status = status if status != "ativo" else "encerrada"
    novo = MatriculaHistorico(
        aluno_id=aluno.id,
        turma_id=aluno.turma_id,
        ano_letivo_id=ano_letivo_id,
        status=status,
        data_inicio=date.today(),
    )
    db.add(novo)
    return novo


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
    ano_letivo = obter_ano_letivo_ativo(db)
    dados = aluno.model_dump()
    dados["nome"] = limpar_prefixo_nome_aluno(dados.get("nome"))
    db_aluno = Aluno(**dados, ano_letivo_id=ano_letivo.id)
    db.add(db_aluno)
    db.flush()
    registrar_matricula_historico(db, db_aluno, ano_letivo.id, db_aluno.status)
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
    return sorted(alunos, key=lambda aluno: limpar_prefixo_nome_aluno(aluno.nome).casefold())


@router.get("/alunos/virada-ano/previa")
def previa_virada_ano(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_alunos(db, usuario)
    if usuario.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    ano_letivo = obter_ano_letivo_ativo(db)
    preencher_ano_letivo_em_historico(db, ano_letivo.id)
    db.commit()
    return calcular_previa_virada(db)


@router.post("/alunos/virada-ano")
def realizar_virada_ano(
    proximo_inicio: date | None = Form(None),
    proximo_fim: date | None = Form(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    exigir_alunos(db, usuario)
    if usuario.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")

    ano_letivo_atual = obter_ano_letivo_ativo(db)
    preencher_ano_letivo_em_historico(db, ano_letivo_atual.id)

    proximo_ano = db.query(AnoLetivo).filter(AnoLetivo.ano == ano_letivo_atual.ano + 1).first()
    criou_proximo_ano = False
    if proximo_ano and proximo_ano.encerrado:
        raise HTTPException(status_code=400, detail="O proximo ano letivo ja existe, mas esta encerrado")
    if not proximo_ano:
        proximo_numero = ano_letivo_atual.ano + 1
        proximo_ano = AnoLetivo(
            nome=f"Ano Letivo {proximo_numero}",
            ano=proximo_numero,
            data_inicio=proximo_inicio or date(proximo_numero, 2, 1),
            data_fim=proximo_fim or date(proximo_numero, 12, 31),
            ativo=True,
        )
        db.add(proximo_ano)
        db.flush()
        criou_proximo_ano = True
    elif proximo_inicio and proximo_fim:
        proximo_ano.data_inicio = proximo_inicio
        proximo_ano.data_fim = proximo_fim

    ano_letivo_atual.encerrado = True
    ano_letivo_atual.ativo = False
    proximo_ano.ativo = True
    proximo_ano.encerrado = False

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
            registrar_matricula_historico(db, aluno, ano_letivo_atual.id, "concluido")
            concluidos += 1
            continue

        destino_id = proxima_turma.get((turma_atual.ano + 1, turma_atual.letra, turma_atual.curso_id))
        if destino_id:
            aluno.turma_id = destino_id
            aluno.ano_letivo_id = proximo_ano.id
            registrar_matricula_historico(db, aluno, proximo_ano.id, aluno.status)
            promovidos += 1

    registrar_auditoria(
        db,
        usuario,
        "virada_ano",
        "aluno",
        None,
        f"origem={ano_letivo_atual.nome}; destino={proximo_ano.nome}; promovidos={promovidos}; concluidos={concluidos}",
    )
    db.commit()
    return {
        "mensagem": "Virada de ano letivo realizada com sucesso",
        "ano_origem": ano_letivo_atual.nome,
        "ano_destino": proximo_ano.nome,
        "proximo_ano_criado": criou_proximo_ano,
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

    turma_anterior = aluno.turma_id
    status_anterior = aluno.status
    dados_limpos = dados.model_dump()
    dados_limpos["nome"] = limpar_prefixo_nome_aluno(dados_limpos.get("nome"))
    for campo, valor in dados_limpos.items():
        setattr(aluno, campo, valor)
    ano_letivo = obter_ano_letivo_ativo(db)
    if aluno.turma_id != turma_anterior or aluno.status != status_anterior:
        aluno.ano_letivo_id = ano_letivo.id
        registrar_matricula_historico(db, aluno, ano_letivo.id, aluno.status)

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

    leitor = preparar_csv_importacao(arquivo)

    criados = 0
    ignorados = 0
    erros = []
    turma_importacao = None
    ano_letivo_importacao = obter_ano_letivo_ativo(db)

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

            turma = resolver_turma_importacao(db, linha, turma_importacao)

            aluno = Aluno(
                nome=limpar_prefixo_nome_aluno(linha.get("nome")),
                matricula=matricula,
                data_nascimento=parse_data_nascimento(linha.get("data_nascimento") or ""),
                responsavel=(linha.get("responsavel") or "").strip(),
                contato_responsavel=(linha.get("contato_responsavel") or "").strip(),
                turma_id=turma.id,
                status=(linha.get("status") or "ativo").strip() or "ativo",
                ano_letivo_id=ano_letivo_importacao.id,
            )
            if not aluno.nome or not aluno.responsavel or not aluno.contato_responsavel:
                raise ValueError("campos obrigatorios ausentes")
            db.add(aluno)
            db.flush()
            registrar_matricula_historico(db, aluno, ano_letivo_importacao.id, aluno.status)
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


@router.post("/alunos/importar-csv/preview")
def preview_importar_alunos_csv(
    arquivo: UploadFile = File(...),
    curso_id: int | None = Form(None),
    ano: int | None = Form(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    exigir_alunos(db, usuario)
    if usuario.perfil not in ["admin", "ppdt"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    turma_importacao = None
    if curso_id and ano:
        turma_importacao = db.query(Turma).filter(Turma.curso_id == curso_id, Turma.ano == ano).first()
        if not turma_importacao:
            raise HTTPException(status_code=400, detail="Turma nao encontrada para o curso e ano selecionados")

    leitor = preparar_csv_importacao(arquivo)
    return analisar_linhas_importacao(db, leitor, turma_importacao)
