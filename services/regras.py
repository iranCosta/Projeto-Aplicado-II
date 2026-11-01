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
    """Entrada fora do esperado (nulo, negativo, campo faltando, sensor inexistente).
    `campo` indica qual campo causou o erro, quando é um só (a API devolve isso ao cliente)."""

    def __init__(self, mensagem: str, campo: str | None = None):
        super().__init__(mensagem)
        self.campo = campo


def _validar(leitura, sensores_validos):
    if not isinstance(leitura, dict) or not leitura:
        raise DadosInvalidosError("leitura vazia ou em formato inválido (esperado dict)")

    faltando = [c for c in ["sensor_id"] + CAMPOS_NUMERICOS if c not in leitura]
    if faltando:
        raise DadosInvalidosError(f"campos ausentes: {faltando}")

    sid = leitura["sensor_id"]
    if isinstance(sid, bool) or not isinstance(sid, int) or sid <= 0:
        raise DadosInvalidosError(f"sensor_id deve ser inteiro positivo: {sid!r}", "sensor_id")

    if sensores_validos is not None and leitura["sensor_id"] not in sensores_validos:
        raise DadosInvalidosError(f"sensor inexistente: {leitura['sensor_id']}", "sensor_id")

    for campo in CAMPOS_NUMERICOS:
        v = leitura[campo]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v):
            raise DadosInvalidosError(f"{campo} nulo ou não numérico: {v!r}", campo)

    if leitura["rms"] < 0:
        raise DadosInvalidosError(f"rms negativo: {leitura['rms']}", "rms")
    if leitura["frequencia_pico"] < 0:
        raise DadosInvalidosError(f"frequência de pico negativa: {leitura['frequencia_pico']}", "frequencia_pico")
    if leitura["rotacao_rpm"] <= 0:
        raise DadosInvalidosError(f"rotação deve ser maior que zero: {leitura['rotacao_rpm']}", "rotacao_rpm")


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



GRAVIDADE = {"NORMAL": 0, "ATENCAO": 1, "CRITICO": 2}


def deve_alertar(status_anterior: str | None, status_atual: str) -> bool:
    """Alerta quando o status do sensor piora em relação à leitura anterior (sem anterior = NORMAL)."""
    return GRAVIDADE[status_atual] > GRAVIDADE[status_anterior or "NORMAL"]

if __name__ == "__main__":
    # Demonstração no terminal (Aula 05). Rode da raiz: python -m services.regras
    base = {"sensor_id": 1, "assimetria": 0.1, "frequencia_pico": 30.0, "rotacao_rpm": 1780}
    cenarios = {
        "1. caso perfeito": {**base, "rms": 1.5, "curtose": 3.0},
        "2. caso crítico": {**base, "rms": 8.2, "curtose": 9.0},
        "3. erro de entrada": {**base, "rms": -1.0, "curtose": 3.0},
    }
    for nome, leitura in cenarios.items():
        try:
            print(f"{nome}: {diagnosticar_leitura(leitura, sensores_validos={1, 2, 3, 4, 5, 6})}")
        except DadosInvalidosError as e:
            print(f"{nome}: DadosInvalidosError -> {e}")
