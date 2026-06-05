from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class OcorrenciaBase(BaseModel):
    aluno_id: int
    data: date
    tipo: str
    descricao: str
    medida: str
    gravidade: str = "Leve"
    status: str = "Aberta"
    acoes_tomadas: Optional[str] = None
    registrado_por: str
    responsavel_notificado: bool = False
    numero_ocorrencia: int

class OcorrenciaCreate(OcorrenciaBase):
    pass

class OcorrenciaUpdate(BaseModel):
    tipo: str
    descricao: str
    medida: str
    gravidade: str
    status: str
    acoes_tomadas: Optional[str] = None
    responsavel_notificado: bool
    editado_por: str

class Ocorrencia(OcorrenciaBase):
    id: int
    editado_por: Optional[str] = None
    editado_em: Optional[datetime] = None
    class Config:
        from_attributes = True
