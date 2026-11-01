"""Testes do painel com a API simulada. Rode da raiz: python -m unittest dashboard.test_dashboard -v"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA))

import cliente  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402


def sensor(sid, tag, status, rms=1.5, curtose=3.0, leitura_id=1, modelo=None):
    motivos = {"NORMAL": ["indicadores dentro dos limites"], "ATENCAO": ["RMS 5.00 >= 4.5 (atenção)"],
               "CRITICO": ["RMS 8.20 >= 7.1 (crítico)"], None: ["sem leituras"]}[status]
    return {"sensor_id": sid, "tag": tag, "ativo": f"Ativo {tag}", "posicao": "LADO_ACOPLADO",
            "leitura_id": leitura_id, "timestamp": "2026-10-22T20:00:00Z" if leitura_id else None,
            "rms": rms if leitura_id else None, "curtose": curtose if leitura_id else None,
            "status_alerta": status, "cor": None, "motivos": motivos, "modelo": modelo}


SENSORES = [
    sensor(1, "MOT-101", "NORMAL", modelo={"anomalia": True, "score": 0.71}),
    sensor(2, "MOT-102", "CRITICO", rms=8.2),
    sensor(3, "CMP-201", "ATENCAO", rms=5.0),
    sensor(4, "CMP-202", None, leitura_id=None),
]


def historico(sensor_id, limite=200):
    s = next(x for x in SENSORES if x["sensor_id"] == sensor_id)
    if s["leitura_id"] is None:
        return []
    return [{**s, "id": i, "timestamp": f"2026-10-22T{20 - i:02d}:00:00Z"} for i in range(5)]


ALERTAS = {"total": 2, "nao_reconhecidos": 3, "alertas": [
    {"id": 11, "leitura_id": 5, "sensor_id": 2, "tag": "MOT-102", "posicao": "LADO_ACOPLADO",
     "timestamp": "2026-10-22T20:00:00Z", "severidade": "CRITICO", "mensagem": "RMS 8.20 >= 7.1 (crítico)",
     "reconhecido": False},
    {"id": 10, "leitura_id": 4, "sensor_id": 3, "tag": "CMP-201", "posicao": "LADO_ACOPLADO",
     "timestamp": "2026-10-22T19:00:00Z", "severidade": "ATENCAO", "mensagem": "RMS 5.00 >= 4.5 (atenção)",
     "reconhecido": False},
]}


def rodar():
    at = AppTest.from_file(str(PASTA / "app.py"), default_timeout=30)
    return at.run()


class TestPainel(unittest.TestCase):
    def setUp(self):
        # nenhum teste fala com a API de verdade
        for nome, kw in (("alertas_pendentes", {"return_value": ALERTAS}), ("reconhecer", {"return_value": {}})):
            p = patch.object(cliente, nome, **kw)
            setattr(self, nome, p.start())
            self.addCleanup(p.stop)

    @patch.object(cliente, "historico", side_effect=historico)
    @patch.object(cliente, "status_sensores", return_value=SENSORES)
    def test_lista_de_alertas_e_reconhecer(self, *_):
        at = rodar()
        self.assertTrue(any("Alertas não reconhecidos: 3" in s.value for s in at.subheader))
        html = " ".join(m.value for m in at.markdown)
        self.assertIn("RMS 8.20 &gt;= 7.1 (crítico)", html)
        self.assertIn("Mostrando os 2 mais recentes de 3", " ".join(c.value for c in at.caption))
        at.button(key="reconhecer_11").click().run()
        self.reconhecer.assert_called_once_with(11)

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

    @patch.object(cliente, "historico", side_effect=historico)
    @patch.object(cliente, "status_sensores", return_value=SENSORES)
    def test_modelo_no_cartao_e_na_caixa(self, *_):
        at = rodar()
        html = " ".join(m.value for m in at.markdown)
        self.assertEqual(html.count("visibility:hidden"), 3)  # aviso visível só no MOT-101 (regra NORMAL)
        self.assertIn("1 com padrão anômalo pelo modelo", html)
        self.assertIn("Modelo preditivo: não treinado", html)  # MOT-102 aberto, sem avaliação do modelo
        at.selectbox[0].set_value(SENSORES[0]).run()
        caixa = next(m.value for m in at.markdown if 'class="diagnostico"' in m.value)
        self.assertIn("PADRÃO ANÔMALO (score 0.71)", caixa)

    @patch.object(cliente, "historico", side_effect=historico)
    def test_api_cai_depois_de_responder(self, *_):
        with patch.object(cliente, "status_sensores", return_value=SENSORES):
            at = rodar()
        self.assertTrue(any("Conectado à API" in c.value for c in at.caption))
        with patch.object(cliente, "status_sensores", side_effect=cliente.ApiIndisponivel("conexão recusada")):
            at.run()
        self.assertIn("Sem comunicação com a API desde", at.error[0].value)
        html = " ".join(m.value for m in at.markdown)
        self.assertIn("CRÍTICO", html)  # os últimos dados continuam na tela...
        self.assertIn('class="desatualizado"', html)  # ...esmaecidos

    @patch.object(cliente, "status_sensores", side_effect=cliente.ApiIndisponivel("conexão recusada"))
    def test_api_fora_do_ar(self, *_):
        at = rodar()
        self.assertFalse(at.exception)
        self.assertIn("API indisponível", at.error[0].value)
        self.assertEqual(len(at.selectbox), 0)


if __name__ == "__main__":
    unittest.main()
