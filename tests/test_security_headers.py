import unittest

from starlette.responses import Response

from app.security import aplicar_cabecalhos_seguranca, configuracao_documentacao


class SecurityHeadersTests(unittest.TestCase):
    def test_cabecalhos_basicos_sao_aplicados(self):
        response = Response()

        aplicar_cabecalhos_seguranca(response, producao=False, caminho="/api/alunos")

        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertIn("frame-ancestors 'none'", response.headers["content-security-policy"])
        self.assertNotIn("strict-transport-security", response.headers)

    def test_hsts_e_documentacao_sao_protegidos_em_producao(self):
        response = Response()

        aplicar_cabecalhos_seguranca(response, producao=True, caminho="/")

        self.assertEqual(response.headers["strict-transport-security"], "max-age=31536000")
        self.assertEqual(
            configuracao_documentacao(producao=True),
            {"docs_url": None, "redoc_url": None, "openapi_url": None},
        )

    def test_arquivos_estaticos_podem_ser_cacheados(self):
        response = Response()

        aplicar_cabecalhos_seguranca(response, producao=False, caminho="/static/css/style.css")

        self.assertNotIn("cache-control", response.headers)


if __name__ == "__main__":
    unittest.main()
