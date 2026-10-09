from fastapi.responses import JSONResponse

from src.database import get_connection


def checar_saude() -> JSONResponse:
    try:
        con = get_connection()
        try:
            con.execute("SELECT 1").fetchone()
        finally:
            con.close()
        return JSONResponse(status_code=200, content={"status": "healthy", "database": "connected"})
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "disconnected"})
