"""Testes da regra de diagnóstico. Rode da raiz: python -m unittest services.test_regras -v"""
import unittest

from services.regras import (LIM_CURT_ATENCAO, LIM_CURT_CRITICO, LIM_RMS_ATENCAO, LIM_RMS_CRITICO,
                             LIM_RMS_SENSOR_TRAVADO, DadosInvalidosError, deve_alertar, diagnosticar_leitura)

SENSORES = {1, 2, 3, 4, 5, 6}


def leitura(**kw):
    base = {"sensor_id": 1, "rms": 1.5, "assimetria": 0.1, "curtose": 3.0,
            "frequencia_pico": 30.0, "rotacao_rpm": 1780}
    return {**base, **kw}


class TestStatus(unittest.TestCase):
    def test_caso_perfeito(self):
        r = diagnosticar_leitura(leitura(), SENSORES)
        self.assertEqual((r["status"], r["cor"]), ("NORMAL", "verde"))

    def test_caso_critico(self):
        r = diagnosticar_leitura(leitura(rms=8.2, curtose=9.0), SENSORES)
        self.assertEqual((r["status"], r["cor"]), ("CRITICO", "vermelho"))
        self.assertEqual(len(r["motivos"]), 2)

    def test_atencao_por_rms(self):
        self.assertEqual(diagnosticar_leitura(leitura(rms=5.0))["status"], "ATENCAO")

    def test_atencao_por_curtose(self):
        self.assertEqual(diagnosticar_leitura(leitura(curtose=5.0))["status"], "ATENCAO")

    def test_sensor_travado(self):
        r = diagnosticar_leitura(leitura(rms=0.05))
        self.assertEqual(r["status"], "ATENCAO")
        self.assertIn("travado", r["motivos"][0])

    def test_critico_prevalece_sobre_atencao(self):
        # curtose em atenção, RMS em crítico -> crítico, sem motivo de atenção
        r = diagnosticar_leitura(leitura(rms=7.5, curtose=5.0))
        self.assertEqual(r["status"], "CRITICO")
        self.assertEqual(len(r["motivos"]), 1)

    def test_limites_exatos(self):
        casos = [
            (dict(rms=LIM_RMS_ATENCAO - 0.01), "NORMAL"),
            (dict(rms=LIM_RMS_ATENCAO), "ATENCAO"),
            (dict(rms=LIM_RMS_CRITICO - 0.01), "ATENCAO"),
            (dict(rms=LIM_RMS_CRITICO), "CRITICO"),
            (dict(curtose=LIM_CURT_ATENCAO), "ATENCAO"),
            (dict(curtose=LIM_CURT_CRITICO), "CRITICO"),
            (dict(rms=LIM_RMS_SENSOR_TRAVADO), "NORMAL"),
        ]
        for kw, esperado in casos:
            with self.subTest(**kw):
                self.assertEqual(diagnosticar_leitura(leitura(**kw))["status"], esperado)

    def test_funcao_pura(self):
        entrada = leitura(rms=6.0)
        copia = dict(entrada)
        self.assertEqual(diagnosticar_leitura(entrada), diagnosticar_leitura(entrada))
        self.assertEqual(entrada, copia)


class TestEntradaInvalida(unittest.TestCase):
    def assertInvalida(self, entrada, trecho, sensores=None):
        with self.assertRaises(DadosInvalidosError) as ctx:
            diagnosticar_leitura(entrada, sensores)
        self.assertIn(trecho, str(ctx.exception))

    def test_vazia_ou_nao_dict(self):
        for entrada in ({}, None, [], "texto"):
            with self.subTest(entrada=entrada):
                self.assertInvalida(entrada, "vazia")

    def test_campo_ausente(self):
        entrada = leitura()
        del entrada["curtose"]
        self.assertInvalida(entrada, "curtose")

    def test_sensor_id_invalido(self):
        for sid in ("1", None, 0, -3, 1.0, True):
            with self.subTest(sensor_id=sid):
                self.assertInvalida(leitura(sensor_id=sid), "sensor_id")

    def test_sensor_inexistente(self):
        self.assertInvalida(leitura(sensor_id=99), "inexistente", SENSORES)

    def test_erro_informa_o_campo(self):
        with self.assertRaises(DadosInvalidosError) as ctx:
            diagnosticar_leitura(leitura(rotacao_rpm=0))
        self.assertEqual(ctx.exception.campo, "rotacao_rpm")

    def test_valores_nao_numericos(self):
        for v in (None, "1.5", float("nan"), float("inf"), True):
            with self.subTest(valor=v):
                self.assertInvalida(leitura(rms=v), "rms")

    def test_negativos_e_rotacao_zero(self):
        self.assertInvalida(leitura(rms=-0.1), "rms negativo")
        self.assertInvalida(leitura(frequencia_pico=-1), "frequência")
        self.assertInvalida(leitura(rotacao_rpm=0), "rotação")



class TestAlerta(unittest.TestCase):
    def test_alerta_so_quando_piora(self):
        casos = [(None, "NORMAL", False), (None, "ATENCAO", True), (None, "CRITICO", True),
                 ("NORMAL", "ATENCAO", True), ("ATENCAO", "CRITICO", True), ("NORMAL", "CRITICO", True),
                 ("ATENCAO", "ATENCAO", False), ("CRITICO", "ATENCAO", False), ("CRITICO", "NORMAL", False)]
        for anterior, atual, esperado in casos:
            with self.subTest(anterior=anterior, atual=atual):
                self.assertEqual(deve_alertar(anterior, atual), esperado)

if __name__ == "__main__":
    unittest.main()
