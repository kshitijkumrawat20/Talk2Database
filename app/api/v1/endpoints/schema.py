from fastapi import APIRouter, HTTPException 
from sqlalchemy import inspect 
from app.services.sql_agent_instance import sql_agent
from pydantic import BaseModel 
from typing import List 

class TableIndexingRequest(BaseModel):
    table_names: List[str]


router = APIRouter()

@router.get("/schema")
async def get_schema():
    if not sql_agent.db: 
        raise HTTPException(
            status_code=400,
            detail="Database connection is not established. Please set up the connection first."
        )
    try: 
        inspector = inspect(sql_agent.db._engine)
        schema_data = {}
        for table_name in inspector.get_table_names():
            columns = []
            for col in inspector.get_columns(table_name):
                columns.append({
                    "name": col['name'],
                    "type": str(col['type']),
                    "nullable": col.get('nullable', True)
                })
            fks = []
            for fk in inspector.get_foreign_keys(table_name):
                fks.append({
                    "constrained_columns": fk['constrained_columns'],
                    "referred_table": fk['referred_table'],
                    "referred_columns": fk['referred_columns']
                })
            schema_data[table_name] = {
                "columns": columns,
                "foreign_keys": fks
            }
        return schema_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching the schema."
        )
    
@router.post("/schema/indexing")
async def update_indexing(request: TableIndexingRequest):
    if not sql_agent.db:
        raise HTTPException(
            status_code=400,
            detail="Database connection is not established. Please set up the connection first."
        )
    try:
        # Set allowed tables on the agent and the database wrapper
        sql_agent.allowed_tables = request.table_names
        sql_agent.db.allowed_tables = request.table_names
        return {"message": "Indexing updated successfully for the specified tables."}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while updating indexing: {str(e)}"
        )

@router.get("/schema/indexing")
async def get_indexing():
    if not sql_agent.db:
        raise HTTPException(
            status_code=400,
            detail="Database connection is not established. Please set up the connection first."
        )
    try:
        inspector = inspect(sql_agent.db._engine)
        all_tables = inspector.get_table_names()
        allowed = getattr(sql_agent, 'allowed_tables', all_tables)  # Default to all tables if not set
        return {"all_tables": all_tables, "allowed_tables": allowed}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching indexing information: {str(e)}"
        )