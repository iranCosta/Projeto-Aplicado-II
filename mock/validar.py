#!/usr/bin/env python3
"""Valida os dados gerados em data/vibracao.db e imprime um relatório.
Uso: python validar.py [caminho_do_db]
Sai com código 1 se alguma verificação falhar."""
import sqlite3
import sys
from pathlib import Path

db = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data" / "vibracao.db"
if not db.exists():
    sys.exit(f"Banco não encontrado: {db}. Rode antes: python simulator.py")
con = sqlite3.connect(db)
q = lambda sql: con.execute(sql).fetchall()
falhas = []


def check(nome, ok, detalhe=""):
    print(f"  [{'OK' if ok else 'FALHA'}] {nome} {detalhe}")
    if not ok:
        falhas.append(nome)


total = q("SELECT COUNT(*) FROM leituras_brutas")[0][0]
print(f"\n== Contagens ==\n  ativos={q('SELECT COUNT(*) FROM ativos')[0][0]} "
      f"sensores={q('SELECT COUNT(*) FROM sensores')[0][0]} leituras={total} "
      f"alertas={q('SELECT COUNT(*) FROM alertas')[0][0]}")

print("\n== Distribuição por status ==")
for st, n in q("SELECT status_alerta, COUNT(*) FROM leituras_brutas GROUP BY 1 ORDER BY 2 DESC"):
    print(f"  {st:8s} {n:6d} ({100 * n / total:.1f}%)")

print("\n== Anomalias injetadas ==")
for tp, n, rms, curt in q("SELECT COALESCE(tipo_anomalia,'(normal)'), COUNT(*), ROUND(AVG(rms),2), "
                          "ROUND(AVG(curtose),2) FROM leituras_brutas GROUP BY 1 ORDER BY 2 DESC"):
    print(f"  {tp:18s} n={n:6d}  rms_médio={rms:6.2f}  curtose_média={curt:6.2f}")

print("\n== Verificações ==")
check("há leituras", total > 0)
frac = q("SELECT AVG(anomalia_real) FROM leituras_brutas")[0][0]
check("fração de anomalias entre 5% e 15%", 0.05 <= frac <= 0.15, f"(={100 * frac:.1f}%)")
check("todos os tipos de anomalia presentes",
      q("SELECT COUNT(DISTINCT tipo_anomalia) FROM leituras_brutas WHERE tipo_anomalia IS NOT NULL")[0][0] == 5)
check("sem valores nulos/negativos em rms", q("SELECT COUNT(*) FROM leituras_brutas WHERE rms IS NULL OR rms<0")[0][0] == 0)
check("sem FK órfã (sensor)", q("SELECT COUNT(*) FROM leituras_brutas l LEFT JOIN sensores s ON s.id=l.sensor_id WHERE s.id IS NULL")[0][0] == 0)
check("sem FK órfã (alerta→leitura)", q("SELECT COUNT(*) FROM alertas a LEFT JOIN leituras_brutas l ON l.id=a.leitura_id WHERE l.id IS NULL")[0][0] == 0)
rms_norm = q("SELECT MAX(rms), AVG(curtose) FROM leituras_brutas WHERE anomalia_real=0")[0]
check("normais abaixo do limiar de atenção (RMS < 4,5)", rms_norm[0] < 4.5, f"(máx={rms_norm[0]:.2f})")
check("curtose média normal próxima de 2–3,5", 1.5 < rms_norm[1] < 3.5, f"(={rms_norm[1]:.2f})")

# Quão bem o limiar simples separa o gabarito (referência para o Isolation Forest da equipe)
tp = q("SELECT COUNT(*) FROM leituras_brutas WHERE anomalia_real=1 AND status_alerta!='NORMAL'")[0][0]
fn = q("SELECT COUNT(*) FROM leituras_brutas WHERE anomalia_real=1 AND status_alerta='NORMAL'")[0][0]
fp = q("SELECT COUNT(*) FROM leituras_brutas WHERE anomalia_real=0 AND status_alerta!='NORMAL'")[0][0]
print(f"\n== Regra de limiar vs. gabarito ==\n  detectadas={tp} perdidas(início de degradação)={fn} falsos_alarmes={fp}")
print("\nRESULTADO:", "TUDO OK" if not falhas else f"{len(falhas)} falha(s): {falhas}")
sys.exit(1 if falhas else 0)
