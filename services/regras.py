"""
Regra de negócio: diagnóstico de uma leitura de vibração.

Recebe os indicadores de uma janela de vibração (RMS, curtose, ...) e devolve
o status do ativo (NORMAL / ATENCAO / CRITICO) com o motivo.
Limiares inspirados na ISO 10816 (mesmos do simulator.py).
"""
import math

LIM_RMS_ATENCAO, LIM_RMS_CRITICO = 4.5, 7.1
LIM_CURT_ATENCAO, LIM_CURT_CRITICO = 4.0, 8.0
LIM_RMS_SENSOR_TRAVADO = 0.2

CAMPOS_NUMERICOS = ["rms", "assimetria", "curtose", "frequencia_pico", "rotacao_rpm"]


class DadosInvalidosError(ValueError):
    """Entrada fora do esperado (nulo, negativo, campo faltando, sensor inexistente)."""


def _validar(leitura, sensores_validos):
    if not isinstance(leitura, dict) or not leitura:
        raise DadosInvalidosError("leitura vazia ou em formato inválido (esperado dict)")

    faltando = [c for c in ["sensor_id"] + CAMPOS_NUMERICOS if c not in leitura]
    if faltando:
        raise DadosInvalidosError(f"campos ausentes: {faltando}")

    if sensores_validos is not None and leitura["sensor_id"] not in sensores_validos:
        raise DadosInvalidosError(f"sensor inexistente: {leitura['sensor_id']}")

    for campo in CAMPOS_NUMERICOS:
        v = leitura[campo]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v):
            raise DadosInvalidosError(f"{campo} nulo ou não numérico: {v!r}")

    if leitura["rms"] < 0:
        raise DadosInvalidosError(f"rms negativo: {leitura['rms']}")
    if leitura["frequencia_pico"] < 0:
        raise DadosInvalidosError(f"frequência de pico negativa: {leitura['frequencia_pico']}")
    if leitura["rotacao_rpm"] <= 0:
        raise DadosInvalidosError(f"rotação deve ser maior que zero: {leitura['rotacao_rpm']}")


def diagnosticar_leitura(leitura: dict, sensores_validos=None) -> dict:
    """Função pura: mesma entrada, mesma saída. Levanta DadosInvalidosError se a entrada for ruim."""
    _validar(leitura, sensores_validos)
    rms, curt = leitura["rms"], leitura["curtose"]
    motivos = []

    if rms >= LIM_RMS_CRITICO:
        motivos.append(f"RMS {rms:.2f} >= {LIM_RMS_CRITICO} (crítico)")
    if curt >= LIM_CURT_CRITICO:
        motivos.append(f"curtose {curt:.2f} >= {LIM_CURT_CRITICO} (crítico)")
    if motivos:
        status = "CRITICO"
    else:
        if rms >= LIM_RMS_ATENCAO:
            motivos.append(f"RMS {rms:.2f} >= {LIM_RMS_ATENCAO} (atenção)")
        if curt >= LIM_CURT_ATENCAO:
            motivos.append(f"curtose {curt:.2f} >= {LIM_CURT_ATENCAO} (atenção)")
        if rms < LIM_RMS_SENSOR_TRAVADO:
            motivos.append(f"RMS {rms:.2f} < {LIM_RMS_SENSOR_TRAVADO}: possível sensor travado")
        status = "ATENCAO" if motivos else "NORMAL"

    return {
        "sensor_id": leitura["sensor_id"],
        "status": status,
        "cor": {"NORMAL": "verde", "ATENCAO": "amarelo", "CRITICO": "vermelho"}[status],
        "motivos": motivos or ["indicadores dentro dos limites"],
    }
