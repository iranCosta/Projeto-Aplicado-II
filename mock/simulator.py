#!/usr/bin/env python3
"""
Simulador / Mock de dados de vibração industrial
Projeto Aplicado II - Diagnóstico Preditivo (ArcelorMittal / Tuper)

Gera janelas de vibração sintéticas (sinal bruto com numpy), reduz cada janela a
RMS, assimetria, curtose e frequência de pico, e grava no formato escolhido.

Operação normal ~90% do tempo; anomalias ~10% (configurável), em episódios com
severidade crescente (degradação progressiva), como numa falha real.

Exemplos:
    python simulator.py                                  # lote de 3000 leituras -> SQLite
    python simulator.py --n 5000 --saida csv json        # lote em CSV e JSON
    python simulator.py --modo stream --intervalo 1      # 1 leitura/sensor por segundo (Ctrl+C para parar)
    python simulator.py --modo stream --n 20 --intervalo 0.2 --seed 7
"""
import argparse
import csv
import json
import math
import random
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
FS = 2048          # taxa de amostragem (Hz)
JANELA = 1024      # amostras por leitura (0,5 s)

# Limiares de alerta (inspirados na ISO 10816, velocidade RMS em mm/s)
LIM_RMS_ATENCAO, LIM_RMS_CRITICO = 4.5, 7.1
LIM_CURT_ATENCAO, LIM_CURT_CRITICO = 4.0, 8.0
LIM_RMS_SENSOR_TRAVADO = 0.2

TIPOS_ANOMALIA = ["DESBALANCEAMENTO", "DESALINHAMENTO", "FALHA_ROLAMENTO", "PICO_ISOLADO", "SENSOR_TRAVADO"]

ATIVOS = [
    (1, "MOT-101", "Motor Laminador 1", "MOTOR", "Laminação", 1780),
    (2, "MOT-102", "Motor Laminador 2", "MOTOR", "Laminação", 1780),
    (3, "CMP-201", "Compressor de Ar 1", "COMPRESSOR", "Utilidades", 3560),
    (4, "CMP-202", "Compressor de Ar 2", "COMPRESSOR", "Utilidades", 3560),
]
SENSORES = [  # (id, ativo_id, posicao)
    (1, 1, "LADO_ACOPLADO"), (2, 1, "LADO_LIVRE"),
    (3, 2, "LADO_ACOPLADO"), (4, 2, "LADO_LIVRE"),
    (5, 3, "LADO_ACOPLADO"), (6, 4, "LADO_ACOPLADO"),
]


@dataclass
class Episodio:
    tipo: str
    duracao: int
    passo: int = 0

    def severidade(self) -> float:
        """Rampa de 0,4 a 1,0 ao longo do episódio (degradação progressiva)."""
        if self.duracao <= 1:
            return 1.0
        return 0.4 + 0.6 * self.passo / (self.duracao - 1)


@dataclass
class SensorSim:
    sensor_id: int
    rpm_nominal: float
    rng: random.Random
    nprng: np.random.Generator
    frac_anomalia: float
    r0: float = 0.0
    episodio: Episodio | None = None
    ultimo_status: str = "NORMAL"
    duracao_media: float = 8.0

    def __post_init__(self):
        self.r0 = self.rng.uniform(1.2, 2.2)  # nível de vibração "saudável" deste sensor

    # ---- controle de episódios ------------------------------------------------
    def _sorteia_episodio(self):
        f = self.frac_anomalia
        if f <= 0:
            return
        p_inicio = f / (self.duracao_media * (1 - f))
        if self.rng.random() < p_inicio:
            tipo = self.rng.choices(TIPOS_ANOMALIA, weights=[3, 2, 3, 2, 1])[0]
            if tipo == "PICO_ISOLADO":
                dur = self.rng.randint(1, 2)
            elif tipo == "SENSOR_TRAVADO":
                dur = self.rng.randint(3, 8)
            else:
                dur = max(3, int(self.rng.gauss(self.duracao_media + 2, 3)))
            self.episodio = Episodio(tipo, dur)

    # ---- geração do sinal -----------------------------------------------------
    def _sinal(self, tipo: str | None, sev: float) -> tuple[np.ndarray, float]:
        rpm = self.rpm_nominal * (1 + self.rng.gauss(0, 0.004))
        f1 = rpm / 60.0
        t = np.arange(JANELA) / FS
        fase = self.rng.uniform(0, 2 * math.pi)
        a1 = self.r0 * 1.1 * (1 + self.rng.gauss(0, 0.03))
        a2 = a1 * 0.2
        ruido = self.r0 * 0.3

        if tipo == "DESBALANCEAMENTO":
            a1 *= 1 + 3.5 * sev
        elif tipo == "DESALINHAMENTO":
            a1 *= 1 + 1.0 * sev
            a2 *= 1 + 14 * sev
        elif tipo == "SENSOR_TRAVADO":
            a1, a2, ruido = 0.0, 0.0, self.r0 * 0.005

        x = (a1 * np.sin(2 * np.pi * f1 * t + fase)
             + a2 * np.sin(2 * np.pi * 2 * f1 * t + 0.5 * fase)
             + self.nprng.normal(0, ruido, JANELA))

        if tipo == "FALHA_ROLAMENTO":
            # trem de impulsos (~3,58x, tipo BPFO) excitando ressonância de 700 Hz com decaimento
            periodo = int(FS / (3.58 * f1))
            n = np.arange(int(0.004 * FS))
            pulso = np.exp(-n / (0.0008 * FS)) * np.sin(2 * np.pi * 700 * n / FS)
            for i in range(self.rng.randint(0, periodo - 1), JANELA, periodo):
                fim = min(JANELA, i + len(n))
                x[i:fim] += self.r0 * 12 * sev * pulso[: fim - i]
        elif tipo == "PICO_ISOLADO":
            for _ in range(self.rng.randint(1, 2)):
                x[self.rng.randrange(JANELA)] += self.r0 * 18 * self.rng.choice([-1, 1])
        return x, rpm

    @staticmethod
    def _indicadores(x: np.ndarray) -> dict:
        xc = x - x.mean()
        m2 = float(np.mean(xc ** 2))
        rms = math.sqrt(float(np.mean(x ** 2)))
        m3 = float(np.mean(xc ** 3))
        m4 = float(np.mean(xc ** 4))
        assim = m3 / m2 ** 1.5 if m2 > 1e-12 else 0.0
        curt = m4 / m2 ** 2 if m2 > 1e-12 else 3.0
        espectro = np.abs(np.fft.rfft(xc))
        freq_pico = float(np.argmax(espectro[1:]) + 1) * FS / JANELA
        return {"rms": rms, "assimetria": assim, "curtose": curt, "frequencia_pico": freq_pico}

    @staticmethod
    def classifica(ind: dict) -> str:
        if ind["rms"] >= LIM_RMS_CRITICO or ind["curtose"] >= LIM_CURT_CRITICO:
            return "CRITICO"
        if (ind["rms"] >= LIM_RMS_ATENCAO or ind["curtose"] >= LIM_CURT_ATENCAO
                or ind["rms"] < LIM_RMS_SENSOR_TRAVADO):
            return "ATENCAO"
        return "NORMAL"

    def proxima_leitura(self, ts: datetime) -> dict:
        if self.episodio is None:
            self._sorteia_episodio()
        ep = self.episodio
        tipo, sev = (ep.tipo, ep.severidade()) if ep else (None, 0.0)
        x, rpm = self._sinal(tipo, sev)
        ind = self._indicadores(x)
        if ep:
            ep.passo += 1
            if ep.passo >= ep.duracao:
                self.episodio = None
        return {
            "sensor_id": self.sensor_id,
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rms": round(ind["rms"], 4),
            "assimetria": round(ind["assimetria"], 4),
            "curtose": round(ind["curtose"], 4),
            "frequencia_pico": round(ind["frequencia_pico"], 1),
            "rotacao_rpm": round(rpm, 1),
            "status_alerta": self.classifica(ind),
            "anomalia_real": 1 if tipo else 0,
            "tipo_anomalia": tipo,
        }


def criar_sensores(seed: int, frac: float) -> list[SensorSim]:
    rpm_por_ativo = {a[0]: a[5] for a in ATIVOS}
    sims = []
    for sid, aid, _ in SENSORES:
        s = seed * 1000 + sid
        sims.append(SensorSim(sid, rpm_por_ativo[aid], random.Random(s), np.random.default_rng(s), frac))
    return sims


def gera_alerta(leitura: dict, leitura_id: int, ultimo: dict) -> dict | None:
    """Alerta quando o status do sensor piora em relação à leitura anterior."""
    ordem = {"NORMAL": 0, "ATENCAO": 1, "CRITICO": 2}
    sid, st = leitura["sensor_id"], leitura["status_alerta"]
    anterior = ultimo.get(sid, "NORMAL")
    ultimo[sid] = st
    if ordem[st] > ordem[anterior]:
        return {
            "leitura_id": leitura_id, "sensor_id": sid, "timestamp": leitura["timestamp"],
            "severidade": st,
            "mensagem": f"Sensor {sid}: {st} (RMS={leitura['rms']} mm/s, curtose={leitura['curtose']})",
            "reconhecido": 0,
        }
    return None


# ----------------------------------------------------------------------------- saídas
def abre_db(caminho: Path, recriar: bool) -> sqlite3.Connection:
    if recriar and caminho.exists():
        caminho.unlink()
    con = sqlite3.connect(caminho)
    con.executescript((AQUI / "schema.sql").read_text(encoding="utf-8"))
    con.executemany("INSERT OR IGNORE INTO ativos VALUES (?,?,?,?,?,?)", ATIVOS)
    con.executemany("INSERT OR IGNORE INTO sensores (id, ativo_id, posicao) VALUES (?,?,?)", SENSORES)
    con.commit()
    return con


COLS_LEIT = ["sensor_id", "timestamp", "rms", "assimetria", "curtose", "frequencia_pico",
             "rotacao_rpm", "status_alerta", "anomalia_real", "tipo_anomalia"]


def insere_leitura(con: sqlite3.Connection, l: dict, ultimo: dict) -> int:
    cur = con.execute(
        f"INSERT INTO leituras_brutas ({','.join(COLS_LEIT)}) VALUES ({','.join('?' * len(COLS_LEIT))})",
        [l[c] for c in COLS_LEIT])
    lid = cur.lastrowid
    a = gera_alerta(l, lid, ultimo)
    if a:
        con.execute("INSERT INTO alertas (leitura_id, sensor_id, timestamp, severidade, mensagem, reconhecido) "
                    "VALUES (:leitura_id,:sensor_id,:timestamp,:severidade,:mensagem,:reconhecido)", a)
    return lid


def grava_csv_json(leituras: list[dict], saidas: list[str], pasta: Path):
    if "csv" in saidas:
        with open(pasta / "leituras_brutas.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS_LEIT)
            w.writeheader()
            w.writerows(leituras)
        with open(pasta / "ativos.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "tag", "nome", "tipo", "localizacao", "rpm_nominal"])
            w.writerows(ATIVOS)
        with open(pasta / "sensores.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "ativo_id", "posicao"])
            w.writerows(SENSORES)
    if "json" in saidas:
        doc = {
            "ativos": [dict(zip(["id", "tag", "nome", "tipo", "localizacao", "rpm_nominal"], a)) for a in ATIVOS],
            "sensores": [dict(zip(["id", "ativo_id", "posicao"], s)) for s in SENSORES],
            "leituras_brutas": leituras,
        }
        (pasta / "leituras_brutas.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")


# ----------------------------------------------------------------------------- modos
def modo_batch(args, pasta: Path):
    sims = criar_sensores(args.seed, args.anomalias)
    por_sensor = math.ceil(args.n / len(sims))
    agora = datetime.now(timezone.utc).replace(microsecond=0)
    inicio = agora - timedelta(seconds=args.passo * por_sensor)
    leituras = []
    for sim in sims:
        for i in range(por_sensor):
            leituras.append(sim.proxima_leitura(inicio + timedelta(seconds=args.passo * i)))
    leituras.sort(key=lambda l: (l["timestamp"], l["sensor_id"]))
    leituras = leituras[: args.n]

    if "sqlite" in args.saida:
        con = abre_db(pasta / "vibracao.db", recriar=True)
        ultimo: dict = {}
        for l in leituras:
            insere_leitura(con, l, ultimo)
        con.commit()
        con.close()
    grava_csv_json(leituras, args.saida, pasta)
    n_anom = sum(l["anomalia_real"] for l in leituras)
    print(f"[ok] {len(leituras)} leituras | {n_anom} anômalas ({100 * n_anom / len(leituras):.1f}%) | "
          f"{len(sims)} sensores | saída: {', '.join(args.saida)} em {pasta}")


def modo_stream(args, pasta: Path):
    sims = criar_sensores(args.seed, args.anomalias)
    con = abre_db(pasta / "vibracao.db", recriar=args.recriar)
    ultimo: dict = {}
    cor = {"NORMAL": "\033[92m", "ATENCAO": "\033[93m", "CRITICO": "\033[91m"}
    total = 0
    print(f"[stream] {len(sims)} sensores, 1 leitura/sensor a cada {args.intervalo}s. Ctrl+C para parar.")
    try:
        while args.n == 0 or total < args.n:
            ts = datetime.now(timezone.utc).replace(microsecond=0)
            for sim in sims:
                l = sim.proxima_leitura(ts)
                insere_leitura(con, l, ultimo)
                total += 1
                marca = f" <- {l['tipo_anomalia']}" if l["anomalia_real"] else ""
                print(f"{l['timestamp']} sensor={l['sensor_id']} rms={l['rms']:6.2f} curt={l['curtose']:6.2f} "
                      f"pico={l['frequencia_pico']:7.1f}Hz {cor[l['status_alerta']]}{l['status_alerta']}\033[0m{marca}")
                if args.n and total >= args.n:
                    break
            con.commit()
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\n[stream] interrompido.")
    finally:
        con.commit()
        con.close()
    print(f"[ok] {total} leituras gravadas em {pasta / 'vibracao.db'}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Simulador de vibração industrial (ArcelorMittal/Tuper)")
    p.add_argument("--modo", choices=["batch", "stream"], default="batch")
    p.add_argument("--n", type=int, default=3000,
                   help="batch: nº total de leituras; stream: nº de leituras (0 = infinito)")
    p.add_argument("--saida", nargs="+", choices=["sqlite", "csv", "json"], default=["sqlite"],
                   help="formatos do modo batch (stream grava sempre em SQLite)")
    p.add_argument("--anomalias", type=float, default=0.10, help="fração de leituras anômalas (padrão 0.10)")
    p.add_argument("--passo", type=int, default=60, help="batch: segundos entre leituras de um sensor")
    p.add_argument("--intervalo", type=float, default=1.0, help="stream: segundos entre rodadas")
    p.add_argument("--seed", type=int, default=42, help="semente para reproduzir os dados")
    p.add_argument("--pasta", default=str(AQUI / "data"), help="pasta de saída")
    p.add_argument("--recriar", action="store_true", help="stream: apaga o banco antes de começar")
    args = p.parse_args(argv)
    if not 0 <= args.anomalias < 1:
        p.error("--anomalias deve estar entre 0 e 1")
    pasta = Path(args.pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    (modo_batch if args.modo == "batch" else modo_stream)(args, pasta)


if __name__ == "__main__":
    sys.exit(main())
