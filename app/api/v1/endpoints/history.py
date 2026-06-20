from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from app.api.v1.auth import get_db

router = APIRouter()

class HistoryItem(BaseModel):
    id: int
    username: str
    natural_query: str
    generated_sql: str
    executed_at: str

class HistoryCreate(BaseModel):
    username: str
    natural_query: str
    generated_sql: str

@router.post("/history")
def add_to_history(item: HistoryCreate):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO query_history (username, natural_query, generated_sql) VALUES (?, ?, ?)",
            (item.username, item.natural_query, item.generated_sql)
        )
        conn.commit()
        conn.close()
        return {"message": "Query added to history successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/history", response_model=List[HistoryItem])
def get_history(username: Optional[str] = None):
    try:
        conn = get_db()
        cur = conn.cursor()
        if username:
            cur.execute(
                "SELECT id, username, natural_query, generated_sql, executed_at FROM query_history WHERE username = ? ORDER BY executed_at DESC", 
                (username,)
            )
        else:
            cur.execute("SELECT id, username, natural_query, generated_sql, executed_at FROM query_history ORDER BY executed_at DESC")
        
        rows = cur.fetchall()
        items = []
        for row in rows:
            items.append({
                "id": row["id"],
                "username": row["username"],
                "natural_query": row["natural_query"],
                "generated_sql": row["generated_sql"],
                "executed_at": str(row["executed_at"])
            })
        conn.close()
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
