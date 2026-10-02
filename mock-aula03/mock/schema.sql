-- =====================================================================
-- Modelagem de dados enxuta - Diagnóstico Preditivo (ArcelorMittal/Tuper)
-- SQLite | 4 tabelas: ativos, sensores, leituras_brutas, alertas
-- =====================================================================
PRAGMA foreign_keys = ON;

-- Máquinas monitoradas (motores e compressores)
CREATE TABLE IF NOT EXISTS ativos (
    id            INTEGER PRIMARY KEY,
    tag           TEXT    NOT NULL UNIQUE,            -- ex: MOT-101
    nome          TEXT    NOT NULL,
    tipo          TEXT    NOT NULL CHECK (tipo IN ('MOTOR','COMPRESSOR')),
    localizacao   TEXT,
    rpm_nominal   REAL    NOT NULL CHECK (rpm_nominal > 0)
);

-- Sensores de vibração instalados nos ativos
CREATE TABLE IF NOT EXISTS sensores (
    id                  INTEGER PRIMARY KEY,
    ativo_id            INTEGER NOT NULL REFERENCES ativos(id),
    posicao             TEXT    NOT NULL,              -- ex: LADO_ACOPLADO / LADO_LIVRE
    taxa_amostragem_hz  INTEGER NOT NULL DEFAULT 2048,
    unidade             TEXT    NOT NULL DEFAULT 'mm/s'
);

-- Uma linha = uma janela de vibração já reduzida a indicadores estatísticos
CREATE TABLE IF NOT EXISTS leituras_brutas (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id        INTEGER NOT NULL REFERENCES sensores(id),
    timestamp        TEXT    NOT NULL,                 -- ISO 8601 (UTC)
    rms              REAL    NOT NULL CHECK (rms >= 0),
    assimetria       REAL    NOT NULL,                 -- skewness
    curtose          REAL    NOT NULL,                 -- kurtosis (não-excesso; normal ~3)
    frequencia_pico  REAL    NOT NULL CHECK (frequencia_pico >= 0),  -- Hz
    rotacao_rpm      REAL    NOT NULL,
    status_alerta    TEXT    NOT NULL CHECK (status_alerta IN ('NORMAL','ATENCAO','CRITICO')),
    -- Gabarito do simulador (só existe no mock; serve para validar o detector):
    anomalia_real    INTEGER NOT NULL DEFAULT 0 CHECK (anomalia_real IN (0,1)),
    tipo_anomalia    TEXT                              -- NULL quando normal
);
CREATE INDEX IF NOT EXISTS idx_leituras_sensor_ts ON leituras_brutas(sensor_id, timestamp);

-- Alertas gerados quando o status de um sensor piora
CREATE TABLE IF NOT EXISTS alertas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    leitura_id    INTEGER NOT NULL REFERENCES leituras_brutas(id),
    sensor_id     INTEGER NOT NULL REFERENCES sensores(id),
    timestamp     TEXT    NOT NULL,
    severidade    TEXT    NOT NULL CHECK (severidade IN ('ATENCAO','CRITICO')),
    mensagem      TEXT    NOT NULL,
    reconhecido   INTEGER NOT NULL DEFAULT 0
);
