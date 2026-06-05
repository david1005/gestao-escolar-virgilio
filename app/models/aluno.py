from sqlalchemy import Column, Integer, String, Date
from app.database import Base

class Curso(Base):
    __tablename__ = "cursos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    sigla = Column(String, nullable=False)

class Turma(Base):
    __tablename__ = "turmas"

    id = Column(Integer, primary_key=True, index=True)
    ano = Column(Integer, nullable=False)       # 1, 2 ou 3
    letra = Column(String, nullable=False)      # A, B, C, D
    curso_id = Column(Integer, nullable=False)

class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    matricula = Column(String, unique=True, nullable=False)
    data_nascimento = Column(Date, nullable=False)
    responsavel = Column(String, nullable=False)
    contato_responsavel = Column(String, nullable=False)
    turma_id = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="ativo")
