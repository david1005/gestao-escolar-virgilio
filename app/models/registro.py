from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DateTime
from app.database import Base

class Registro(Base):
    __tablename__ = "registros"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False)
    data = Column(Date, nullable=False)
    tipo = Column(String, nullable=False)  # "Atraso" ou "Saída antecipada"
    aula = Column(Integer, nullable=False)  # 1 a 9
    aula_retorno_prevista = Column(Integer, nullable=True)
    aula_retorno_real = Column(Integer, nullable=True)
    tipo_saida = Column(String, nullable=True)
    status_retorno = Column(String, nullable=True)
    motivo = Column(String, nullable=False)
    tem_documento = Column(Boolean, default=False)
    observacoes = Column(String, nullable=True)
    ano_letivo_id = Column(Integer, nullable=True)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
