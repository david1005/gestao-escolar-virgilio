from datetime import date, datetime, timedelta
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app.auth import tem_permissao, usuario_pode_acessar_aluno
from app.models.aluno import Aluno
from app.models.notificacao import Notificacao
from app.models.ocorrencia import Ocorrencia
from app.models.registro import Registro
from app.models.usuario import Usuario


MODELOS = {'ocorrencia': Ocorrencia, 'registro': Registro}
MODULOS = {'ocorrencia': 'ocorrencias', 'registro': 'registros'}


def pode_ver(db, usuario, entidade, item):
    if not usuario.ativo or not tem_permissao(db, usuario, MODULOS[entidade]):
        return False
    aluno = db.get(Aluno, item.aluno_id)
    return aluno is not None and usuario_pode_acessar_aluno(db, usuario, aluno)


def gravar(db, usuario_id, chave, tipo, titulo, mensagem, entidade=None, entidade_id=None):
    n = db.query(Notificacao).filter_by(usuario_id=usuario_id, chave_deduplicacao=chave).first()
    if n is None:
        # A unique constraint also protects simultaneous browser refreshes.
        try:
            with db.begin_nested():
                n = Notificacao(usuario_id=usuario_id, chave_deduplicacao=chave,
                    tipo=tipo, titulo=titulo, mensagem=mensagem,
                    entidade=entidade, entidade_id=entidade_id, ativa=True)
                db.add(n)
                db.flush()
        except IntegrityError:
            n = db.query(Notificacao).filter_by(usuario_id=usuario_id, chave_deduplicacao=chave).one()
    else:
        if not n.ativa:
            n.ativa = True
            n.lida_em = None
            n.atualizada_em = datetime.now()
        if n.mensagem != mensagem or tipo == 'alteracao':
            n.mensagem = mensagem
            n.atualizada_em = datetime.now()
    return n


def sincronizar(db, usuario):
    desejadas = set()
    regras = [
        ('ocorrencia', 'ocorrencia_antiga', db.query(Ocorrencia).filter(
            Ocorrencia.status.in_(['Aberta', 'Em acompanhamento']),
            Ocorrencia.data < date.today() - timedelta(days=15)),
            'Ocorrência pendente', 'Ocorrência aberta há mais de 15 dias.'),
        ('registro', 'retorno_pendente', db.query(Registro).filter(
            Registro.tipo != 'Atraso', Registro.tipo_saida == 'temporaria',
            Registro.status_retorno == 'Pendente'),
            'Retorno não confirmado', 'Saída temporária com retorno pendente.'),
    ]
    for entidade, tipo, query, titulo, mensagem in regras:
        if not tem_permissao(db, usuario, MODULOS[entidade]):
            continue
        for item in query.all():
            if pode_ver(db, usuario, entidade, item):
                chave = f'{tipo}:{item.id}'
                desejadas.add(chave)
                aluno = db.get(Aluno, item.aluno_id)
                gravar(db, usuario.id, chave, tipo, titulo, f'{aluno.nome}: {mensagem}', entidade, item.id)
    for n in db.query(Notificacao).filter(
        Notificacao.usuario_id == usuario.id,
        Notificacao.tipo.in_(['ocorrencia_antiga', 'retorno_pendente']),
        Notificacao.ativa == True).all():
        if n.chave_deduplicacao not in desejadas:
            n.ativa = False
            n.lida_em = n.lida_em or datetime.now()
    db.flush()


def notificacoes_visiveis(db, usuario):
    resultado = []
    for n in db.query(Notificacao).filter_by(usuario_id=usuario.id).order_by(
        Notificacao.atualizada_em.desc(), Notificacao.id.desc()).all():
        if n.tipo == 'seguranca':
            if usuario.perfil == 'admin' and usuario.ativo:
                resultado.append(n)
        elif n.entidade in MODELOS:
            item = db.get(MODELOS[n.entidade], n.entidade_id)
            if item and pode_ver(db, usuario, n.entidade, item):
                resultado.append(n)
    return resultado


def notificar_edicao(db, entidade, item, editor):
    criador_id = getattr(item, 'criado_por_id', None)
    if not criador_id or criador_id == editor.id:
        return
    criador = db.get(Usuario, criador_id)
    if not criador or not pode_ver(db, criador, entidade, item):
        return
    anterior = db.query(Notificacao).filter_by(usuario_id=criador.id,
        tipo='alteracao', entidade=entidade, entidade_id=item.id, ativa=True,
        lida_em=None).first()
    chave = anterior.chave_deduplicacao if anterior else f'alteracao:{entidade}:{item.id}:{uuid4().hex}'
    gravar(db, criador.id, chave, 'alteracao', 'Item alterado por outro usuário',
        f'{editor.nome} alterou {entidade} #{item.id}.', entidade, item.id)


def notificar_bloqueio(db, email, ip, chave):
    nome, _, dominio = email.partition('@')
    mascarado = f'{nome[:1]}***@{dominio}' if dominio else 'conta informada'
    for usuario in db.query(Usuario).filter_by(perfil='admin', ativo=1).all():
        gravar(db, usuario.id, chave, 'seguranca', 'Muitas falhas de login',
            f'Cinco falhas para {mascarado}. Origem: {ip}. Bloqueio de 10 minutos.')
