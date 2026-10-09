import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from app.routes.ocorrencia import criar_ocorrencia, editar_ocorrencia
from app.schemas.ocorrencia import OcorrenciaCreate, OcorrenciaUpdate


class FakeCreateDB:
    def __init__(self):
        self.adicionados = []

    def add(self, item):
        self.adicionados.append(item)

    def flush(self):
        self.adicionados[0].id = 1

    def commit(self):
        pass

    def refresh(self, item):
        pass


class FakeQuery:
    def __init__(self, resultado):
        self.resultado = resultado

    def filter(self, *args):
        return self

    def first(self):
        return self.resultado


class FakeUpdateDB(FakeCreateDB):
    def __init__(self, ocorrencia):
        super().__init__()
        self.ocorrencia = ocorrencia

    def query(self, model):
        return FakeQuery(self.ocorrencia)


class IdentidadeAutorOcorrenciaTests(unittest.TestCase):
    def setUp(self):
        self.usuario = SimpleNamespace(id=7, nome="Usuario Autenticado", perfil="admin")

    @patch("app.routes.ocorrencia.registrar_auditoria")
    @patch("app.routes.ocorrencia.obter_ano_letivo_ativo")
    @patch("app.routes.ocorrencia.exigir_acesso_aluno")
    @patch("app.routes.ocorrencia.exigir_ocorrencias")
    def test_criacao_usa_usuario_autenticado_como_autor(
        self,
        exigir_ocorrencias,
        exigir_acesso_aluno,
        obter_ano_letivo_ativo,
        registrar_auditoria,
    ):
        db = FakeCreateDB()
        obter_ano_letivo_ativo.return_value = SimpleNamespace(id=2026)
        dados = OcorrenciaCreate(
            aluno_id=10,
            data=date(2026, 10, 7),
            tipo="Indisciplina",
            descricao="Descricao",
            medida="So registro",
            gravidade="Leve",
            status="Aberta",
            registrado_por="Nome Falsificado",
            responsavel_notificado=False,
            numero_ocorrencia=1,
        )

        resultado = criar_ocorrencia(dados, db, self.usuario)

        self.assertEqual(resultado.registrado_por, "Usuario Autenticado")

    @patch("app.routes.ocorrencia.registrar_auditoria")
    @patch("app.routes.ocorrencia.exigir_acesso_aluno")
    @patch("app.routes.ocorrencia.exigir_ocorrencias")
    def test_edicao_usa_usuario_autenticado_como_editor(
        self,
        exigir_ocorrencias,
        exigir_acesso_aluno,
        registrar_auditoria,
    ):
        ocorrencia = SimpleNamespace(
            id=3,
            aluno_id=10,
            tipo="Indisciplina",
            descricao="Descricao antiga",
            medida="So registro",
            gravidade="Leve",
            status="Aberta",
            acoes_tomadas=None,
            responsavel_notificado=False,
            editado_por=None,
            editado_em=None,
        )
        db = FakeUpdateDB(ocorrencia)
        dados = OcorrenciaUpdate(
            tipo="Outro",
            descricao="Descricao atualizada",
            medida="Advertencia",
            gravidade="Media",
            status="Em acompanhamento",
            acoes_tomadas="Conversa",
            responsavel_notificado=True,
            editado_por="Nome Falsificado",
        )

        resultado = editar_ocorrencia(3, dados, db, self.usuario)

        self.assertEqual(resultado.editado_por, "Usuario Autenticado")


if __name__ == "__main__":
    unittest.main()
