import sqlite3

from src.config import DATABASE_PATH, SCHEMA_PATH

# Mesmos dados do mock/simulator.py (necessários por causa das chaves estrangeiras)
ATIVOS = [
    (1, "MOT-101", "Motor Laminador 1", "MOTOR", "Laminação", 1780),
    (2, "MOT-102", "Motor Laminador 2", "MOTOR", "Laminação", 1780),
    (3, "CMP-201", "Compressor de Ar 1", "COMPRESSOR", "Utilidades", 3560),
    (4, "CMP-202", "Compressor de Ar 2", "COMPRESSOR", "Utilidades", 3560),
]
SENSORES = [
    (1, 1, "LADO_ACOPLADO"), (2, 1, "LADO_LIVRE"),
    (3, 2, "LADO_ACOPLADO"), (4, 2, "LADO_LIVRE"),
    (5, 3, "LADO_ACOPLADO"), (6, 4, "LADO_ACOPLADO"),
]


def get_connection(criar: bool = False) -> sqlite3.Connection:
    """Por padrão NÃO cria o arquivo: se o banco sumir, a conexão falha (útil para o /health)."""
    modo = "rwc" if criar else "rw"
    con = sqlite3.connect(f"{DATABASE_PATH.as_uri()}?mode={modo}", uri=True)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db() -> None:
    """Cria as tabelas (schema.sql) e os ativos/sensores iniciais, se ainda não existirem."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = get_connection(criar=True)
    try:
        con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        con.executemany("INSERT OR IGNORE INTO ativos VALUES (?,?,?,?,?,?)", ATIVOS)
        con.executemany("INSERT OR IGNORE INTO sensores (id, ativo_id, posicao) VALUES (?,?,?)", SENSORES)
        con.commit()
    finally:
        con.close()
