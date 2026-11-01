"""Testes do Isolation Forest. Rode da raiz: python -m unittest services.test_modelo -v"""
import sys
import tempfile
import time
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "mock"))

import simulator  # noqa: E402

from services import modelo  # noqa: E402


class TestModelo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        pasta = Path(cls.tmp.name)
        simulator.main(["--n", "3000", "--saida", "sqlite", "--seed", "7", "--pasta", str(pasta)])
        cls.df = modelo.ler_banco(pasta / "vibracao.db")
        cls.treino, cls.teste = modelo.separar_treino_teste(cls.df)
        cls.modelos = modelo.treinar(cls.treino)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_sem_vazamento_do_gabarito(self):
        self.assertNotIn("anomalia_real", modelo.FEATURES)
        self.assertNotIn("tipo_anomalia", modelo.FEATURES)
        self.assertNotIn("status_alerta", modelo.FEATURES)

    def test_divisao_temporal_por_sensor(self):
        self.assertEqual(len(self.treino) + len(self.teste), len(self.df))
        for sid, g in self.teste.groupby("sensor_id"):
            ultimo_treino = self.treino[self.treino.sensor_id == sid]["timestamp"].max()
            self.assertGreater(g["timestamp"].min(), ultimo_treino)  # teste sempre depois do treino

    def test_um_modelo_por_sensor(self):
        self.assertEqual(sorted(self.modelos), sorted(self.df["sensor_id"].unique()))

    def test_modelo_detecta_mais_que_a_regra_no_teste(self):
        r = modelo.avaliar(self.modelos, self.teste)
        self.assertGreater(r["anomalias_reais"], 0)
        self.assertGreater(r["isolation_forest"]["recall"], r["regra_de_limiar"]["recall"])
        self.assertGreaterEqual(r["isolation_forest"]["precisao"], 0.5)

    def test_sensor_sem_modelo(self):
        p = modelo.pontuar({}, self.teste.head(3))
        self.assertTrue(p["anomalia_if"].isna().all())

    def test_salvar_e_carregar(self):
        caminho = Path(self.tmp.name) / "m.joblib"
        modelo.salvar(self.modelos, caminho, {"treinado_em": "x"})
        pacote = modelo.carregar(caminho)
        self.assertEqual(pacote["features"], modelo.FEATURES)
        a = modelo.pontuar(self.modelos, self.teste)["score_if"]
        b = modelo.pontuar(pacote["modelos"], self.teste)["score_if"]
        self.assertTrue((a == b).all())  # mesmo resultado sem retreinar
        self.assertIsNone(modelo.carregar(Path(self.tmp.name) / "nao_existe.joblib"))

    def test_inferencia_rapida(self):
        # RNF01: inferência sobre ~5 mil leituras em menos de 3 s
        grande = self.df.sample(5000, replace=True, random_state=0)
        inicio = time.perf_counter()
        modelo.pontuar(self.modelos, grande)
        self.assertLess(time.perf_counter() - inicio, 3.0)


if __name__ == "__main__":
    unittest.main()
