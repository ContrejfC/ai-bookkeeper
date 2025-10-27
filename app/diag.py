import os
import socket
import asyncio
import asyncpg
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/diag/network")
async def diag():
    """Minimal database connectivity test"""
    try:
        url = os.environ["DATABASE_URL"]
        host = url.split("@")[1].split("/")[0].split(":")[0]
        
        # Test TCP connectivity
        try:
            socket.gethostbyname(host)
            with socket.create_connection((host, 5432), timeout=5) as s:
                pass
            tcp_status = "ok"
        except Exception as e:
            raise HTTPException(500, f"tcp_failed: {e}")
        
        # Test SQL connectivity
        try:
            conn = await asyncpg.connect(url, timeout=10)
            v = await conn.fetchval("select 1")
            await conn.close()
            sql_status = "ok"
            sql_value = v
        except Exception as e:
            raise HTTPException(500, f"sql_failed: {e}")
        
        return {"tcp": tcp_status, "sql": sql_status, "value": sql_value}
        
    except Exception as e:
        raise HTTPException(500, f"diagnostic_failed: {e}")
