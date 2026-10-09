import unittest

from app.routes.sistema import texto_html_seguro


class EscapeHtmlBackendTests(unittest.TestCase):
    def test_escapa_html_e_atributos(self):
        self.assertEqual(
            texto_html_seguro('<img src=x onerror="alert(1)">'),
            '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;',
        )

    def test_valor_nulo_vira_texto_vazio(self):
        self.assertEqual(texto_html_seguro(None), '')


if __name__ == "__main__":
    unittest.main()
