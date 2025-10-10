from pydantic import BaseModel, Field
from langgraph.graph import MessagesState

class SQLAgentState(MessagesState):
    """State for the agent"""
    next_tool : str = ""
    tables_list: str = ""
    schema_of_table: str = ""
    query_gen : str= ""
    # check_query: str = ""
    execute_query : str = ""
    task_complete: bool = False
    response_to_user: str= ""
    current_task: str = ""
    query: str = "" ## query of the human stored in it 

class DBQuery(BaseModel):
    query: str = Field(..., description="The SQL query to execute")
