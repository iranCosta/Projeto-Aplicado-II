"""Testes automatizados do mock. Rode: python -m unittest test_mock -v"""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import simulator


class TestSimulador(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pasta = Path(cls.tmp.name)
        simulator.main(["--n", "3000", "--saida", "sqlite", "csv", "json", "--seed", "1", "--pasta", str(cls.pasta)])
        cls.con = sqlite3.connect(cls.pasta / "vibracao.db")

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        cls.tmp.cleanup()

    def q(self, sql):
        return self.con.execute(sql).fetchall()

    def test_quantidade(self):
        self.assertEqual(self.q("SELECT COUNT(*) FROM leituras_brutas")[0][0], 3000)

    def test_proporcao_normal_anomalia(self):
        frac = self.q("SELECT AVG(anomalia_real) FROM leituras_brutas")[0][0]
        self.assertTrue(0.05 <= frac <= 0.15, frac)

    def test_todos_tipos_de_anomalia(self):
        tipos = {r[0] for r in self.q("SELECT DISTINCT tipo_anomalia FROM leituras_brutas WHERE tipo_anomalia IS NOT NULL")}
        self.assertEqual(tipos, set(simulator.TIPOS_ANOMALIA))

    def test_normais_dentro_da_faixa(self):
        mx = self.q("SELECT MAX(rms) FROM leituras_brutas WHERE anomalia_real=0")[0][0]
        self.assertLess(mx, simulator.LIM_RMS_ATENCAO)

    def test_anomalias_geram_alertas(self):
        self.assertGreater(self.q("SELECT COUNT(*) FROM alertas")[0][0], 0)
        self.assertGreater(self.q("SELECT COUNT(*) FROM leituras_brutas WHERE status_alerta='CRITICO'")[0][0], 0)

    def test_rolamento_tem_curtose_alta(self):
        v = self.q("SELECT AVG(curtose) FROM leituras_brutas WHERE tipo_anomalia='FALHA_ROLAMENTO'")[0][0]
        self.assertGreater(v, 4)

    def test_checks_do_banco_rejeitam_entrada_invalida(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO leituras_brutas (sensor_id,timestamp,rms,assimetria,curtose,frequencia_pico,"
                             "rotacao_rpm,status_alerta) VALUES (1,'2026-01-01T00:00:00Z',-1,0,3,30,1780,'NORMAL')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO leituras_brutas (sensor_id,timestamp,rms,assimetria,curtose,frequencia_pico,"
                             "rotacao_rpm,status_alerta) VALUES (1,'2026-01-01T00:00:00Z',1,0,3,30,1780,'XYZ')")

    def test_csv_json_gerados(self):
        self.assertTrue((self.pasta / "leituras_brutas.csv").exists())
        doc = json.loads((self.pasta / "leituras_brutas.json").read_text(encoding="utf-8"))
        self.assertEqual(len(doc["leituras_brutas"]), 3000)

    def test_reprodutivel_com_seed(self):
        with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
            for t in (t1, t2):
                simulator.main(["--n", "60", "--saida", "json", "--seed", "9", "--pasta", t])
            a = json.loads((Path(t1) / "leituras_brutas.json").read_text())["leituras_brutas"]
            b = json.loads((Path(t2) / "leituras_brutas.json").read_text())["leituras_brutas"]
            self.assertEqual([x["rms"] for x in a], [x["rms"] for x in b])


if __name__ == "__main__":
    unittest.main()
