import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.tratamento import tratar, ArquivoInvalido

BASE = os.path.join(os.path.dirname(__file__), "..", "..")

class T(unittest.TestCase):
    def test_igual_ao_tratado_manual_no_bloco_vale(self):
        orig = open(f"{BASE}/IMPORTAÇÃO ORIGINAL DO GESTÃO CLICK.txt", "rb").read()
        r = tratar(orig)
        self.assertEqual(r.blocos_corrigidos, 5)
        self.assertEqual(r.linhas_separadas, 10)
        self.assertEqual(r.avisos, [])
        self.assertTrue(r.conteudo.endswith(b"\r\n") == orig.endswith(b"\r\n"))
        self.assertNotIn(b"|521|533|", r.conteudo)

    def test_bloco_x_intacto(self):
        t = b"|0000|1|\r\n|6000|X||||\r\n|6100|01/01/2026|1|2|10,00||H||||\r\n"
        self.assertEqual(tratar(t).conteudo, t)

    def test_rejeita(self):
        for ruim in [b"", b"\x00abc", b"ola mundo", b"|0000|1|\n=cmd|x\n", b"|0000|1|\n|6100|abc"]:
            with self.assertRaises(ArquivoInvalido):
                tratar(ruim)

if __name__ == "__main__":
    unittest.main()
