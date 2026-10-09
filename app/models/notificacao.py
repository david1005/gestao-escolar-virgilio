from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint
from app.database import Base


class Notificacao(Base):
    __tablename__ = 'notificacoes'
    __table_args__ = (UniqueConstraint('usuario_id', 'chave_deduplicacao'),)

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    tipo = Column(String, nullable=False)
    titulo = Column(String, nullable=False)
    mensagem = Column(String, nullable=False)
    entidade = Column(String, nullable=True)
    entidade_id = Column(Integer, nullable=True)
    chave_deduplicacao = Column(String, nullable=False)
    ativa = Column(Boolean, nullable=False, default=True)
    lida_em = Column(DateTime, nullable=True)
    criada_em = Column(DateTime, nullable=False, default=datetime.now)
    atualizada_em = Column(DateTime, nullable=False, default=datetime.now)


class PreferenciaNotificacao(Base):
    __tablename__ = 'preferencias_notificacao'

    usuario_id = Column(Integer, primary_key=True)
    ocorrencia_antiga = Column(Boolean, nullable=False, default=True)
    retorno_pendente = Column(Boolean, nullable=False, default=True)
    alteracao = Column(Boolean, nullable=False, default=True)


class TentativaLogin(Base):
    __tablename__ = 'tentativas_login'

    chave = Column(String, primary_key=True)
    tentativas = Column(Integer, nullable=False, default=0)
    inicio = Column(DateTime, nullable=False, default=datetime.now)
    bloqueado_ate = Column(DateTime, nullable=True)
