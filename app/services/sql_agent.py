# # from langchain_community.utilities import SQLDatabase
# # from langchain_groq import ChatGroq
# # from langgraph.graph import StateGraph, END, START
# # from langchain_core.messages import AIMessage, ToolMessage, AnyMessage
# # from langgraph.graph.message import AnyMessage, add_messages
# # from langchain_core.tools import tool
# # from typing import Annotated, Literal, TypedDict, Any
# # from pydantic import BaseModel, Field
# # from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks
# # from langgraph.prebuilt import ToolNode
# # from langchain_core.prompts import ChatPromptTemplate
# # from langchain_community.agent_toolkits import SQLDatabaseToolkit
# # from dotenv import load_dotenv
# # import os
# # from IPython.display import display
# # from PIL import Image
# # import os
# # load_dotenv()

# # # Global variables
# # db = None
# # toolkit = None
# # tools = None
# # list_tables_tool = None
# # sql_db_query = None
# # get_schema_tool = None
# # app = None  # This will store the compiled workflow

# # # Setting up LLM
# # llm = ChatGroq(model="llama3-70b-8192", api_key = os.getenv("GROQ_API_KEY"))

# # def setup_database_connection(connection_string: str):
# #     global db, toolkit, tools, list_tables_tool, sql_db_query, get_schema_tool, app

# #     try:
# #         # Initialize database connection
# #         db = SQLDatabase.from_uri(connection_string)
# #         print("Database connection successful!")

# #         try:
# #             # Initialize toolkit and tools
# #             toolkit = SQLDatabaseToolkit(db=db, llm=llm)
# #             tools = toolkit.get_tools()
# #             for tool in tools:
# #                 print(f"Initialized tool: {tool.name}")

# #             # Create instances of the tools
# #             list_tables_tool = next((tool for tool in tools if tool.name == "sql_db_list_tables"), None)
# #             sql_db_query = next((tool for tool in tools if tool.name == "sql_db_query"), None)
# #             get_schema_tool = next((tool for tool in tools if tool.name == "sql_db_schema"), None)

# #             if not all([list_tables_tool, sql_db_query, get_schema_tool]):
# #                 raise ValueError("Failed to initialize one or more required database tools")

# #             # Initialize workflow and compile it into an app
# #             initialize_workflow()
            
# #             return db

# #         except Exception as e:
# #             print(f"Error initializing tools and workflow: {str(e)}")
# #             raise ValueError(f"Failed to initialize database tools: {str(e)}")

# #     except ImportError as e:
# #         print(f"Database driver import error: {str(e)}")
# #         raise ValueError(f"Missing database driver or invalid database type: {str(e)}")
# #     except ValueError as e:
# #         print(f"Invalid connection string or configuration: {str(e)}")
# #         raise
# #     except Exception as e:
# #         print(f"Unexpected error during database connection: {str(e)}")
# #         raise ValueError(f"Failed to establish database connection: {str(e)}")

# # def initialize_workflow():
# #     global app

# #     # Binding tools with LLM
# #     llm_to_get_schema = llm.bind_tools([get_schema_tool]) if get_schema_tool else None
# #     llm_with_tools = llm.bind_tools([query_to_database])

# #     class State(TypedDict):
# #         messages: Annotated[list[AnyMessage], add_messages]

# #     class SubmitFinalAnswer(BaseModel):
# #         final_answer: str = Field(..., description="The final answer to the user")

# #     llm_with_final_answer = llm.bind_tools([SubmitFinalAnswer])

# #     def handle_tool_error(state: State):
# #         error = state.get("error")
# #         tool_calls = state["messages"][-1].tool_calls
# #         return {"messages": [ToolMessage(content=f"Error: {repr(error)}\n please fix your mistakes.", tool_call_id=tc["id"],) for tc in tool_calls]}

# #     def create_node_from_tool_with_fallback(tools: list) -> RunnableWithFallbacks[Any, dict]:
# #         return ToolNode(tools).with_fallbacks([RunnableLambda(handle_tool_error)], exception_key="error")

# #     list_tables = create_node_from_tool_with_fallback([list_tables_tool]) if list_tables_tool else None
# #     get_schema = create_node_from_tool_with_fallback([get_schema_tool]) if get_schema_tool else None
# #     query_database = create_node_from_tool_with_fallback([query_to_database])

# #     query_check_system = """You are a SQL expert. Carefully review the SQL query for common mistakes, including:

# #             Issues with NULL handling (e.g., NOT IN with NULLs)
# #             Improper use of UNION instead of UNION ALL
# #             Incorrect use of BETWEEN for exclusive ranges
# #             Data type mismatches or incorrect casting
# #             Quoting identifiers improperly
# #             Incorrect number of arguments in functions
# #             Errors in JOIN conditions

# #             If you find any mistakes, rewrite the query to fix them. If it's correct, reproduce it as is."""
# #     query_check_prompt = ChatPromptTemplate.from_messages([("system", query_check_system), ("placeholder", "{messages}")])
# #     check_generated_query = query_check_prompt | llm_with_tools
    
# #     def check_the_given_query(state: State):
# #         return {"messages": [check_generated_query.invoke({"messages": [state["messages"][-1]]})]}

# #     query_gen_system_prompt = """You are a SQL expert with a strong attention to detail.Given an input question, output a syntactically correct SQLite query to run, then look at the results of the query and return the answer.

# #         1. DO NOT call any tool besides SubmitFinalAnswer to submit the final answer.

# #         When generating the query:

# #         2. Output the SQL query that answers the input question without a tool call.

# #         3. Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.

# #         4. You can order the results by a relevant column to return the most interesting examples in the database.

# #         5. Never query for all the columns from a specific table, only ask for the relevant columns given the question.

# #         6. If you get an error while executing a query, rewrite the query and try again.

# #         7. If you get an empty result set, you should try to rewrite the query to get a non-empty result set.

# #         8. NEVER make stuff up if you don't have enough information to answer the query... just say you don't have enough information.

# #         9. If you have enough information to answer the input question, simply invoke the appropriate tool to submit the final answer to the user.

# #         10. DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database. Do not return any sql query except answer."""
# #     query_gen_prompt = ChatPromptTemplate.from_messages([("system", query_gen_system_prompt), ("placeholder", "{messages}")])
# #     query_generator = query_gen_prompt | llm_with_final_answer

# #     def first_tool_call(state: State) -> dict[str, list[AIMessage]]:
# #         return {"messages": [AIMessage(content="", tool_calls=[{"name": "sql_db_list_tables", "args": {}, "id": "tool_abcd123"}])]}

# #     def check_the_given_query(state: State):
# #         return {"messages": [check_generated_query.invoke({"messages": [state["messages"][-1]]})]}

# #     def generation_query(state: State):
# #         message = query_generator.invoke(state)
# #         tool_messages = []
# #         if message.tool_calls:
# #             for tc in message.tool_calls:
# #                 if tc["name"] != "SubmitFinalAnswer":
# #                     tool_messages.append(
# #                         ToolMessage(
# #                             content=f"Error: The wrong tool was called: {tc['name']}. Please fix your mistakes. Remember to only call SubmitFinalAnswer to submit the final answer. Generated queries should be outputted WITHOUT a tool call.",
# #                             tool_call_id=tc["id"],
# #                         )
# #                     )
# #         else:
# #             tool_messages = []
# #         return {"messages": [message] + tool_messages}

# #     def should_continue(state: State):
# #         messages = state["messages"]
# #         last_message = messages[-1]
# #         if getattr(last_message, "tool_calls", None):
# #             return END
# #         elif last_message.content.startswith("Error:"):
# #             return "query_gen"
# #         else:
# #             return "correct_query"

# #     def llm_get_schema(state: State):
# #         response = llm_to_get_schema.invoke(state["messages"])
# #         return {"messages": [response]}

# #     # Create workflow
# #     workflow = StateGraph(State)
# #     workflow.add_node("first_tool_call", first_tool_call)
# #     workflow.add_node("list_tables_tool", list_tables)
# #     workflow.add_node("get_schema_tool", get_schema)
# #     workflow.add_node("model_get_schema", llm_get_schema)
# #     workflow.add_node("query_gen", generation_query)
# #     workflow.add_node("correct_query", check_the_given_query)
# #     workflow.add_node("execute_query", query_database)

# #     workflow.add_edge(START, "first_tool_call")
# #     workflow.add_edge("first_tool_call", "list_tables_tool")
# #     workflow.add_edge("list_tables_tool", "model_get_schema")
# #     workflow.add_edge("model_get_schema", "get_schema_tool")
# #     workflow.add_edge("get_schema_tool", "query_gen")
# #     workflow.add_conditional_edges("query_gen", should_continue, {END: END, "correct_query": "correct_query"})
# #     workflow.add_edge("correct_query", "execute_query")
# #     workflow.add_edge("execute_query", "query_gen")

# #     # Compile the workflow into an executable app
# #     app = workflow.compile()
    

# #     # # # Save the graph image as a file
# #     # image_path = "workflow_graph.png"
# #     # app.get_graph().draw_mermaid_png().save(image_path)

# #     # Open and display the image
# #     # import io

# #     # # Generate the graph image as bytes
# #     # image_bytes = app.get_graph().draw_mermaid_png()

# #     # # Convert bytes to an Image object
# #     # image = Image.open(io.BytesIO(image_bytes))

# #     # # Save the image to a file
# #     # image_path = "workflow_graph.png"
# #     # image.save(image_path)


# # @tool
# # def query_to_database(query: str) -> str:
# #     """
# #     Execute a SQL query against the database and return the result.
# #     If the query is invalid or returns no result, an error message will be returned.
# #     In case of an error, the user is advised to rewrite the query and try again.
# #     """
# #     if db is None:
# #         return "Error: Database connection not established. Please set up the connection first."
# #     result = db.run_no_throw(query)
# #     if not result:
# #         return "Error: Query failed. Please rewrite your query and try again."
# #     return result

# # def execute_query(query: str):
# #     if db is None:
# #         raise ValueError("Database connection not established. Please set up the connection first.")
# #     if app is None:
# #         raise ValueError("Workflow not initialized. Please set up the connection first.")
# #     response = app.invoke({"messages": [("user", query)]})
# #     return response["messages"][-1].tool_calls[0]["args"]["final_answer"]


from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import AIMessage, ToolMessage, AnyMessage, HumanMessage
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.tools import tool
from typing import Annotated, Literal, TypedDict, Any
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from dotenv import load_dotenv
import os
from IPython.display import display
import PIL
import io
from langgraph.errors import GraphRecursionError

import os
import io
from typing import Annotated, Any, TypedDict

from IPython.display import Image, display
from langchain_core.runnables.graph import MermaidDrawMethod

# Added for more robust tool call handling
from typing import Optional

class SQLAgent:
    def __init__(self, model="llama3-70b-8192"):
        load_dotenv()
        # Initialize instance variables
        self.db = None
        self.toolkit = None
        self.tools = None
        self.list_tables_tool = None
        self.sql_db_query = None
        self.get_schema_tool = None
        self.app = None
        
        # Setting up LLM
        self.llm = ChatGroq(model=model, api_key="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")
        
        # Register the tool method
        self.query_to_database = self._create_query_tool()

    def _create_query_tool(self):
        """Create the query tool bound to this instance"""
        print("creating _create_query_tool")
        @tool
        def query_to_database(query: str) -> str:
            """
            Execute a SQL query against the database and return the result.
            If the query is invalid or returns no result, an error message will be returned.
            In case of an error, the user is advised to rewrite the query and try again.
            """
            if self.db is None:
                return "Error: Database connection not established. Please set up the connection first."
            result = self.db.run_no_throw(query)
            if not result:
                return "Error: Query failed. Please rewrite your query and try again."
            return result
        
        return query_to_database

    def setup_database_connection(self, connection_string: str):
        """Set up database connection and initialize tools"""
        try:
            # Initialize database connection
            self.db = SQLDatabase.from_uri(connection_string)
            print("Database connection successful!")

            try:
                # Initialize toolkit and tools
                self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
                self.tools = self.toolkit.get_tools()
                for tool in self.tools:
                    print(f"Initialized tool: {tool.name}")

                # Create instances of the tools
                self.list_tables_tool = next((tool for tool in self.tools if tool.name == "sql_db_list_tables"), None)
                self.sql_db_query = next((tool for tool in self.tools if tool.name == "sql_db_query"), None)
                self.get_schema_tool = next((tool for tool in self.tools if tool.name == "sql_db_schema"), None)

                if not all([self.list_tables_tool, self.sql_db_query, self.get_schema_tool]):
                    raise ValueError("Failed to initialize one or more required database tools")

                # Initialize workflow and compile it into an app
                self.initialize_workflow()
                
                return self.db

            except Exception as e:
                print(f"Error initializing tools and workflow: {str(e)}")
                raise ValueError(f"Failed to initialize database tools: {str(e)}")

        except ImportError as e:
            print(f"Database driver import error: {str(e)}")
            raise ValueError(f"Missing database driver or invalid database type: {str(e)}")
        except ValueError as e:
            print(f"Invalid connection string or configuration: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error during database connection: {str(e)}")
            raise ValueError(f"Failed to establish database connection: {str(e)}")

    def initialize_workflow(self):
        """Initialize the workflow graph"""
        
        print("Intializing Workflow....")
        # Binding tools with LLM
        llm_to_get_schema = self.llm.bind_tools([self.get_schema_tool]) if self.get_schema_tool else None
        llm_with_tools = self.llm.bind_tools([self.query_to_database])

        class State(TypedDict):
            messages: Annotated[list[AnyMessage], add_messages]

        class SubmitFinalAnswer(BaseModel):
            final_answer: str = Field(..., description="The final answer to the user")

        llm_with_final_answer = self.llm.bind_tools([SubmitFinalAnswer])

        def handle_tool_error(state: State):
            error = state.get("error")
            tool_calls = state["messages"][-1].tool_calls
            return {"messages": [ToolMessage(content=f"Error: {repr(error)}\n please fix your mistakes.", tool_call_id=tc["id"],) for tc in tool_calls]}

        def create_node_from_tool_with_fallback(tools: list) -> RunnableWithFallbacks[Any, dict]:
            return ToolNode(tools).with_fallbacks([RunnableLambda(handle_tool_error)], exception_key="error")

        list_tables = create_node_from_tool_with_fallback([self.list_tables_tool]) if self.list_tables_tool else None
        get_schema = create_node_from_tool_with_fallback([self.get_schema_tool]) if self.get_schema_tool else None
        query_database = create_node_from_tool_with_fallback([self.query_to_database])

        query_check_system = """You are a SQL expert. Carefully review the SQL query for common mistakes, including:

                Issues with NULL handling (e.g., NOT IN with NULLs)
                Improper use of UNION instead of UNION ALL
                Incorrect use of BETWEEN for exclusive ranges
                Data type mismatches or incorrect casting
                Quoting identifiers improperly
                Incorrect number of arguments in functions
                Errors in JOIN conditions

                If you find any mistakes, rewrite the query to fix them. If it's correct, reproduce it as is."""
        query_check_prompt = ChatPromptTemplate.from_messages([("system", query_check_system), ("placeholder", "{messages}")])
        check_generated_query = query_check_prompt | llm_with_tools
        
        def check_the_given_query(state: State):
            return {"messages": [check_generated_query.invoke({"messages": [state["messages"][-1]]})]}

        query_gen_system_prompt = """You are a SQL expert with a strong attention to detail.Given an input question, output a syntactically correct SQLite query to run, then look at the results of the query and return the answer.

            1. DO NOT call any tool besides SubmitFinalAnswer to submit the final answer.

            When generating the query:

            2. Output the SQL query that answers the input question without a tool call.

            3. Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.

            4. You can order the results by a relevant column to return the most interesting examples in the database.

            5. Never query for all the columns from a specific table, only ask for the relevant columns given the question.

            6. If you get an error while executing a query, rewrite the query and try again.

            7. If you get an empty result set, you should try to rewrite the query to get a non-empty result set.

            8. NEVER make stuff up if you don't have enough information to answer the query... just say you don't have enough information.

            9. If you have enough information to answer the input question, simply invoke the appropriate tool to submit the final answer to the user.

            10. DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database. Do not return any sql query except answer."""
        query_gen_prompt = ChatPromptTemplate.from_messages([("system", query_gen_system_prompt), ("placeholder", "{messages}")])
        query_generator = query_gen_prompt | llm_with_final_answer

        def first_tool_call(state: State) -> dict[str, list[AIMessage]]:
            return {"messages": [AIMessage(content="", tool_calls=[{"name": "sql_db_list_tables", "args": {}, "id": "tool_abcd123"}])]}

        def generation_query(state: State):
            message = query_generator.invoke(state)
            tool_messages = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    if tc["name"] != "SubmitFinalAnswer":
                        tool_messages.append(
                            ToolMessage(
                                content=f"Error: The wrong tool was called: {tc['name']}. Please fix your mistakes. Remember to only call SubmitFinalAnswer to submit the final answer. Generated queries should be outputted WITHOUT a tool call.",
                                tool_call_id=tc["id"],
                            )
                        )
            else:
                tool_messages = []
            return {"messages": [message] + tool_messages}

        def should_continue(state: State):
            messages = state["messages"]
            last_message = messages[-1]
            if getattr(last_message, "tool_calls", None):
                # Check if the tool call is SubmitFinalAnswer
                if len(last_message.tool_calls) > 0 and last_message.tool_calls[0]["name"] == "SubmitFinalAnswer":
                    return END
                else:
                    # Wrong tool called, route to error handling (not implemented here)
                    return "query_gen"  # Or a dedicated error node
            elif last_message.content.startswith("Error:"):
                return "query_gen"
            else:
                return "correct_query"

        def llm_get_schema(state: State):
            response = llm_to_get_schema.invoke(state["messages"])
            return {"messages": [response]}

        # Create workflow
        workflow = StateGraph(State)
        workflow.add_node("first_tool_call", first_tool_call)
        workflow.add_node("list_tables_tool", list_tables)
        workflow.add_node("get_schema_tool", get_schema)
        workflow.add_node("model_get_schema", llm_get_schema)
        workflow.add_node("query_gen", generation_query)
        workflow.add_node("correct_query", check_the_given_query)
        workflow.add_node("execute_query", query_database)

        workflow.add_edge(START, "first_tool_call")
        workflow.add_edge("first_tool_call", "list_tables_tool")
        workflow.add_edge("list_tables_tool", "model_get_schema")
        workflow.add_edge("model_get_schema", "get_schema_tool")
        workflow.add_edge("get_schema_tool", "query_gen")
        workflow.add_conditional_edges("query_gen", should_continue, {END: END, "correct_query": "correct_query", "query_gen": "query_gen"})
        workflow.add_edge("correct_query", "execute_query")
        workflow.add_edge("execute_query", "query_gen")

        # Compile the workflow into an executable app
        self.app = workflow.compile()
        
            
        # # Generate the graph image as bytes
        # image_bytes = self.app.get_graph().draw_mermaid_png()

        # # Convert bytes to an Image object
        # image = Image.open(io.BytesIO(image_bytes))

        # # Save the image to a file
        # image.save("workflow_graph.png")
        # print(f"Workflow graph saved")
    
    def is_query_relevant(self, query: str) -> bool:
        """Check if the query is relevant to the database using the LLM."""
        
        # Retrieve the schema of the relevant tables
        if self.list_tables_tool:
            relevant_tables = self.list_tables_tool.invoke("")
            # print(relevant_tables)
        table_list= relevant_tables.split(", ")
        print(table_list)
        # print(agent.get_schema_tool.invoke(table_list[0]))
        schema = ""
        for table in table_list:
            schema+= self.get_schema_tool.invoke(table)

        print(schema)
            
        # if self.get_schema_tool:
        #     schema_response = self.get_schema_tool.invoke({})
        #     table_schema = schema_response.content  # Assuming this returns the schema as a string

        relevance_check_prompt = (
            """You are an expert SQL agent which takes user query in Natural language and find out it have releavnce with the given schema or not. Please determine if the following query is related to a database.Here is the schema of the tables present in database:\n{schema}\n\n. If the query related to given schema respond with 'yes'. Here is the query: {query}. Answer with only 'yes' or 'no'."""
        ).format(schema=relevant_tables, query=query)
        
        response = self.llm.invoke([{"role": "user", "content": relevance_check_prompt}])
    
    # Assuming the LLM returns a simple 'yes' or 'no'
        return response.content == "yes"

    
    def execute_query(self, query: str):
        """Execute a query through the workflow"""
        if self.db is None:
            raise ValueError("Database connection not established. Please set up the connection first.")
        if self.app is None:
            raise ValueError("Workflow not initialized. Please set up the connection first.")
        # First, handle simple queries like "list tables" directly
        query_lower = query.lower()
        if any(phrase in query_lower for phrase in ["list all the tables", "show tables", "name of tables",
                                                    "which tables are present", "how many tables"]):
            if self.list_tables_tool:
                tables = self.list_tables_tool.invoke("")
                return f"The tables in the database are: {tables}"
            else:
                return "Error: Unable to list tables. The list_tables_tool is not initialized."

        # Check if the query is relevant to the database
        if not self.is_query_relevant(query):
            print("Not relevent to database.")
            # If not relevant, let the LLM answer the question directly
            non_relevant_prompt = (
                """You are an expert SQL agent created by Kshitij Kumrawat. You can only assist with questions related to databases so repond the user with the following example resonse and Do not answer any questions that are not related to databases.:  
                Please ask a question that pertains to database operations, such as querying tables, retrieving data, or understanding the database schema. """
            )
    
    # Invoke the LLM with the non-relevant prompt
            response = self.llm.invoke([{"role": "user", "content": non_relevant_prompt}])
            # print(response.content)
            return response.content
        
        # If relevant, proceed with the SQL workflow
        response = self.app.invoke({"messages": [HumanMessage(content=query, role="user")]})

        # More robust final answer extraction
        if (
            response
            and response["messages"]
            and response["messages"][-1].tool_calls
            and len(response["messages"][-1].tool_calls) > 0
            and "args" in response["messages"][-1].tool_calls[0]
            and "final_answer" in response["messages"][-1].tool_calls[0]["args"]
        ):
            return response["messages"][-1].tool_calls[0]["args"]["final_answer"]
        else:
            return "Error: Could not extract final answer."


# import matplotlib.pyplot as plt
# import io
# import base64
# from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, AnyMessage
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_experimental.utilities import PythonREPL
# from langgraph.graph import END, StateGraph, START
# from typing import Annotated, TypedDict, Sequence, Union, Any, Optional
# from pydantic import BaseModel, Field
# import os
# from langchain_groq import ChatGroq
# import logging
# from IPython.display import Image, display
# from langchain_community.utilities import SQLDatabase
# from langchain_community.agent_toolkits import SQLDatabaseToolkit
# from langchain_core.tools import tool
# from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks
# from langgraph.prebuilt import ToolNode
# from dotenv import load_dotenv
# from langgraph.graph.message import AnyMessage, add_messages


# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # ------------------------ Data Models ------------------------

# class VisualizationCode(BaseModel):
#     code: str = Field(..., description="Valid Python code snippet that can be executed to create a visualization")

# class VisualizationAdvice(BaseModel):
#     advice: str = Field(..., description="A single paragraph of advice on how to improve the visualization.")

# class State(TypedDict):
#     messages: Annotated[Sequence[Union[AIMessage, HumanMessage]], "messages"]


# # ------------------------ Visualization Agent ------------------------

# class VisualizationAgent:
#     def __init__(self, model="llama3-70b-8192"):
#         self.llm = ChatGroq(model=model, api_key=os.getenv("GROQ_API_KEY"))
#         self.python_repl = PythonREPL()

#     def create_python_code(self, state: State):
#         """Create visualization based on the query result"""
#         messages = state["messages"]
#         logger.info("---------------------------Creating python code---------------------------")
#         logger.info(f"Messages inside the create_python_code function: {messages}")
#         logger.info("---------------------------------------------------------------------------")

#         create_python_code_system = """
#         You are a data visualization expert. Your ONLY task is to write valid Python code to create a matplotlib visualization based on the provided data. The data can be database results, text from files, etc.
#         Return ONLY the code. Do not include any explanations or surrounding text. Do not use plt.show() and do not set any style elements (colors, gridlines, etc.). The variable names should be descriptive.
#         """

#         create_python_code_prompt = ChatPromptTemplate.from_messages(
#             [("system", create_python_code_system), (MessagesPlaceholder(variable_name="messages"))]
#         )
#         formatted_create_python_code_prompt = create_python_code_prompt.invoke(
#             {"messages": messages}
#         )
#         create_python_code_llm = self.llm.with_structured_output(VisualizationCode)
#         create_python_code_result = create_python_code_llm.invoke(
#             formatted_create_python_code_prompt
#         )
#         logger.info(f"Create python code result: {create_python_code_result}")
#         logger.info(
#             "--------------------------------Python code created--------------------------------"
#         )
#         return {
#             "messages": state["messages"] + [AIMessage(content=create_python_code_result.code)]
#         }

#     def viz_advice(self, state: State):
#         """Give advice on how to improve the visualization"""
#         messages = state["messages"]
#         logger.info(
#             "---------------------------Giving advice on how to improve the visualization---------------------------"
#         )
#         logger.info(f"Messages inside the viz_advice function: {messages}")
#         logger.info(
#             "---------------------------------------------------------------------------"
#         )

#         viz_advice_system = """
#         You are a data visualization expert. You are given a description of data (e.g., database query results, text) and you need to give advice on how to create the best, most intuitive, and comprehensive visualization. Consider the data type, relationships, and what insights the user might be looking for.

#         Return the advice as a single paragraph of text describing the plot to create.
#         """

#         viz_advice_prompt = ChatPromptTemplate.from_messages(
#             [("system", viz_advice_system), ("user", f"Here is the data description: {messages[0].content if messages else ''}")]
#         )
#         formatted_viz_advice_prompt = viz_advice_prompt.invoke({})
#         viz_advice_llm = self.llm.with_structured_output(VisualizationAdvice)
#         viz_advice_result = viz_advice_llm.invoke(formatted_viz_advice_prompt)

#         logger.info(f"Viz advice result: {viz_advice_result}")
#         logger.info(
#             "--------------------------------Advice given--------------------------------"
#         )
#         return {"messages": state["messages"] + [AIMessage(content=viz_advice_result.advice)]}

#     def create_visualization(self, state: State):
#         messages = state["messages"]
#         python_code = messages[-1].content

#         try:
#             logger.info(f"Executing python code: {python_code}")

#             # Execute visualization code
#             output = self.python_repl.run(python_code)
#             logger.info(f"Python REPL output: {output}")

#             buf = io.BytesIO()
#             plt.savefig(buf,
#                         format='png',
#                         bbox_inches='tight',
#                         dpi=300,
#                         facecolor='#ffffff',
#                         edgecolor='none',
#                         pad_inches=0.5,
#                         transparent=False)
#             buf.seek(0)

#             img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
#             img_data_url = f"data:image/png;base64,{img_str}"

#             plt.close('all')

#             return {"messages": state["messages"] + [AIMessage(content=img_data_url)]}

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             logger.error(f"Error during code execution: {str(e)}")
#             return {"messages": state["messages"] + [AIMessage(content=f"Error creating visualization: {str(e)}")]}

#     def graph_workflow(self, query_result: str):
#         workflow = StateGraph(State)

#         workflow.add_node("viz_advice", self.viz_advice)
#         workflow.add_node("create_python_code", self.create_python_code)
#         workflow.add_node("create_visualization", self.create_visualization)

#         workflow.add_edge(START, "viz_advice")
#         workflow.add_edge("viz_advice", "create_python_code")
#         workflow.add_edge("create_python_code", "create_visualization")
#         workflow.add_edge("create_visualization", END)

#         app = workflow.compile()

#         response = app.invoke({"messages": [HumanMessage(content=query_result)]})
#         return response["messages"][-1].content

# # ------------------------ SQL Agent ------------------------

# class SQLAgent:
#     def __init__(self, model="llama3-70b-8192"):
#         load_dotenv()
#         # Initialize instance variables
#         self.db = None
#         self.toolkit = None
#         self.tools = None
#         self.list_tables_tool = None
#         self.sql_db_query = None
#         self.get_schema_tool = None
#         self.app = None
        
#         # Setting up LLM
#         self.llm = ChatGroq(model=model, api_key=os.getenv("GROQ_API_KEY"))
        
#         # Register the tool method
#         self.query_to_database = self._create_query_tool()

#     def _create_query_tool(self):
#         """Create the query tool bound to this instance"""
#         print("creating _create_query_tool")
#         @tool
#         def query_to_database(query: str) -> str:
#             """
#             Execute a SQL query against the database and return the result.
#             If the query is invalid or returns no result, an error message will be returned.
#             In case of an error, the user is advised to rewrite the query and try again.
#             """
#             if self.db is None:
#                 return "Error: Database connection not established. Please set up the connection first."
#             result = self.db.run_no_throw(query)
#             if not result:
#                 return "Error: Query failed. Please rewrite your query and try again."
#             return result
        
#         return query_to_database

#     def setup_database_connection(self, connection_string: str):
#         """Set up database connection and initialize tools"""
#         try:
#             # Initialize database connection
#             self.db = SQLDatabase.from_uri(connection_string)
#             print("Database connection successful!")

#             try:
#                 # Initialize toolkit and tools
#                 self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
#                 self.tools = self.toolkit.get_tools()
#                 for tool in self.tools:
#                     print(f"Initialized tool: {tool.name}")

#                 # Create instances of the tools
#                 self.list_tables_tool = next((tool for tool in self.tools if tool.name == "sql_db_list_tables"), None)
#                 self.sql_db_query = next((tool for tool in self.tools if tool.name == "sql_db_query"), None)
#                 self.get_schema_tool = next((tool for tool in self.tools if tool.name == "sql_db_schema"), None)

#                 if not all([self.list_tables_tool, self.sql_db_query, self.get_schema_tool]):
#                     raise ValueError("Failed to initialize one or more required database tools")

#                 # Initialize workflow and compile it into an app
#                 self.initialize_workflow()
                
#                 return self.db

#             except Exception as e:
#                 print(f"Error initializing tools and workflow: {str(e)}")
#                 raise ValueError(f"Failed to initialize database tools: {str(e)}")

#         except ImportError as e:
#             print(f"Database driver import error: {str(e)}")
#             raise ValueError(f"Missing database driver or invalid database type: {str(e)}")
#         except ValueError as e:
#             print(f"Invalid connection string or configuration: {str(e)}")
#             raise
#         except Exception as e:
#             print(f"Unexpected error during database connection: {str(e)}")
#             raise ValueError(f"Failed to establish database connection: {str(e)}")

#     def initialize_workflow(self):
#         """Initialize the workflow graph"""
        
#         print("Intializing Workflow....")
#         # Binding tools with LLM
#         llm_to_get_schema = self.llm.bind_tools([self.get_schema_tool]) if self.get_schema_tool else None
#         llm_with_tools = self.llm.bind_tools([self.query_to_database])

#         class State(TypedDict):
#             messages: Annotated[list[AnyMessage], add_messages]

#         class SubmitFinalAnswer(BaseModel):
#             final_answer: str = Field(..., description="The final answer to the user")

#         llm_with_final_answer = self.llm.bind_tools([SubmitFinalAnswer])

#         def handle_tool_error(state: State):
#             error = state.get("error")
#             tool_calls = state["messages"][-1].tool_calls
#             return {"messages": [ToolMessage(content=f"Error: {repr(error)}\n please fix your mistakes.", tool_call_id=tc["id"],) for tc in tool_calls]}

#         def create_node_from_tool_with_fallback(tools: list) -> RunnableWithFallbacks[Any, dict]:
#             return ToolNode(tools).with_fallbacks([RunnableLambda(handle_tool_error)], exception_key="error")

#         list_tables = create_node_from_tool_with_fallback([self.list_tables_tool]) if self.list_tables_tool else None
#         get_schema = create_node_from_tool_with_fallback([self.get_schema_tool]) if self.get_schema_tool else None
#         query_database = create_node_from_tool_with_fallback([self.query_to_database])

#         query_check_system = """You are a SQL expert. Carefully review the SQL query for common mistakes, including:

#                 Issues with NULL handling (e.g., NOT IN with NULLs)
#                 Improper use of UNION instead of UNION ALL
#                 Incorrect use of BETWEEN for exclusive ranges
#                 Data type mismatches or incorrect casting
#                 Quoting identifiers improperly
#                 Incorrect number of arguments in functions
#                 Errors in JOIN conditions

#                 If you find any mistakes, rewrite the query to fix them. If it's correct, reproduce it as is."""
#         query_check_prompt = ChatPromptTemplate.from_messages([("system", query_check_system), ("placeholder", "{messages}")])
#         check_generated_query = query_check_prompt | llm_with_tools
        
#         def check_the_given_query(state: State):
#             return {"messages": [check_generated_query.invoke({"messages": [state["messages"][-1]]})]}

#         query_gen_system_prompt = """You are a SQL expert with a strong attention to detail.Given an input question, output a syntactically correct SQLite query to run, then look at the results of the query and return the answer.

#             1. DO NOT call any tool besides SubmitFinalAnswer to submit the final answer.

#             When generating the query:

#             2. Output the SQL query that answers the input question without a tool call.

#             3. Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.

#             4. You can order the results by a relevant column to return the most interesting examples in the database.

#             5. Never query for all the columns from a specific table, only ask for the relevant columns given the question.

#             6. If you get an error while executing a query, rewrite the query and try again.

#             7. If you get an empty result set, you should try to rewrite the query to get a non-empty result set.

#             8. NEVER make stuff up if you don't have enough information to answer the query... just say you don't have enough information.

#             9. If you have enough information to answer the input question, simply invoke the appropriate tool to submit the final answer to the user.

#             10. DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database. Do not return any sql query except answer."""
#         query_gen_prompt = ChatPromptTemplate.from_messages([("system", query_gen_system_prompt), ("placeholder", "{messages}")])
#         query_generator = query_gen_prompt | llm_with_final_answer

#         def first_tool_call(state: State) -> dict[str, list[AIMessage]]:
#             return {"messages": [AIMessage(content="", tool_calls=[{"name": "sql_db_list_tables", "args": {}, "id": "tool_abcd123"}])]}

#         def generation_query(state: State):
#             message = query_generator.invoke(state)
#             tool_messages = []
#             if message.tool_calls:
#                 for tc in message.tool_calls:
#                     if tc["name"] != "SubmitFinalAnswer":
#                         tool_messages.append(
#                             ToolMessage(
#                                 content=f"Error: The wrong tool was called: {tc['name']}. Please fix your mistakes. Remember to only call SubmitFinalAnswer to submit the final answer. Generated queries should be outputted WITHOUT a tool call.",
#                                 tool_call_id=tc["id"],
#                             )
#                         )
#             else:
#                 tool_messages = []
#             return {"messages": [message] + tool_messages}

#         def should_continue(state: State):
#             messages = state["messages"]
#             last_message = messages[-1]
#             if getattr(last_message, "tool_calls", None):
#                 # Check if the tool call is SubmitFinalAnswer
#                 if len(last_message.tool_calls) > 0 and last_message.tool_calls[0]["name"] == "SubmitFinalAnswer":
#                     return END
#                 else:
#                     # Wrong tool called, route to error handling (not implemented here)
#                     return "query_gen"  # Or a dedicated error node
#             elif last_message.content.startswith("Error:"):
#                 return "query_gen"
#             else:
#                 return "correct_query"

#         def llm_get_schema(state: State):
#             response = llm_to_get_schema.invoke(state["messages"])
#             return {"messages": [response]}

#         # Create workflow
#         workflow = StateGraph(State)
#         workflow.add_node("first_tool_call", first_tool_call)
#         workflow.add_node("list_tables_tool", list_tables)
#         workflow.add_node("get_schema_tool", get_schema)
#         workflow.add_node("model_get_schema", llm_get_schema)
#         workflow.add_node("query_gen", generation_query)
#         workflow.add_node("correct_query", check_the_given_query)
#         workflow.add_node("execute_query", query_database)

#         workflow.add_edge(START, "first_tool_call")
#         workflow.add_edge("first_tool_call", "list_tables_tool")
#         workflow.add_edge("list_tables_tool", "model_get_schema")
#         workflow.add_edge("model_get_schema", "get_schema_tool")
#         workflow.add_edge("get_schema_tool", "query_gen")
#         workflow.add_conditional_edges("query_gen", should_continue, {END: END, "correct_query": "correct_query", "query_gen": "query_gen"})
#         workflow.add_edge("correct_query", "execute_query")
#         workflow.add_edge("execute_query", "query_gen")

#         # Compile the workflow into an executable app
#         self.app = workflow.compile()
    
#     def is_query_relevant(self, query: str) -> bool:
#         """Check if the query is relevant to the database using the LLM."""
        
#         # Retrieve the schema of the relevant tables
#         if self.list_tables_tool:
#             relevant_tables = self.list_tables_tool.invoke("")
#             # print(relevant_tables)
#         table_list= relevant_tables.split(", ")
#         print(table_list)
#         # print(agent.get_schema_tool.invoke(table_list[0]))
#         schema = ""
#         for table in table_list:
#             schema+= self.get_schema_tool.invoke(table)

#         print(schema)
            
#         # if self.get_schema_tool:
#         #     schema_response = self.get_schema_tool.invoke({})
#         #     table_schema = schema_response.content  # Assuming this returns the schema as a string

#         relevance_check_prompt = (
#             """You are an expert SQL agent which takes user query in Natural language and find out it have releavnce with the given schema or not. Please determine if the following query is related to a database.Here is the schema of the tables present in database:\n{schema}\n\n. If the query related to given schema respond with 'yes'. Here is the query: {query}. Answer with only 'yes' or 'no'."""
#         ).format(schema=relevant_tables, query=query)
        
#         response = self.llm.invoke([{"role": "user", "content": relevance_check_prompt}])
    
#     # Assuming the LLM returns a simple 'yes' or 'no'
#         return response.content == "yes"
    
#     def execute_query(self, query: str) -> Union[str, bytes]:
#         """Execute a query through the workflow and potentially visualize the results."""
#         if self.db is None:
#             raise ValueError("Database connection not established. Please set up the connection first.")
#         if self.app is None:
#             raise ValueError("Workflow not initialized. Please set up the connection first.")

#         # First, handle simple queries like "list tables" directly
#         query_lower = query.lower()
#         if any(phrase in query_lower for phrase in ["list all the tables", "show tables", "name of tables",
#                                                     "which tables are present", "how many tables"]):
#             if self.list_tables_tool:
#                 tables = self.list_tables_tool.invoke("")
#                 return f"The tables in the database are: {tables}"
#             else:
#                 return "Error: Unable to list tables. The list_tables_tool is not initialized."

#         # Check if the query is relevant to the database
#         if not self.is_query_relevant(query):
#             print("Not relevent to database.")
#             # If not relevant, let the LLM answer the question directly
#             non_relevant_prompt = (
#                 """You are an expert SQL agent created by Kshitij Kumrawat. You can only assist with questions related to databases so repond the user with the following example resonse and Do not answer any questions that are not related to databases.:  
#                 Please ask a question that pertains to database operations, such as querying tables, retrieving data, or understanding the database schema. """
#             )
#             response = self.llm.invoke([{"role": "user", "content": non_relevant_prompt}])
#             return response.content

#         # If relevant, proceed with the SQL workflow
#         response = self.app.invoke({"messages": [HumanMessage(content=query, role="user")]})

#         # More robust final answer extraction
#         if (
#             response
#             and response["messages"]
#             and response["messages"][-1].tool_calls
#             and len(response["messages"][-1].tool_calls) > 0
#             and "args" in response["messages"][-1].tool_calls[0]
#             and "final_answer" in response["messages"][-1].tool_calls[0]["args"]
#         ):
#             final_answer = response["messages"][-1].tool_calls[0]["args"]["final_answer"]
#         else:
#             return "Error: Could not extract final answer."

#         # Check if visualization is requested
#         if "visualize" in query_lower or "chart" in query_lower or "graph" in query_lower:
#             try:
#                 # Chain Visualization Agent to the SQL results
#                 viz_agent = VisualizationAgent()
#                 image_data = viz_agent.graph_workflow(final_answer)
#                 return image_data  # Return the base64-encoded image data
#             except Exception as e:
#                 logger.error(f"Error during visualization: {e}")
#                 return f"Error creating visualization: {e}"
#         else:
#             return final_answer

# ------------------------ Main Execution ------------------------

# if __name__ == "__main__":
#     # Example usage:
#     database_connection_string = "mysql+pymysql://admin:9522359448@mydatabase.cf8u2cy0a4h6.us-east-1.rds.amazonaws.com:3306/mydb" # Replace with your database connection string

#     # Initialize agents
#     sql_agent = SQLAgent()
#     sql_agent.setup_database_connection(database_connection_string)

#     # Example query with visualization request
#     query = "Create a bar graph of order tables with order id and amount"
#     result = sql_agent.execute_query(query)

#     if isinstance(result, str) and result.startswith("data:image/png;base64,"):
#         # Display the image
#         try:
#             image_data = base64.b64decode(result.split(',')[1])
#             display(Image(data=image_data))
#         except Exception as e:
#             print(f"Error displaying image: {e}")
#     else:
#         print("Query Result:", result)