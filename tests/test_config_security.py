import os
import unittest
from unittest.mock import patch

from app.config import obter_admin_inicial, obter_secret_key


class ConfigSecurityTests(unittest.TestCase):
    def test_producao_rejeita_secret_key_ausente_ou_padrao(self):
        for secret_key in ("", "troque_esta_chave_em_producao", "curta"):
            with self.subTest(secret_key=secret_key):
                with patch.dict(
                    os.environ,
                    {"APP_ENV": "production", "SECRET_KEY": secret_key},
                    clear=False,
                ):
                    with self.assertRaises(RuntimeError):
                        obter_secret_key()

    def test_producao_aceita_secret_key_forte(self):
        secret_key = "a" * 48
        with patch.dict(
            os.environ,
            {"APP_ENV": "production", "SECRET_KEY": secret_key},
            clear=False,
        ):
            self.assertEqual(obter_secret_key(), secret_key)

    def test_desenvolvimento_gera_chave_temporaria(self):
        with patch.dict(os.environ, {"APP_ENV": "development", "SECRET_KEY": ""}, clear=False):
            self.assertGreaterEqual(len(obter_secret_key()), 32)

    def test_admin_inicial_exige_configuracao_explicita(self):
        with patch.dict(
            os.environ,
            {"ADMIN_EMAIL": "", "ADMIN_PASSWORD": ""},
            clear=False,
        ):
            with self.assertRaises(RuntimeError):
                obter_admin_inicial()

    def test_admin_inicial_rejeita_credenciais_de_exemplo(self):
        with patch.dict(
            os.environ,
            {"ADMIN_EMAIL": "admin@teste.com", "ADMIN_PASSWORD": "Admin1234"},
            clear=False,
        ):
            with self.assertRaises(RuntimeError):
                obter_admin_inicial()

    def test_admin_inicial_aceita_credenciais_fortes(self):
        with patch.dict(
            os.environ,
            {
                "ADMIN_EMAIL": "responsavel@escola.local",
                "ADMIN_PASSWORD": "SenhaForte2026",
                "ADMIN_NAME": "Responsavel",
            },
            clear=False,
        ):
            self.assertEqual(
                obter_admin_inicial(),
                ("responsavel@escola.local", "SenhaForte2026", "Responsavel"),
            )


if __name__ == "__main__":
    unittest.main()
