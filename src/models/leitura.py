def listar_ultimas(con, limite: int = 10) -> list[dict]:
    rows = con.execute(
        "SELECT l.id, l.sensor_id, a.tag, l.timestamp, l.rms, l.assimetria, l.curtose, "
        "l.frequencia_pico, l.rotacao_rpm, l.status_alerta "
        "FROM leituras_brutas l JOIN sensores s ON s.id = l.sensor_id "
        "JOIN ativos a ON a.id = s.ativo_id "
        "ORDER BY l.timestamp DESC, l.id DESC LIMIT ?", (limite,)).fetchall()
    return [dict(r) for r in rows]


def inserir(con, d: dict) -> int:
    cur = con.execute(
        "INSERT INTO leituras_brutas (sensor_id, timestamp, rms, assimetria, curtose, "
        "frequencia_pico, rotacao_rpm, status_alerta) "
        "VALUES (:sensor_id, :timestamp, :rms, :assimetria, :curtose, "
        ":frequencia_pico, :rotacao_rpm, :status_alerta)", d)
    con.commit()
    return cur.lastrowid
