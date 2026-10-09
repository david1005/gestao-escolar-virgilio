from datetime import datetime
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict, StrictBool
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from app.auth import get_usuario_atual
from app.database import get_db
from app.models.notificacao import Notificacao, PreferenciaNotificacao
from app.services.preferencias_notificacao import preferencias_usuario
from app.models.usuario import Usuario
from app.services.notificacoes import sincronizar, notificacoes_visiveis, MODELOS, pode_ver

router = APIRouter()


class PreferenciasForm(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ocorrencia_antiga: StrictBool
    retorno_pendente: StrictBool
    alteracao: StrictBool


@router.get('/notificacoes/preferencias')
def obter_preferencias(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    return {**preferencias_usuario(db, usuario.id), 'seguranca': usuario.perfil == 'admin'}


@router.put('/notificacoes/preferencias')
def salvar_preferencias(dados: PreferenciasForm, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    valores = dados.model_dump()
    insert = pg_insert if db.get_bind().dialect.name == 'postgresql' else sqlite_insert
    comando = insert(PreferenciaNotificacao).values(usuario_id=usuario.id, **valores)
    db.execute(comando.on_conflict_do_update(index_elements=['usuario_id'], set_=valores))
    db.expire_all()
    db.commit()
    return obter_preferencias(db, usuario)


def serializar(n):
    return {k: getattr(n, k) for k in ('id', 'tipo', 'titulo', 'mensagem',
        'ativa', 'lida_em', 'criada_em', 'atualizada_em')}


@router.get('/notificacoes/resumo')
def resumo(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    sincronizar(db, usuario)
    itens = [n for n in notificacoes_visiveis(db, usuario) if n.ativa]
    db.commit()
    return {'nao_lidas': sum(n.lida_em is None for n in itens),
            'items': [serializar(n) for n in itens[:5]]}


@router.get('/notificacoes/')
def listar(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
           leitura: str = Query('todas', pattern='^(todas|lidas|nao_lidas)$'),
           tipo: str = '', db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    sincronizar(db, usuario)
    itens = notificacoes_visiveis(db, usuario)
    if tipo:
        itens = [n for n in itens if n.tipo == tipo]
    if leitura != 'todas':
        itens = [n for n in itens if (n.lida_em is None) == (leitura == 'nao_lidas')]
    total = len(itens)
    dados = [serializar(n) for n in itens[(page-1)*page_size:page*page_size]]
    db.commit()
    return {'items': dados, 'total': total, 'page': page, 'pages': max(1, ceil(total/page_size))}


@router.put('/notificacoes/ler-todas')
def ler_todas(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    db.query(Notificacao).filter_by(usuario_id=usuario.id, lida_em=None).update(
        {Notificacao.lida_em: datetime.now()}, synchronize_session=False)
    db.commit()
    return {'ok': True}


@router.put('/notificacoes/{id}/ler')
def ler(id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    n = db.query(Notificacao).filter_by(id=id, usuario_id=usuario.id).first()
    if not n:
        raise HTTPException(404, 'Notificacao nao encontrada')
    n.lida_em = n.lida_em or datetime.now()
    db.commit()
    return {'ok': True}


@router.get('/notificacoes/{id}/abrir')
def abrir(id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    n = db.query(Notificacao).filter_by(id=id, usuario_id=usuario.id).first()
    if not n:
        raise HTTPException(404, 'Notificacao nao encontrada')
    if n.tipo == 'seguranca':
        if usuario.perfil != 'admin':
            raise HTTPException(403, 'Acesso negado')
        destino = '/configuracoes'
    else:
        model = MODELOS.get(n.entidade)
        item = db.get(model, n.entidade_id) if model else None
        if not item or not pode_ver(db, usuario, n.entidade, item):
            raise HTTPException(403, 'Item removido ou acesso negado')
        destino = f'/{"ocorrencias" if n.entidade == "ocorrencia" else "registros"}?notificacao={item.id}'
    return RedirectResponse(destino, status_code=303)
