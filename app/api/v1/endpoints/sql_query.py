# # from fastapi import APIRouter, HTTPException
# # from app.models import SQLQueryRequest, SQLQueryResponse
# # from app.services.sql_agent import execute_query

# # router = APIRouter()

# # @router.post("/query", response_model=SQLQueryResponse)
# # async def query_database(request: SQLQueryRequest):
# #     try:
# #         result = execute_query(request.query)
# #         return SQLQueryResponse(result=result)
# #     except ValueError as e:
# #         raise HTTPException(status_code=400, detail=str(e))
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))

# # app/api/v1/endpoints/sql_query.py
# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from app.services.sql_agent_instance import sql_agent

# router = APIRouter()

# class SQLQueryRequest(BaseModel):
#     query: str

# class SQLQueryResponse(BaseModel):
#     result: str

# @router.post("/query", response_model=SQLQueryResponse)
# async def query_database(request: SQLQueryRequest):
#     try:
#         result = sql_agent.execute_query(request.query)
#         return SQLQueryResponse(result=result)
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.sql_agent_instance import sql_agent
from typing import Optional
import uuid
from langchain_core.messages import AIMessage
from sqlalchemy import text
from app.api.v1.auth import get_db

router = APIRouter()

class SQLQueryRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None
    username: Optional[str] = "developer"

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

        # Extract the SQL query from the LangGraph state messages
        sql_query = None
        try:
            state = sql_agent.app.get_state({"configurable": {"thread_id": thread_id}})
            messages = state.values.get("messages", [])
            for msg in reversed(messages):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        # Check if execute_query tool was called
                        if tc.get("name") == "execute_query":
                            # The argument name might be query
                            sql_query = tc.get("args", {}).get("query")
                            break
                    if sql_query:
                        break
        except Exception as e:
            print(f"Error extracting SQL query from state: {e}")

        # Save to query history if found
        if sql_query:
            try:
                username = request.username or "developer"
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO query_history (username, natural_query, generated_sql) VALUES (?, ?, ?)",
                    (username, request.query, sql_query)
                )
                conn.commit()
                conn.close()
                print("Logged successfully executed query to history.")
            except Exception as e:
                print(f"Error saving query to history: {e}")

        return SQLQueryResponse(result=result, thread_id=thread_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query/explain")
async def explain_query(request: SQLQueryRequest):
    if not sql_agent.db:
        raise HTTPException(
            status_code=400,
            detail="Database connection is not established. Please set up the connection first."
        )
    try:
        query = request.query.strip().rstrip(";")
        dialect = sql_agent.db._engine.dialect.name
        
        # Dialect specific syntax
        if dialect == "postgresql":
            explain_sql = f"EXPLAIN (FORMAT JSON) {query}"
        elif dialect == "mysql":
            explain_sql = f"EXPLAIN FORMAT=JSON {query}"
        else:
            explain_sql = f"EXPLAIN QUERY PLAN {query}"
        
        with sql_agent.db._engine.connect() as connection:
            result = connection.execute(text(explain_sql))
            rows = result.fetchall()
            
            # Format results into a serializable list of dicts/lists
            plan_output = []
            for row in rows:
                if dialect in ["postgresql", "mysql"]:
                    # Usually returns a single column containing JSON
                    plan_output.append(row[0])
                else:
                    # SQLite returns (id, parent, notused, detail)
                    plan_output.append(dict(row._mapping))
            
            return {
                "dialect": dialect,
                "explain_query": explain_sql,
                "plan": plan_output
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while explaining the query: {str(e)}"
        )

