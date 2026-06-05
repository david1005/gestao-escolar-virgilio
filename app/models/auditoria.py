from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base


class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=True)
    usuario_nome = Column(String, nullable=True)
    acao = Column(String, nullable=False)
    entidade = Column(String, nullable=False)
    entidade_id = Column(Integer, nullable=True)
    detalhes = Column(String, nullable=True)
    ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
