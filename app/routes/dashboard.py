from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict
from datetime import date
from app.database import get_db
from app.models.aluno import Aluno, Turma, Curso
from app.models.registro import Registro
from app.models.ocorrencia import Ocorrencia
from app.models.sistema import AnoLetivo, MatriculaHistorico
from app.models.usuario import Usuario
from app.auth import get_curso_ids_usuario, get_usuario_atual, tem_permissao

router = APIRouter()

def exigir_dashboard(db: Session, usuario: Usuario):
    if not tem_permissao(db, usuario, "dashboard"):
        raise HTTPException(status_code=403, detail="Acesso negado")

def aluno_autorizado(db: Session, usuario: Usuario, aluno: Aluno | None) -> bool:
    if not aluno:
        return False
    if usuario.perfil == "diretor_turma":
        return aluno.turma_id == usuario.turma_id
    if usuario.perfil == "coordenador":
        turma = db.query(Turma).filter(Turma.id == aluno.turma_id).first()
        return bool(turma and turma.curso_id in get_curso_ids_usuario(usuario))
    return True

def alunos_visiveis(db: Session, usuario: Usuario):
    query = db.query(Aluno)
    if usuario.perfil == "diretor_turma":
        return query.filter(Aluno.turma_id == usuario.turma_id).all()
    if usuario.perfil == "coordenador":
        turmas = db.query(Turma).filter(Turma.curso_id.in_(get_curso_ids_usuario(usuario))).all()
        return query.filter(Aluno.turma_id.in_([t.id for t in turmas])).all()
    return query.all()

def turmas_visiveis(db: Session, usuario: Usuario):
    query = db.query(Turma).order_by(Turma.curso_id, Turma.ano)
    if usuario.perfil == "diretor_turma":
        return query.filter(Turma.id == usuario.turma_id).all()
    if usuario.perfil == "coordenador":
        return query.filter(Turma.curso_id.in_(get_curso_ids_usuario(usuario))).all()
    return query.all()

def nome_turma(turma, curso):
    if not turma:
        return "-"
    return f"{turma.ano}º {turma.letra} - {curso.nome if curso else ''}"

def pertence_ao_ano_letivo(item, ano_letivo_id=None, ano_letivo_numero=None):
    item_ano_id = getattr(item, "ano_letivo_id", None)
    if ano_letivo_id and item_ano_id:
        return item_ano_id == ano_letivo_id
    if ano_letivo_numero and hasattr(item, "data"):
        return item.data.year == ano_letivo_numero
    return True


def aluno_pertence_ao_ano_letivo(aluno, ano_letivo_id=None):
    if not ano_letivo_id:
        return True
    aluno_ano_id = getattr(aluno, "ano_letivo_id", None)
    return not aluno_ano_id or aluno_ano_id == ano_letivo_id


def filtrar_por_data(itens, data_inicio=None, data_fim=None, mes=None, ano_letivo=None, ano_letivo_id=None):
    filtrados = []
    for item in itens:
        data_item = item.data
        if not pertence_ao_ano_letivo(item, ano_letivo_id, ano_letivo):
            continue
        if mes and data_item.month != mes:
            continue
        if data_inicio and data_item < data_inicio:
            continue
        if data_fim and data_item > data_fim:
            continue
        filtrados.append(item)
    return filtrados

def aluno_no_recorte(aluno, turmas_validas, turma_id=None):
    if turma_id:
        return aluno.turma_id == turma_id
    return aluno.turma_id in turmas_validas

@router.get("/dashboard/gerencial")
def dashboard_gerencial(
    curso_id: int | None = Query(default=None),
    turma_id: int | None = Query(default=None),
    mes: int | None = Query(default=None),
    ano_letivo: int | None = Query(default=None),
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    exigir_dashboard(db, usuario)
    ano_letivo_registro = db.query(AnoLetivo).filter(AnoLetivo.ano == ano_letivo).first() if ano_letivo else None
    ano_letivo_id = ano_letivo_registro.id if ano_letivo_registro else None
    cursos = db.query(Curso).order_by(Curso.nome).all()
    turmas_query = db.query(Turma).order_by(Turma.ano, Turma.letra)
    if usuario.perfil == "diretor_turma":
        turma_id = usuario.turma_id
    elif usuario.perfil == "coordenador":
        curso_ids = get_curso_ids_usuario(usuario)
        cursos = [c for c in cursos if c.id in curso_ids]
        turmas_query = turmas_query.filter(Turma.curso_id.in_(curso_ids))
        if curso_id and curso_id not in curso_ids:
            raise HTTPException(status_code=403, detail="Acesso negado")
    if curso_id:
        turmas_query = turmas_query.filter(Turma.curso_id == curso_id)
    turmas = turmas_query.all()

    todos_cursos = {c.id: c for c in cursos}
    todas_turmas_query = db.query(Turma).order_by(Turma.ano, Turma.letra)
    if usuario.perfil == "diretor_turma":
        todas_turmas_query = todas_turmas_query.filter(Turma.id == usuario.turma_id)
    elif usuario.perfil == "coordenador":
        todas_turmas_query = todas_turmas_query.filter(Turma.curso_id.in_(get_curso_ids_usuario(usuario)))
    todas_turmas = todas_turmas_query.all()
    turmas_por_id = {t.id: t for t in todas_turmas}
    turmas_validas = {t.id for t in turmas}

    alunos_todos = db.query(Aluno).all()
    alunos = [
        a for a in alunos_todos
        if aluno_no_recorte(a, turmas_validas, turma_id) and aluno_pertence_ao_ano_letivo(a, ano_letivo_id)
    ]
    aluno_ids = {a.id for a in alunos}

    registros = [r for r in db.query(Registro).all() if r.aluno_id in aluno_ids]
    ocorrencias = [o for o in db.query(Ocorrencia).all() if o.aluno_id in aluno_ids]
    registros = filtrar_por_data(registros, data_inicio, data_fim, mes, ano_letivo, ano_letivo_id)
    ocorrencias = filtrar_por_data(ocorrencias, data_inicio, data_fim, mes, ano_letivo, ano_letivo_id)

    atrasos = [r for r in registros if r.tipo == "Atraso"]
    saidas = [r for r in registros if r.tipo != "Atraso"]
    ocorrencias_abertas = [o for o in ocorrencias if (o.status or "Aberta") == "Aberta"]
    ocorrencias_graves = [o for o in ocorrencias if (o.gravidade or "Leve") == "Grave"]

    alunos_por_id = {a.id: a for a in alunos}

    resumo = {
        "alunos_ativos": sum(1 for a in alunos if (a.status or "ativo") == "ativo"),
        "total_alunos": len(alunos),
        "atrasos": len(atrasos),
        "saidas": len(saidas),
        "ocorrencias": len(ocorrencias),
        "ocorrencias_abertas": len(ocorrencias_abertas),
        "ocorrencias_graves": len(ocorrencias_graves),
        "ocorrencias_resolvidas": sum(1 for o in ocorrencias if (o.status or "") == "Resolvida")
    }

    por_turma = []
    for turma in turmas:
        if turma_id and turma.id != turma_id:
            continue
        curso = todos_cursos.get(turma.curso_id)
        ids_turma = {a.id for a in alunos if a.turma_id == turma.id}
        por_turma.append({
            "turma": nome_turma(turma, curso),
            "atrasos": sum(1 for r in atrasos if r.aluno_id in ids_turma),
            "saidas": sum(1 for r in saidas if r.aluno_id in ids_turma),
            "ocorrencias": sum(1 for o in ocorrencias if o.aluno_id in ids_turma)
        })

    meses = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
    }
    evolucao_map = {i: {"mes": meses[i], "atrasos": 0, "saidas": 0, "ocorrencias": 0} for i in range(1, 13)}
    for r in registros:
        chave = r.data.month
        if r.tipo == "Atraso":
            evolucao_map[chave]["atrasos"] += 1
        else:
            evolucao_map[chave]["saidas"] += 1
    for o in ocorrencias:
        evolucao_map[o.data.month]["ocorrencias"] += 1
    evolucao_mensal = list(evolucao_map.values())

    status_ocorrencias = [
        {"status": "Aberta", "total": sum(1 for o in ocorrencias if (o.status or "Aberta") == "Aberta")},
        {"status": "Em acompanhamento", "total": sum(1 for o in ocorrencias if (o.status or "") == "Em acompanhamento")},
        {"status": "Resolvida", "total": sum(1 for o in ocorrencias if (o.status or "") == "Resolvida")}
    ]

    dados_alunos = defaultdict(lambda: {"atrasos": 0, "saidas": 0, "ocorrencias": 0, "graves": 0, "abertas": 0})
    for r in registros:
        if r.tipo == "Atraso":
            dados_alunos[r.aluno_id]["atrasos"] += 1
        else:
            dados_alunos[r.aluno_id]["saidas"] += 1
    for o in ocorrencias:
        dados_alunos[o.aluno_id]["ocorrencias"] += 1
        if (o.gravidade or "Leve") == "Grave":
            dados_alunos[o.aluno_id]["graves"] += 1
        if (o.status or "Aberta") == "Aberta":
            dados_alunos[o.aluno_id]["abertas"] += 1

    def montar_linha_aluno(aluno_id, dados):
        aluno = alunos_por_id.get(aluno_id)
        turma = turmas_por_id.get(aluno.turma_id) if aluno else None
        curso = todos_cursos.get(turma.curso_id) if turma else None
        return {
            "id": aluno.id if aluno else aluno_id,
            "nome": aluno.nome if aluno else "-",
            "turma": nome_turma(turma, curso),
            **dados
        }

    linhas = [montar_linha_aluno(aluno_id, dados) for aluno_id, dados in dados_alunos.items()]
    ranking_atencao = sorted(
        linhas,
        key=lambda x: (x["ocorrencias"] * 3) + (x["graves"] * 4) + (x["abertas"] * 2) + x["atrasos"],
        reverse=True
    )[:10]
    ranking_atrasos = sorted([x for x in linhas if x["atrasos"] > 0], key=lambda x: x["atrasos"], reverse=True)[:10]
    ranking_ocorrencias = sorted([x for x in linhas if x["ocorrencias"] > 0], key=lambda x: x["ocorrencias"], reverse=True)[:10]
    alunos_criticos = [
        x for x in linhas
        if x["graves"] > 0 or x["abertas"] >= 2 or (x["atrasos"] >= 3 and x["ocorrencias"] >= 1)
    ]
    alunos_criticos = sorted(
        alunos_criticos,
        key=lambda x: (x["graves"] * 5) + (x["abertas"] * 3) + x["ocorrencias"] + x["atrasos"],
        reverse=True
    )[:10]

    return {
        "filtros": {
            "cursos": [{"id": c.id, "nome": c.nome} for c in cursos],
            "turmas": [
                {"id": t.id, "curso_id": t.curso_id, "nome": nome_turma(t, todos_cursos.get(t.curso_id))}
                for t in todas_turmas
            ]
        },
        "resumo": resumo,
        "por_turma": por_turma,
        "evolucao_mensal": evolucao_mensal,
        "status_ocorrencias": status_ocorrencias,
        "ranking_atencao": ranking_atencao,
        "ranking_atrasos": ranking_atrasos,
        "ranking_ocorrencias": ranking_ocorrencias,
        "alunos_criticos": alunos_criticos
    }

@router.get("/dashboard/resumo")
def resumo_geral(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_dashboard(db, usuario)
    alunos = alunos_visiveis(db, usuario)
    aluno_ids = [a.id for a in alunos]
    total_alunos = len(alunos)
    total_ocorrencias = db.query(Ocorrencia).filter(Ocorrencia.aluno_id.in_(aluno_ids)).count()
    total_atrasos = db.query(Registro).filter(Registro.aluno_id.in_(aluno_ids), Registro.tipo == "Atraso").count()
    total_saidas = db.query(Registro).filter(Registro.aluno_id.in_(aluno_ids), Registro.tipo == "Saída antecipada").count()
    return {
        "total_alunos": total_alunos,
        "total_ocorrencias": total_ocorrencias,
        "total_atrasos": total_atrasos,
        "total_saidas": total_saidas
    }

@router.get("/dashboard/atrasos-por-turma")
def atrasos_por_turma(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_dashboard(db, usuario)
    turmas = turmas_visiveis(db, usuario)
    cursos = db.query(Curso).all()
    alunos = alunos_visiveis(db, usuario)
    registros = db.query(Registro).all()

    resultado = []
    for t in turmas:
        curso = next((c for c in cursos if c.id == t.curso_id), None)
        alunos_turma = [a.id for a in alunos if a.turma_id == t.id]
        total = sum(1 for r in registros if r.aluno_id in alunos_turma and r.tipo == "Atraso")
        resultado.append({
            "turma": f"{t.ano}º {t.letra} - {curso.nome if curso else ''}",
            "total": total
        })
    return resultado

@router.get("/dashboard/ocorrencias-por-turma")
def ocorrencias_por_turma(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_dashboard(db, usuario)
    turmas = turmas_visiveis(db, usuario)
    cursos = db.query(Curso).all()
    alunos = alunos_visiveis(db, usuario)
    ocorrencias = db.query(Ocorrencia).all()

    resultado = []
    for t in turmas:
        curso = next((c for c in cursos if c.id == t.curso_id), None)
        alunos_turma = [a.id for a in alunos if a.turma_id == t.id]
        total = sum(1 for o in ocorrencias if o.aluno_id in alunos_turma)
        resultado.append({
            "turma": f"{t.ano}º {t.letra} - {curso.nome if curso else ''}",
            "total": total
        })
    return resultado

@router.get("/dashboard/ranking-ocorrencias")
def ranking_ocorrencias(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_dashboard(db, usuario)
    alunos = alunos_visiveis(db, usuario)
    ocorrencias = db.query(Ocorrencia).all()
    turmas = db.query(Turma).all()
    cursos = db.query(Curso).all()

    ranking = []
    for a in alunos:
        total = sum(1 for o in ocorrencias if o.aluno_id == a.id)
        if total > 0:
            t = next((t for t in turmas if t.id == a.turma_id), None)
            c = next((c for c in cursos if c.id == t.curso_id), None) if t else None
            ranking.append({
                "nome": a.nome,
                "turma": f"{t.ano}º {t.letra} - {c.nome if c else ''}" if t else '-',
                "total": total
            })

    return sorted(ranking, key=lambda x: x["total"], reverse=True)[:10]

@router.get("/dashboard/ranking-atrasos")
def ranking_atrasos(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_dashboard(db, usuario)
    alunos = alunos_visiveis(db, usuario)
    registros = db.query(Registro).all()
    turmas = db.query(Turma).all()
    cursos = db.query(Curso).all()

    ranking = []
    for a in alunos:
        total = sum(1 for r in registros if r.aluno_id == a.id and r.tipo == "Atraso")
        if total > 0:
            t = next((t for t in turmas if t.id == a.turma_id), None)
            c = next((c for c in cursos if c.id == t.curso_id), None) if t else None
            ranking.append({
                "nome": a.nome,
                "turma": f"{t.ano}º {t.letra} - {c.nome if c else ''}" if t else '-',
                "total": total
            })

    return sorted(ranking, key=lambda x: x["total"], reverse=True)[:10]

@router.get("/dashboard/aluno/{aluno_id}")
def dashboard_aluno(aluno_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    exigir_dashboard(db, usuario)
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno_autorizado(db, usuario, aluno):
        raise HTTPException(status_code=403, detail="Acesso negado")
    turma = db.query(Turma).filter(Turma.id == aluno.turma_id).first()
    curso = db.query(Curso).filter(Curso.id == turma.curso_id).first() if turma else None

    ocorrencias = db.query(Ocorrencia).filter(Ocorrencia.aluno_id == aluno_id).order_by(Ocorrencia.data).all()
    registros = db.query(Registro).filter(Registro.aluno_id == aluno_id).order_by(Registro.data).all()
    matriculas = db.query(MatriculaHistorico).filter(
        MatriculaHistorico.aluno_id == aluno_id
    ).order_by(MatriculaHistorico.data_inicio.desc()).all()
    turmas = {t.id: t for t in db.query(Turma).all()}
    cursos = {c.id: c for c in db.query(Curso).all()}
    anos = {a.id: a for a in db.query(AnoLetivo).all()}

    total_ocorrencias = len(ocorrencias)
    total_atrasos = sum(1 for r in registros if r.tipo == "Atraso")
    total_saidas = sum(1 for r in registros if r.tipo == "Saída antecipada")

    if total_ocorrencias == 0:
        proxima_medida = "Só registro"
    elif total_ocorrencias == 1:
        proxima_medida = "Advertência + Notificação ao responsável"
    else:
        proxima_medida = "Suspensão + Notificação ao responsável"

    return {
        "aluno": {
            "id": aluno.id,
            "nome": aluno.nome,
            "matricula": aluno.matricula,
            "turma": f"{turma.ano}º {turma.letra} - {curso.nome if curso else ''}" if turma else '-',
            "responsavel": aluno.responsavel,
            "contato_responsavel": aluno.contato_responsavel
        },
        "resumo": {
            "total_ocorrencias": total_ocorrencias,
            "total_atrasos": total_atrasos,
            "total_saidas": total_saidas,
            "proxima_medida": proxima_medida
        },
        "ocorrencias": [{"data": str(o.data), "tipo": o.tipo, "descricao": o.descricao, "medida": o.medida} for o in ocorrencias],
        "registros": [{"data": str(r.data), "tipo": r.tipo, "aula": r.aula, "motivo": r.motivo} for r in registros],
        "matriculas": [
            {
                "ano_letivo": anos.get(m.ano_letivo_id).nome if anos.get(m.ano_letivo_id) else "-",
                "turma": nome_turma(turmas.get(m.turma_id), cursos.get(turmas.get(m.turma_id).curso_id) if turmas.get(m.turma_id) else None),
                "status": m.status,
                "data_inicio": str(m.data_inicio),
                "data_fim": str(m.data_fim) if m.data_fim else None,
            }
            for m in matriculas
        ]
    }
