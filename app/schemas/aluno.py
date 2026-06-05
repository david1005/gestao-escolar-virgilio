from pydantic import BaseModel
from datetime import date

class TurmaBase(BaseModel):
    ano: int
    letra: str
    curso_id: int

class TurmaCreate(TurmaBase):
    pass

class Turma(TurmaBase):
    id: int
    class Config:
        from_attributes = True

class CursoBase(BaseModel):
    nome: str
    sigla: str

class CursoCreate(CursoBase):
    pass

class Curso(CursoBase):
    id: int
    class Config:
        from_attributes = True

class AlunoBase(BaseModel):
    nome: str
    matricula: str
    data_nascimento: date
    responsavel: str
    contato_responsavel: str
    turma_id: int
    status: str = "ativo"

class AlunoCreate(AlunoBase):
    pass

class AlunoUpdate(AlunoBase):
    pass

class Aluno(AlunoBase):
    id: int
    class Config:
        from_attributes = True
