from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from app.database import Base

class Registro(Base):
    __tablename__ = "registros"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False)
    data = Column(Date, nullable=False)
    tipo = Column(String, nullable=False)  # "Atraso" ou "Saída antecipada"
    aula = Column(Integer, nullable=False)  # 1 a 9
    motivo = Column(String, nullable=False)
    tem_documento = Column(Boolean, default=False)
    observacoes = Column(String, nullable=True)