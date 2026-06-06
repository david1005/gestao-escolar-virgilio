from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text

from app.database import Base


class AnoLetivo(Base):
    __tablename__ = "anos_letivos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    ano = Column(Integer, nullable=False)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=False)
    ativo = Column(Boolean, default=False)
    encerrado = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)


class ConfiguracaoSistema(Base):
    __tablename__ = "configuracoes_sistema"

    id = Column(Integer, primary_key=True, index=True)
    chave = Column(String, unique=True, nullable=False)
    valor = Column(Text, nullable=True)
    atualizado_em = Column(DateTime, default=datetime.now, nullable=False)


class PermissaoPerfil(Base):
    __tablename__ = "permissoes_perfil"

    id = Column(Integer, primary_key=True, index=True)
    perfil = Column(String, unique=True, nullable=False)
    permissoes = Column(Text, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.now, nullable=False)


class Anexo(Base):
    __tablename__ = "anexos"

    id = Column(Integer, primary_key=True, index=True)
    entidade = Column(String, nullable=False)
    entidade_id = Column(Integer, nullable=False)
    nome_original = Column(String, nullable=False)
    nome_arquivo = Column(String, nullable=False)
    caminho = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    tamanho = Column(Integer, nullable=True)
    enviado_por_id = Column(Integer, nullable=True)
    enviado_por_nome = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)


class MatriculaHistorico(Base):
    __tablename__ = "matriculas_historico"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, nullable=False)
    turma_id = Column(Integer, nullable=False)
    ano_letivo_id = Column(Integer, nullable=False)
    status = Column(String, default="ativo", nullable=False)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=True)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
