import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database import Base
from app.models.notificacao import TentativaLogin, Notificacao
from app.models.usuario import Usuario
from app.services.login_seguro import verificar_bloqueio, falhar, limpar


class BloqueioTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add(Usuario(nome='Admin', email='admin@local', senha_hash='hash', perfil='admin', ativo=1))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_cinco_falhas_persistem_e_notificam_uma_vez(self):
        for _ in range(5):
            falhar(self.db, 'teste@local', '127.0.0.1')
            self.db.commit()
        self.db.close()
        self.db = Session(self.engine)
        with self.assertRaises(HTTPException) as erro:
            verificar_bloqueio(self.db, 'teste@local', '127.0.0.1')
        self.assertEqual(erro.exception.status_code, 429)
        self.assertEqual(self.db.query(Notificacao).count(), 1)
        n = self.db.query(Notificacao).one()
        self.assertEqual(n.usuario_id, self.db.query(Usuario).one().id)
        self.assertNotIn('teste@local', n.mensagem)

    def test_expiracao_e_sucesso_limpam_falhas(self):
        falhar(self.db, 'teste@local', '127.0.0.1')
        self.db.query(TentativaLogin).one().inicio = datetime.now()-timedelta(minutes=11)
        falhar(self.db, 'teste@local', '127.0.0.1')
        self.assertEqual(self.db.query(TentativaLogin).one().tentativas, 1)
        limpar(self.db, 'teste@local', '127.0.0.1')
        self.assertEqual(self.db.query(TentativaLogin).count(), 0)
