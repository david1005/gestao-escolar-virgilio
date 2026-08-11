from pydantic import BaseModel
from datetime import date, datetime

class RegistroBase(BaseModel):
    aluno_id: int
    data: date
    tipo: str
    aula: int
    aula_retorno_prevista: int | None = None
    aula_retorno_real: int | None = None
    tipo_saida: str | None = None
    status_retorno: str | None = None
    motivo: str
    tem_documento: bool = False
    observacoes: str = ""

class RegistroCreate(RegistroBase):
    pass

class Registro(RegistroBase):
    id: int
    criado_em: datetime | None = None
    class Config:
        from_attributes = True

class RegistroUpdate(BaseModel):
    tipo: str
    aula: int
    aula_retorno_prevista: int | None = None
    aula_retorno_real: int | None = None
    tipo_saida: str | None = None
    status_retorno: str | None = None
    motivo: str
    tem_documento: bool = False
    observacoes: str = ""
