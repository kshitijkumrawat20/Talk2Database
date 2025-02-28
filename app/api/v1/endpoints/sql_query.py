# from fastapi import APIRouter, HTTPException
# from app.models import SQLQueryRequest, SQLQueryResponse
# from app.services.sql_agent import execute_query

# router = APIRouter()

# @router.post("/query", response_model=SQLQueryResponse)
# async def query_database(request: SQLQueryRequest):
#     try:
#         result = execute_query(request.query)
#         return SQLQueryResponse(result=result)
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# app/api/v1/endpoints/sql_query.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.sql_agent_instance import sql_agent

router = APIRouter()

class SQLQueryRequest(BaseModel):
    query: str

class SQLQueryResponse(BaseModel):
    result: str

@router.post("/query", response_model=SQLQueryResponse)
async def query_database(request: SQLQueryRequest):
    try:
        result = sql_agent.execute_query(request.query)
        return SQLQueryResponse(result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))