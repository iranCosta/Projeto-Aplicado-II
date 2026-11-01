COLUNAS = ("al.id, al.leitura_id, al.sensor_id, a.tag, s.posicao, al.timestamp, al.severidade, "
           "al.mensagem, al.reconhecido")
JOIN = ("FROM alertas al JOIN sensores s ON s.id = al.sensor_id "
        "JOIN ativos a ON a.id = s.ativo_id")


def _formatar(row) -> dict:
    d = dict(row)
    d["reconhecido"] = bool(d["reconhecido"])
    return d


def inserir(con, a: dict) -> int:
    cur = con.execute(
        "INSERT INTO alertas (leitura_id, sensor_id, timestamp, severidade, mensagem, reconhecido) "
        "VALUES (:leitura_id, :sensor_id, :timestamp, :severidade, :mensagem, 0)", a)
    return cur.lastrowid


def listar(con, limite: int, sensor_id: int | None = None, reconhecido: bool | None = None) -> list[dict]:
    filtros, params = [], []
    if sensor_id is not None:
        filtros.append("al.sensor_id = ?")
        params.append(sensor_id)
    if reconhecido is not None:
        filtros.append("al.reconhecido = ?")
        params.append(int(reconhecido))
    where = f"WHERE {' AND '.join(filtros)} " if filtros else ""
    rows = con.execute(f"SELECT {COLUNAS} {JOIN} {where}ORDER BY al.timestamp DESC, al.id DESC LIMIT ?",
                       (*params, limite)).fetchall()
    return [_formatar(r) for r in rows]


def contar_nao_reconhecidos(con) -> int:
    return con.execute("SELECT COUNT(*) FROM alertas WHERE reconhecido = 0").fetchone()[0]


def buscar(con, alerta_id: int) -> dict | None:
    row = con.execute(f"SELECT {COLUNAS} {JOIN} WHERE al.id = ?", (alerta_id,)).fetchone()
    return _formatar(row) if row else None


def reconhecer(con, alerta_id: int) -> None:
    con.execute("UPDATE alertas SET reconhecido = 1 WHERE id = ?", (alerta_id,))
    con.commit()
