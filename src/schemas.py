"""
Esquemas de validação (Pydantic v2) da entrada da API.

Limites operacionais, para janelas de 1024 amostras a 2048 Hz (mesmas do simulador):
- frequencia_pico <= 1024 Hz (frequência de Nyquist: metade da taxa de amostragem);
- curtose entre 1 e 1024 e |assimetria| <= 32: limites matemáticos para 1024 amostras;
- rms <= 100 mm/s (bem acima do nível crítico da ISO 10816) e rotação entre 0 e 10.000 rpm.
"""
from datetime import datetime, timedelta, timezone

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictInt, field_validator

TOLERANCIA_FUTURO = timedelta(minutes=5)  # diferença aceitável entre o relógio do sensor e o servidor


def _numero(**limites):
    # strict: não converte texto ("1.5") nem booleano; allow_inf_nan=False: recusa NaN e infinito
    return Field(strict=True, allow_inf_nan=False, **limites)


class LeituraIn(BaseModel):
    """Indicadores de uma janela de vibração. O status é calculado pela API, não enviado."""

    model_config = ConfigDict(extra="forbid")

    sensor_id: StrictInt = Field(gt=0, examples=[1])
    timestamp: AwareDatetime = Field(examples=["2026-10-22T20:00:00Z"])
    rms: float = _numero(ge=0, le=100, examples=[1.53])
    assimetria: float = _numero(ge=-32, le=32, examples=[0.18])
    curtose: float = _numero(ge=1, le=1024, examples=[3.0])
    frequencia_pico: float = _numero(ge=0, le=1024, examples=[30.0])
    rotacao_rpm: float = _numero(gt=0, le=10000, examples=[1780])

    @field_validator("timestamp")
    @classmethod
    def _nao_no_futuro(cls, v: datetime) -> datetime:
        if v - datetime.now(timezone.utc) > TOLERANCIA_FUTURO:
            raise ValueError("timestamp não pode estar no futuro")
        return v

    def para_banco(self) -> dict:
        """Dicionário no formato da tabela leituras_brutas (timestamp ISO 8601 em UTC)."""
        dados = self.model_dump()
        dados["timestamp"] = self.timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return dados
