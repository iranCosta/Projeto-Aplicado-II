"""Testes da leitura/validação. Rode: python -m unittest test_leitor -v"""
import tempfile
import unittest
from pathlib import Path

import pandas as pd

import leitor_dados as ld
import simulator


class TestLeitor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pasta = Path(cls.tmp.name)
        simulator.main(["--n", "1200", "--saida", "sqlite", "csv", "json", "--seed", "3", "--pasta", str(cls.pasta)])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_tres_fontes_equivalentes(self):
        a = ld.carregar("sqlite", self.pasta / "vibracao.db")
        b = ld.carregar("csv", self.pasta / "leituras_brutas.csv")
        c = ld.carregar("json", self.pasta / "leituras_brutas.json")
        self.assertEqual(len(a), len(b)); self.assertEqual(len(b), len(c))
        self.assertAlmostEqual(a["rms"].sum(), b["rms"].sum(), places=2)
        self.assertAlmostEqual(b["rms"].sum(), c["rms"].sum(), places=2)

    def test_dados_do_mock_sao_validos(self):
        ok, rej = ld.validar(ld.carregar("csv", self.pasta / "leituras_brutas.csv"))
        self.assertEqual(len(rej), 0); self.assertEqual(len(ok), 1200)

    def test_rejeita_entradas_ruins(self):
        df = ld.carregar("csv", self.pasta / "leituras_brutas.csv").head(10).copy()
        df.loc[0, "rms"] = -5                      # negativo
        df.loc[1, "curtose"] = None                # nulo
        df.loc[2, "status_alerta"] = "ALARME"      # status inválido
        df.loc[3, "timestamp"] = "ontem de manhã"  # timestamp inválido
        df = pd.concat([df, df.iloc[[5]]])         # duplicada
        ok, rej = ld.validar(df)
        self.assertEqual(len(rej), 5); self.assertEqual(len(ok), 6)
        self.assertEqual(set(rej["motivo"]), {"rms negativo", "valor nulo/não numérico", "status desconhecido",
                                              "timestamp inválido", "duplicada (sensor+timestamp)"})

    def test_coluna_faltando_levanta_erro(self):
        with self.assertRaises(ValueError):
            ld.validar(pd.DataFrame({"sensor_id": [1]}))

    def test_isolation_forest_supera_ou_iguala_regra_em_recall(self):
        ok, _ = ld.validar(ld.carregar("sqlite", self.pasta / "vibracao.db"))
        met = ld.avaliar_contra_gabarito(ld.detectar_isolation_forest(ok))
        self.assertGreaterEqual(met["isolation_forest"]["recall"], met["regra_de_limiar"]["recall"])


if __name__ == "__main__":
    unittest.main()
