from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DateTime
from datetime import datetime
from app.database import Base

class Ocorrencia(Base):
    __tablename__ = "ocorrencias"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False)
    data = Column(Date, nullable=False)
    tipo = Column(String, nullable=False)
    descricao = Column(String, nullable=False)
    medida = Column(String, nullable=False)
    gravidade = Column(String, nullable=False, default="Leve")
    status = Column(String, nullable=False, default="Aberta")
    acoes_tomadas = Column(String, nullable=True)
    registrado_por = Column(String, nullable=False)
    responsavel_notificado = Column(Boolean, default=False)
    numero_ocorrencia = Column(Integer, nullable=False)
    editado_por = Column(String, nullable=True)
    editado_em = Column(DateTime, nullable=True)
    ano_letivo_id = Column(Integer, nullable=True)
