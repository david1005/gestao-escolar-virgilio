import unittest
from types import SimpleNamespace

from app.auth import usuario_pode_acessar_aluno


class FakeQuery:
    def __init__(self, resultado):
        self.resultado = resultado

    def filter(self, *args):
        return self

    def first(self):
        return self.resultado


class FakeDB:
    def __init__(self, turma=None):
        self.turma = turma

    def query(self, model):
        return FakeQuery(self.turma)


class AutorizacaoAlunoTests(unittest.TestCase):
    def test_diretor_acessa_apenas_a_propria_turma(self):
        usuario = SimpleNamespace(perfil="diretor_turma", turma_id=10, curso_id=None, curso_ids=None)

        self.assertTrue(usuario_pode_acessar_aluno(FakeDB(), usuario, SimpleNamespace(turma_id=10)))
        self.assertFalse(usuario_pode_acessar_aluno(FakeDB(), usuario, SimpleNamespace(turma_id=11)))

    def test_coordenador_acessa_turma_de_curso_vinculado(self):
        usuario = SimpleNamespace(perfil="coordenador", turma_id=None, curso_id=None, curso_ids="2,3")
        aluno = SimpleNamespace(turma_id=20)

        self.assertTrue(usuario_pode_acessar_aluno(FakeDB(SimpleNamespace(id=20, curso_id=2)), usuario, aluno))
        self.assertFalse(usuario_pode_acessar_aluno(FakeDB(), usuario, aluno))

    def test_demais_perfis_mantem_acesso_definido_pelo_modulo(self):
        usuario = SimpleNamespace(perfil="ppdt", turma_id=None, curso_id=None, curso_ids=None)

        self.assertTrue(usuario_pode_acessar_aluno(FakeDB(), usuario, SimpleNamespace(turma_id=99)))


if __name__ == "__main__":
    unittest.main()
