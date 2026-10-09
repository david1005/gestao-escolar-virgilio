import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from app.models.aluno import Aluno
from app.models.ocorrencia import Ocorrencia
from app.models.registro import Registro
from app.models.sistema import PermissaoPerfil
from app.routes.sistema import exigir_acesso_anexo


class FakeQuery:
    def __init__(self, resultado):
        self.resultado = resultado

    def filter(self, *args):
        return self

    def first(self):
        return self.resultado


class FakeDB:
    def __init__(self, resultados=None):
        self.resultados = resultados or {}

    def query(self, model):
        return FakeQuery(self.resultados.get(model))


def usuario(perfil, turma_id=None):
    return SimpleNamespace(
        perfil=perfil,
        turma_id=turma_id,
        curso_id=None,
        curso_ids=None,
    )


class AutorizacaoAnexosTests(unittest.TestCase):
    def test_listagem_global_exige_administrador(self):
        with self.assertRaises(HTTPException) as contexto:
            exigir_acesso_anexo(FakeDB(), usuario("ppdt"))

        self.assertEqual(contexto.exception.status_code, 403)
        exigir_acesso_anexo(FakeDB(), usuario("admin"))

    def test_diretor_acessa_anexo_de_aluno_da_propria_turma(self):
        db = FakeDB({
            PermissaoPerfil: None,
            Aluno: SimpleNamespace(id=1, turma_id=10),
        })

        exigir_acesso_anexo(db, usuario("diretor_turma", turma_id=10), "aluno", 1)

    def test_diretor_nao_acessa_anexo_de_outra_turma(self):
        db = FakeDB({
            PermissaoPerfil: None,
            Aluno: SimpleNamespace(id=2, turma_id=11),
        })

        with self.assertRaises(HTTPException) as contexto:
            exigir_acesso_anexo(db, usuario("diretor_turma", turma_id=10), "aluno", 2)

        self.assertEqual(contexto.exception.status_code, 403)

    def test_registro_e_ocorrencia_sao_resolvidos_ate_o_aluno(self):
        db_registro = FakeDB({
            PermissaoPerfil: None,
            Registro: SimpleNamespace(id=3, aluno_id=7),
            Aluno: SimpleNamespace(id=7, turma_id=10),
        })
        db_ocorrencia = FakeDB({
            PermissaoPerfil: None,
            Ocorrencia: SimpleNamespace(id=4, aluno_id=8),
            Aluno: SimpleNamespace(id=8, turma_id=11),
        })
        diretor = usuario("diretor_turma", turma_id=10)

        exigir_acesso_anexo(db_registro, diretor, "registro", 3)
        with self.assertRaises(HTTPException) as contexto:
            exigir_acesso_anexo(db_ocorrencia, diretor, "ocorrencia", 4)

        self.assertEqual(contexto.exception.status_code, 403)

    def test_entidade_inexistente_e_rejeitada(self):
        db = FakeDB({PermissaoPerfil: None, Registro: None})

        with self.assertRaises(HTTPException) as contexto:
            exigir_acesso_anexo(db, usuario("ppdt"), "registro", 999)

        self.assertEqual(contexto.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
