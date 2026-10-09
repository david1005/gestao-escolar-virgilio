import unittest
from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models.aluno import Aluno, Turma
from app.models.usuario import Usuario
from app.models.ocorrencia import Ocorrencia
from app.models.registro import Registro
from app.models.notificacao import Notificacao
from app.services.notificacoes import sincronizar, notificar_edicao, notificacoes_visiveis
from app.routes.notificacoes import ler
from app.routes.notificacoes import abrir, listar
from app.services.migracao_notificacoes import migrar_criadores
from app.models.auditoria import Auditoria
from fastapi import HTTPException


class NotificacoesTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.admin = Usuario(id=1, nome='Admin', email='a@local', senha_hash='hash', perfil='admin', ativo=1)
        self.diretor = Usuario(id=2, nome='Diretor', email='d@local', senha_hash='hash', perfil='diretor_turma', turma_id=10, ativo=1)
        self.outro = Usuario(id=3, nome='Outro', email='o@local', senha_hash='hash', perfil='diretor_turma', turma_id=20, ativo=1)
        self.aluno = Aluno(id=1, nome='Aluno', matricula='1', data_nascimento=date(2010,1,1), responsavel='Privado', contato_responsavel='Privado', turma_id=10)
        self.oc = Ocorrencia(id=1, aluno_id=1, data=date.today()-timedelta(days=16), tipo='Outro', descricao='Privado', medida='Registro', status='Aberta', registrado_por='Diretor', numero_ocorrencia=1, criado_por_id=2)
        self.db.add_all([self.admin, self.diretor, self.outro, self.aluno, self.oc])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_pendencia_deduplicada_resolvida_e_reativada(self):
        sincronizar(self.db, self.diretor)
        sincronizar(self.db, self.diretor)
        self.assertEqual(self.db.query(Notificacao).count(), 1)
        n = self.db.query(Notificacao).one()
        self.assertNotIn('Privado', n.mensagem)
        self.oc.status = 'Resolvida'
        sincronizar(self.db, self.diretor)
        self.assertFalse(n.ativa)
        self.oc.status = 'Aberta'
        sincronizar(self.db, self.diretor)
        self.assertTrue(n.ativa)
        self.assertIsNone(n.lida_em)

    def test_isolamento_e_revogacao_de_acesso(self):
        sincronizar(self.db, self.outro)
        self.assertEqual(self.db.query(Notificacao).count(), 0)
        sincronizar(self.db, self.diretor)
        self.diretor.turma_id = 20
        self.assertEqual(notificacoes_visiveis(self.db, self.diretor), [])

    def test_edicao_avisa_apenas_criador_e_nao_o_proprio_editor(self):
        notificar_edicao(self.db, 'ocorrencia', self.oc, self.diretor)
        self.assertEqual(self.db.query(Notificacao).count(), 0)
        notificar_edicao(self.db, 'ocorrencia', self.oc, self.admin)
        self.assertEqual(self.db.query(Notificacao).one().usuario_id, 2)

    def test_leitura_nao_permite_outro_destinatario(self):
        sincronizar(self.db, self.diretor)
        n = self.db.query(Notificacao).one()
        with self.assertRaises(HTTPException) as erro:
            ler(n.id, self.db, self.outro)
        self.assertEqual(erro.exception.status_code, 404)
        ler(n.id, self.db, self.diretor)
        self.assertIsNotNone(n.lida_em)

    def test_retorno_pendente_desativa_apos_confirmacao(self):
        r = Registro(aluno_id=1, data=date.today(), tipo='Saida', aula=1, motivo='Privado', tipo_saida='temporaria', status_retorno='Pendente')
        self.db.add(r)
        self.db.flush()
        sincronizar(self.db, self.diretor)
        n = self.db.query(Notificacao).filter_by(tipo='retorno_pendente').one()
        r.status_retorno = 'Retornou'
        sincronizar(self.db, self.diretor)
        self.assertFalse(n.ativa)

    def test_coordenador_respeita_curso_e_biblioteca_so_recebe_registros(self):
        self.db.add(Turma(id=10, ano=1, letra='A', curso_id=5))
        self.db.flush()
        self.diretor.perfil = 'coordenador'
        self.diretor.curso_ids = '6'
        sincronizar(self.db, self.diretor)
        self.assertEqual(self.db.query(Notificacao).count(), 0)
        self.diretor.curso_ids = '5'
        sincronizar(self.db, self.diretor)
        self.assertEqual(self.db.query(Notificacao).count(), 1)
        self.outro.perfil = 'biblioteca'
        sincronizar(self.db, self.outro)
        self.assertEqual(self.db.query(Notificacao).filter_by(usuario_id=3).count(), 0)

    def test_sem_criador_e_com_criador_inativo_nao_notifica(self):
        self.oc.criado_por_id = None
        notificar_edicao(self.db, 'ocorrencia', self.oc, self.admin)
        self.oc.criado_por_id = 2
        self.diretor.ativo = 0
        notificar_edicao(self.db, 'ocorrencia', self.oc, self.admin)
        self.assertEqual(self.db.query(Notificacao).count(), 0)

    def test_historico_paginado_e_destino_revalida_permissoes(self):
        sincronizar(self.db, self.diretor)
        dados = listar(page=1, page_size=1, leitura='todas', tipo='', db=self.db, usuario=self.diretor)
        self.assertEqual(dados['total'], 1)
        self.assertEqual(len(dados['items']), 1)
        n = self.db.query(Notificacao).one()
        self.assertEqual(abrir(n.id, self.db, self.diretor).headers['location'], '/ocorrencias?notificacao=1')
        self.diretor.turma_id = 20
        with self.assertRaises(HTTPException) as erro:
            abrir(n.id, self.db, self.diretor)
        self.assertEqual(erro.exception.status_code, 403)

    def test_migracao_recupera_criador_com_evidencia_de_auditoria(self):
        self.oc.criado_por_id = None
        self.db.add(Auditoria(usuario_id=2, acao='criou', entidade='ocorrencia', entidade_id=1))
        self.db.commit()
        migrar_criadores(self.engine)
        migrar_criadores(self.engine)
        self.db.expire_all()
        self.assertEqual(self.oc.criado_por_id, 2)

    def test_consulta_repetida_preserva_data_e_estado_de_leitura(self):
        sincronizar(self.db, self.diretor)
        n = self.db.query(Notificacao).one()
        instante = n.atualizada_em
        ler(n.id, self.db, self.diretor)
        sincronizar(self.db, self.diretor)
        self.assertEqual(n.atualizada_em, instante)
        self.assertIsNotNone(n.lida_em)
