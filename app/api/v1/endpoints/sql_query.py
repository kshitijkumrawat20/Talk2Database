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
from typing import Optional
import uuid
router = APIRouter()

class SQLQueryRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None

class SQLQueryResponse(BaseModel):
    result: str
    thread_id: str ## client can use this to continue the conversation

@router.post("/query", response_model=SQLQueryResponse)
async def query_database(request: SQLQueryRequest):
    try:
        ## generate if not provided thread id 
        thread_id = request.thread_id or str(uuid.uuid4())
        ## add debug 
        print(f"Thread ID: {thread_id}, Query: {request.query}")
        result = sql_agent.execute_query(request.query, config={"configurable": {"thread_id": thread_id}})
        print(f"Result: {result}")
        return SQLQueryResponse(result=result, thread_id=thread_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))