from sqlalchemy import Column, DateTime, Integer, String
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    perfil = Column(String, nullable=False)  # admin, ppdt, biblioteca, coordenador, diretor_turma
    turma_id = Column(Integer, nullable=True)   # para diretor de turma
    curso_id = Column(Integer, nullable=True)   # para coordenador de curso
    curso_ids = Column(String, nullable=True)   # varios cursos para coordenador, separados por virgula
    ultimo_login = Column(DateTime, nullable=True)
    ativo = Column(Integer, default=1)
