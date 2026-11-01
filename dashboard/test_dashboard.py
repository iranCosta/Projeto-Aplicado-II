"""Testes do painel com a API simulada. Rode da raiz: python -m unittest dashboard.test_dashboard -v"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA))

import cliente  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402


def sensor(sid, tag, status, rms=1.5, curtose=3.0, leitura_id=1):
    motivos = {"NORMAL": ["indicadores dentro dos limites"], "ATENCAO": ["RMS 5.00 >= 4.5 (atenção)"],
               "CRITICO": ["RMS 8.20 >= 7.1 (crítico)"], None: ["sem leituras"]}[status]
    return {"sensor_id": sid, "tag": tag, "ativo": f"Ativo {tag}", "posicao": "LADO_ACOPLADO",
            "leitura_id": leitura_id, "timestamp": "2026-10-22T20:00:00Z" if leitura_id else None,
            "rms": rms if leitura_id else None, "curtose": curtose if leitura_id else None,
            "status_alerta": status, "cor": None, "motivos": motivos}


SENSORES = [
    sensor(1, "MOT-101", "NORMAL"),
    sensor(2, "MOT-102", "CRITICO", rms=8.2),
    sensor(3, "CMP-201", "ATENCAO", rms=5.0),
    sensor(4, "CMP-202", None, leitura_id=None),
]


def historico(sensor_id, limite=200):
    s = next(x for x in SENSORES if x["sensor_id"] == sensor_id)
    if s["leitura_id"] is None:
        return []
    return [{**s, "id": i, "timestamp": f"2026-10-22T{20 - i:02d}:00:00Z"} for i in range(5)]


def rodar():
    at = AppTest.from_file(str(PASTA / "app.py"), default_timeout=30)
    return at.run()


class TestPainel(unittest.TestCase):
    @patch.object(cliente, "historico", side_effect=historico)
    @patch.object(cliente, "status_sensores", return_value=SENSORES)
    def test_cartoes_e_resumo(self, *_):
        at = rodar()
        self.assertFalse(at.exception)
        html = " ".join(m.value for m in at.markdown)
        for rotulo in ("NORMAL", "CRÍTICO", "ATENÇÃO", "SEM DADOS"):
            self.assertIn(rotulo, html)
        self.assertIn("1 crítico(s)", html)
        self.assertIn("pulso", html)  # cartão crítico pisca

    @patch.object(cliente, "historico", side_effect=historico)
    @patch.object(cliente, "status_sensores", return_value=SENSORES)
    def test_abre_no_sensor_critico(self, *_):
        at = rodar()
        self.assertEqual(at.selectbox[0].value["tag"], "MOT-102")
        caixa = next(m.value for m in at.markdown if 'class="diagnostico"' in m.value)
        self.assertIn("Diagnóstico: CRÍTICO", caixa)
        self.assertIn("RMS 8.20", caixa)

    @patch.object(cliente, "historico", side_effect=historico)
    @patch.object(cliente, "status_sensores", return_value=SENSORES)
    def test_sensor_sem_leituras(self, *_):
        at = rodar()
        at.selectbox[0].set_value(SENSORES[3]).run()
        self.assertIn("ainda não tem leituras", at.info[0].value)

    @patch.object(cliente, "status_sensores", side_effect=cliente.ApiIndisponivel("conexão recusada"))
    def test_api_fora_do_ar(self, *_):
        at = rodar()
        self.assertFalse(at.exception)
        self.assertIn("API indisponível", at.error[0].value)
        self.assertEqual(len(at.selectbox), 0)


if __name__ == "__main__":
    unittest.main()
