COLUNAS = ("l.id, l.sensor_id, a.tag, l.timestamp, l.rms, l.assimetria, l.curtose, "
           "l.frequencia_pico, l.rotacao_rpm, l.status_alerta")
JOIN_ATIVO = ("FROM leituras_brutas l JOIN sensores s ON s.id = l.sensor_id "
              "JOIN ativos a ON a.id = s.ativo_id")


def listar_ultimas(con, limite: int = 10) -> list[dict]:
    return listar_filtradas(con, limite)


def listar_filtradas(con, limite: int, sensor_id: int | None = None, status: str | None = None) -> list[dict]:
    filtros, params = [], []
    if sensor_id is not None:
        filtros.append("l.sensor_id = ?")
        params.append(sensor_id)
    if status is not None:
        filtros.append("l.status_alerta = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(filtros)} " if filtros else ""
    rows = con.execute(
        f"SELECT {COLUNAS} {JOIN_ATIVO} {where}"
        "ORDER BY l.timestamp DESC, l.id DESC LIMIT ?", (*params, limite)).fetchall()
    return [dict(r) for r in rows]


def ultima_por_sensor(con) -> list[dict]:
    """Uma linha por sensor com a leitura mais recente (campos da leitura nulos se ainda não houver)."""
    rows = con.execute(
        "SELECT s.id AS sensor_id, a.tag, a.nome AS ativo, s.posicao, l.id AS leitura_id, l.timestamp, "
        "l.rms, l.assimetria, l.curtose, l.frequencia_pico, l.rotacao_rpm, l.status_alerta "
        "FROM sensores s JOIN ativos a ON a.id = s.ativo_id "
        "LEFT JOIN leituras_brutas l ON l.id = (SELECT id FROM leituras_brutas WHERE sensor_id = s.id "
        "ORDER BY timestamp DESC, id DESC LIMIT 1) "
        "ORDER BY s.id").fetchall()
    return [dict(r) for r in rows]


def ids_sensores(con) -> set[int]:
    return {r[0] for r in con.execute("SELECT id FROM sensores")}


def inserir(con, d: dict) -> int:
    cur = con.execute(
        "INSERT INTO leituras_brutas (sensor_id, timestamp, rms, assimetria, curtose, "
        "frequencia_pico, rotacao_rpm, status_alerta) "
        "VALUES (:sensor_id, :timestamp, :rms, :assimetria, :curtose, "
        ":frequencia_pico, :rotacao_rpm, :status_alerta)", d)
    return cur.lastrowid  # o commit fica com quem chama (leitura e alerta na mesma transação)


def status_anterior(con, sensor_id: int, timestamp: str, leitura_id: int) -> str | None:
    """Status da leitura imediatamente anterior (no tempo) do mesmo sensor."""
    row = con.execute(
        "SELECT status_alerta FROM leituras_brutas WHERE sensor_id = ? AND id != ? "
        "AND (timestamp < ? OR (timestamp = ? AND id < ?)) ORDER BY timestamp DESC, id DESC LIMIT 1",
        (sensor_id, leitura_id, timestamp, timestamp, leitura_id)).fetchone()
    return row[0] if row else None
