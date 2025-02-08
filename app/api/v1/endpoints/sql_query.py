from fastapi import APIRouter, HTTPException
from app.models import SQLQueryRequest, SQLQueryResponse
from app.services.sql_agent import execute_query

router = APIRouter()

@router.post("/query", response_model=SQLQueryResponse)
async def query_database(request: SQLQueryRequest):
    try:
        result = execute_query(request.query)
        return SQLQueryResponse(result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))