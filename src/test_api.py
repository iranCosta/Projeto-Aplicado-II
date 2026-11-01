"""Testes da API (usa um banco temporário). Rode da raiz: python -m unittest src.test_api -v"""
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

_TMP = tempfile.TemporaryDirectory()
os.environ["DATABASE_PATH"] = str(Path(_TMP.name) / "teste.db")  # antes de importar src.config
os.environ["MODELO_PATH"] = str(Path(_TMP.name) / "sem_modelo.joblib")  # por padrão, API sem modelo

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from services import modelo  # noqa: E402
from src import database, ia  # noqa: E402
from src.main import app  # noqa: E402


def payload(**kw):
    base = {"sensor_id": 1, "timestamp": "2026-10-22T20:00:00Z", "rms": 1.53, "assimetria": 0.18,
            "curtose": 3.0, "frequencia_pico": 30.0, "rotacao_rpm": 1780}
    return {**base, **kw}


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = TestClient(app)
        cls.c = cls.ctx.__enter__()  # executa o lifespan (init_db)

    @classmethod
    def tearDownClass(cls):
        cls.ctx.__exit__(None, None, None)

    def post_invalido(self, corpo, campo, trecho):
        r = self.c.post("/api/dados", json=corpo)
        self.assertEqual(r.status_code, 422, r.text)
        erros = r.json()["detail"]
        self.assertTrue(any(e["campo"] == campo and trecho in e["mensagem"] for e in erros), erros)

    # ---------------------------------------------------------------- sucesso
    def test_health(self):
        self.assertEqual(self.c.get("/health").status_code, 200)

    def test_post_normal(self):
        r = self.c.post("/api/dados", json=payload())
        self.assertEqual(r.status_code, 201, r.text)
        corpo = r.json()
        self.assertEqual((corpo["status_alerta"], corpo["cor"]), ("NORMAL", "verde"))
        self.assertIsInstance(corpo["id"], int)
        self.assertIsNone(corpo["modelo"])  # sem modelo treinado, a API segue só com a regra

    def test_post_critico_aparece_no_get(self):
        r = self.c.post("/api/dados", json=payload(sensor_id=3, rms=8.2, curtose=9.0))
        self.assertEqual(r.json()["status_alerta"], "CRITICO")
        self.assertEqual(len(r.json()["motivos"]), 2)
        lista = self.c.get("/api/diagnosticos", params={"status": "CRITICO"}).json()["diagnosticos"]
        self.assertIn(r.json()["id"], [d["id"] for d in lista])
        self.assertTrue(all(d["status_alerta"] == "CRITICO" and d["cor"] == "vermelho" for d in lista))

    def test_timestamp_com_fuso_vira_utc(self):
        r = self.c.post("/api/dados", json=payload(sensor_id=2, timestamp="2026-10-22T17:00:00-03:00"))
        self.assertEqual(r.json()["timestamp"], "2026-10-22T20:00:00Z")

    def test_inteiro_aceito_em_campo_decimal(self):
        self.assertEqual(self.c.post("/api/dados", json=payload(rms=2)).status_code, 201)

    def test_status_por_sensor(self):
        self.c.post("/api/dados", json=payload(sensor_id=5, rms=5.0))
        sensores = {s["sensor_id"]: s for s in self.c.get("/api/status").json()["sensores"]}
        self.assertEqual(len(sensores), 6)
        self.assertEqual((sensores[5]["status_alerta"], sensores[5]["cor"]), ("ATENCAO", "amarelo"))
        self.assertIsNone(sensores[6]["leitura_id"])  # sensor 6 não recebe leituras nestes testes

    def test_filtro_por_sensor(self):
        self.c.post("/api/dados", json=payload(sensor_id=4))
        lista = self.c.get("/api/diagnosticos", params={"sensor_id": 4}).json()["diagnosticos"]
        self.assertTrue(lista and all(d["sensor_id"] == 4 for d in lista))

    # ------------------------------------------------------ dados inválidos
    def test_status_alerta_nao_pode_ser_enviado(self):
        self.post_invalido(payload(status_alerta="NORMAL"), "status_alerta", "calculado pela API")

    def test_campo_extra(self):
        self.post_invalido(payload(temperatura=80), "temperatura", "não permitido")

    def test_campo_ausente(self):
        corpo = payload()
        del corpo["curtose"]
        self.post_invalido(corpo, "curtose", "obrigatório")

    def test_limites(self):
        casos = [
            ("rms", -0.1, "maior ou igual a 0"),
            ("rms", 150, "menor ou igual a 100"),
            ("curtose", 0.5, "maior ou igual a 1"),
            ("frequencia_pico", 2000, "menor ou igual a 1024"),
            ("rotacao_rpm", 0, "maior que 0"),
            ("sensor_id", 0, "maior que 0"),
        ]
        for campo, valor, trecho in casos:
            with self.subTest(campo=campo, valor=valor):
                self.post_invalido(payload(**{campo: valor}), campo, trecho)

    def test_tipos_estritos(self):
        self.post_invalido(payload(rms="1.5"), "rms", "número")
        self.post_invalido(payload(rms=True), "rms", "número")
        self.post_invalido(payload(sensor_id="1"), "sensor_id", "inteiro")
        self.post_invalido(payload(sensor_id=1.5), "sensor_id", "inteiro")

    def test_nan_e_infinito(self):
        for valor in ("NaN", "Infinity"):
            with self.subTest(valor=valor):
                corpo = '{"sensor_id": 1, "timestamp": "2026-10-22T20:00:00Z", "rms": %s, "assimetria": 0, ' \
                        '"curtose": 3, "frequencia_pico": 30, "rotacao_rpm": 1780}' % valor
                r = self.c.post("/api/dados", content=corpo, headers={"Content-Type": "application/json"})
                self.assertEqual(r.status_code, 422, r.text)
                self.assertIn("finito", r.json()["detail"][0]["mensagem"])

    def test_timestamps_invalidos(self):
        futuro = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        self.post_invalido(payload(timestamp="ontem"), "timestamp", "ISO 8601")
        self.post_invalido(payload(timestamp="2026-10-22T20:00:00"), "timestamp", "fuso")
        self.post_invalido(payload(timestamp=futuro), "timestamp", "futuro")

    def test_sensor_inexistente(self):
        self.post_invalido(payload(sensor_id=99), None, "sensor inexistente")

    def test_corpo_nao_objeto(self):
        self.assertEqual(self.c.post("/api/dados", json=[1, 2]).status_code, 422)

    def test_filtro_status_invalido(self):
        self.assertEqual(self.c.get("/api/diagnosticos", params={"status": "VERDE"}).status_code, 422)

    # ------------------------------------------------------ falha operacional
    def test_banco_indisponivel(self):
        with patch.object(database, "DATABASE_PATH", Path(_TMP.name) / "nao_existe.db"):
            r = self.c.post("/api/dados", json=payload())
        self.assertEqual(r.status_code, 503)
        self.assertIn("indisponível", r.json()["detail"][0]["mensagem"])



def modelo_sintetico():
    """Isolation Forest treinado com leituras normais aleatórias dos 6 sensores."""
    rng = np.random.default_rng(0)
    n = 300
    df = pd.DataFrame({"sensor_id": np.repeat(np.arange(1, 7), n), "rms": rng.normal(1.5, 0.1, 6 * n),
                       "assimetria": rng.normal(0, 0.1, 6 * n), "curtose": rng.normal(3, 0.1, 6 * n),
                       "frequencia_pico": rng.normal(30, 0.5, 6 * n)})
    return {"modelos": modelo.treinar(df), "treinado_em": "2026-11-01T00:00:00+00:00"}


class TestModeloNaAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = TestClient(app)
        cls.c = cls.ctx.__enter__()
        cls.patch = patch.object(ia, "_pacote", modelo_sintetico())
        cls.patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        cls.ctx.__exit__(None, None, None)

    def test_health_informa_modelo(self):
        self.assertTrue(self.c.get("/health").json()["modelo"]["carregado"])

    def test_leitura_tipica_nao_e_anomala(self):
        r = self.c.post("/api/dados", json=payload(sensor_id=6, rms=1.5, curtose=3.0, assimetria=0.0))
        self.assertFalse(r.json()["modelo"]["anomalia"])

    def test_modelo_ve_o_que_a_regra_nao_ve(self):
        # pico em 500 Hz com RMS e curtose normais: a regra diz NORMAL, o modelo estranha
        r = self.c.post("/api/dados", json=payload(sensor_id=6, frequencia_pico=500.0)).json()
        self.assertEqual(r["status_alerta"], "NORMAL")
        self.assertTrue(r["modelo"]["anomalia"])
        self.assertGreater(r["modelo"]["score"], 0.5)

    def test_gets_trazem_modelo(self):
        self.c.post("/api/dados", json=payload(sensor_id=6))
        d = self.c.get("/api/diagnosticos", params={"sensor_id": 6}).json()["diagnosticos"][0]
        self.assertIn("anomalia", d["modelo"])
        sensores = {s["sensor_id"]: s for s in self.c.get("/api/status").json()["sensores"]}
        self.assertIn("score", sensores[6]["modelo"])


if __name__ == "__main__":
    unittest.main()
