from pydantic import BaseModel
from datetime import date

class RegistroBase(BaseModel):
    aluno_id: int
    data: date
    tipo: str
    aula: int
    motivo: str
    tem_documento: bool = False
    observacoes: str = ""

class RegistroCreate(RegistroBase):
    pass

class Registro(RegistroBase):
    id: int
    class Config:
        from_attributes = True

class RegistroUpdate(BaseModel):
    tipo: str
    aula: int
    motivo: str
    tem_documento: bool = False
    observacoes: str = ""