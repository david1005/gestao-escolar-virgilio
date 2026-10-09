import unittest
from pathlib import Path
import re

from app.security import SECURITY_HEADERS


RAIZ = Path(__file__).resolve().parents[1]


class AssetsLocaisTests(unittest.TestCase):
    def test_templates_nao_carregam_scripts_ou_estilos_externos(self):
        templates_com_assets_externos = []

        for template in (RAIZ / "templates").glob("*.html"):
            conteudo = template.read_text(encoding="utf-8")
            if re.search(r"<(?:script|link)[^>]+(?:src|href)=[\"']https?://", conteudo):
                templates_com_assets_externos.append(template.name)

        self.assertEqual(templates_com_assets_externos, [])

    def test_csp_nao_autoriza_jsdelivr(self):
        self.assertNotIn("cdn.jsdelivr.net", SECURITY_HEADERS["Content-Security-Policy"])

    def test_bibliotecas_de_frontend_estao_hospedadas_localmente(self):
        arquivos = [
            "static/vendor/bootstrap/css/bootstrap.min.css",
            "static/vendor/bootstrap/js/bootstrap.bundle.min.js",
            "static/vendor/bootstrap-icons/font/bootstrap-icons.css",
            "static/vendor/bootstrap-icons/font/fonts/bootstrap-icons.woff",
            "static/vendor/bootstrap-icons/font/fonts/bootstrap-icons.woff2",
            "static/vendor/chart.js/chart.umd.min.js",
        ]

        for arquivo in arquivos:
            with self.subTest(arquivo=arquivo):
                caminho = RAIZ / arquivo
                self.assertTrue(caminho.is_file())
                self.assertGreater(caminho.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
