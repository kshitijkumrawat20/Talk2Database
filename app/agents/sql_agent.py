
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END, START, MessagesState
from langchain_core.messages import AIMessage, ToolMessage, AnyMessage, HumanMessage
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from typing import Annotated, Literal, TypedDict, Any, Optional, Dict, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv
import os
from IPython.display import display, Image
import PIL
from langgraph.errors import GraphRecursionError
import io
from langchain_core.runnables.graph import MermaidDrawMethod
from langchain_google_genai import ChatGoogleGenerativeAI
from app.schemas.agent_state import DBQuery, SQLAgentState
from app.tools.database_tools import DatabaseTools
from app.utils.database_connection import DatabaseConnection
from langchain_core.prompts import PromptTemplate
from langchain_experimental.utilities import PythonREPL
load_dotenv()
import os
os.environ["GROQ_API_KEY"]=os.getenv("GROQ_API_KEY")
os.environ["GEMINI_API_KEY"]=os.getenv("GEMINI_API_KEY")


class SQLAgent:
    def __init__(self):
        
        # Initialize instance variables
        self.db = None
        self.toolkit = None
        self.tools = None
        self.list_tables_tool = None
        self.sql_db_query = None
        self.get_schema_tool = None
        self.repl = PythonREPL()
        self.code = None 

        # Setting up LLM
        # self.llm = ChatGroq(model=model,api_key = os.getenv("GROQ_API_KEY"))
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=os.environ["GEMINI_API_KEY"])
        # Register the tool method
        # self.query_to_database = self._create_query_tool()

    

    def setup_database_connection(self, connection_string: str):
        """Set up database connection and initialize tools"""
        try:
            # Initialize database connection
            # self.db = SQLDatabase.from_uri(connection_string)
            # print("Database connection successful!")
            self.db = DatabaseConnection(connection_string).db
            print("Database connection successful!")
            self.db_tools = DatabaseTools(db=self.db, llm=self.llm)

            try:
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

        def creating_sql_agent_chain():
            """Creating a sql agent chain"""

            # 4. check_query - Check if the query is correct
            # - Query checked: {check_query}
            # If query generated but not checked, respond with 'check_query'.
            #     If query checked but not executed, respond with 'execute_query'.
            print("Creating a sql agent chain")
            sql_agent_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a supervisor SQL agent managing tools to get the answer to the user's query.
                
                Based on the current state, decide which tool should be called next:
                1. list_table_tools - List all tables from the database
                2. get_schema - Get the schema of required tables
                3. generate_query - Generate a SQL query
                4. execute_query - Execute the query
                5. visualization_agent - Generate visualization if required
                6. response - Create response for the user

                Current state:
                - Tables listed: {tables_list}
                - Schema retrieved: {schema_of_table}
                - Query generated: {query_gen}
                - Query executed: {execute_query}
                - Visualization required: {visualization_required}
                - Visualization generated: {bs64_image}
                - Response created: {response_to_user}
                
                IMPORTANT DECISION LOGIC (follow this order strictly):
                1. If no tables are listed, respond with 'list_table_tools'.
                2. If tables are listed but no schema, respond with 'get_schema'.
                3. If schema exists but no query generated, respond with 'generate_query'.
                4. If query generated but not executed, respond with 'execute_query'.
                5. If query executed AND visualization is required AND no visualization generated, respond with 'visualization_agent'.
                6. If query executed AND (no visualization required OR visualization generated) AND no response created, respond with 'response'.
                7. If everything is complete, respond with 'DONE'.
                
                CRITICAL: Never call visualization_agent unless query has been executed first!
                CRITICAL: If visualization is already generated (bs64_image is not empty), do not call visualization_agent again!
                
                Respond with ONLY the tool name or 'DONE'.
                """),
                ("human", "{task}")
            ])
            return sql_agent_prompt | self.llm

        def sql_agent(state: SQLAgentState) -> Dict:
            """Agent decides which tool to call next"""
            messages = state["messages"]
            task = messages[-1].content if messages else "No task"
            
            # Store the original query in state if not already stored
            if not state.get("query"):
                state["query"] = task
            
            # Check if visualization is required based on query keywords
            visualization_keywords = ["graph", "chart", "plot", "visualize", "visualization", "bar chart", "pie chart", "histogram", "scatter plot", "line chart"]
            if not state.get("visualization_required") and any(keyword in task.lower() for keyword in visualization_keywords):
                state["visualization_required"] = True
                print(f"🎨 Visualization detected in query: {task}")
            
            # Check what's been completed (convert to boolean properly)
            tables_list = bool(state.get("tables_list", "").strip())
            schema_of_table = bool(state.get("schema_of_table", "").strip())
            query_gen = bool(state.get("query_gen", "").strip())
            # check_query = bool(state.get("check_query", "").strip())
            execute_query = bool(state.get("execute_query", "").strip())
            visualization_required = bool(state.get("visualization_required", False))
            bs64_image = bool(state.get("bs64_image", "").strip())
            response_to_user = bool(state.get("response_to_user", "").strip())
            
            # print(f"State check - Tables: {tables_list}, Schema: {schema_of_table}, Query: {query_gen}, Execute: {execute_query}, Viz Required: {visualization_required}, Viz Generated: {bs64_image}, Response: {response_to_user}")
            
            chain = creating_sql_agent_chain()
            decision = chain.invoke({
                "task": task,
                "tables_list": tables_list,
                "schema_of_table": schema_of_table,
                "query_gen": query_gen,
                # "check_query": check_query,
                "execute_query": execute_query,
                "visualization_required": visualization_required,
                "bs64_image": bs64_image,
                "response_to_user": response_to_user
            })
            decision_text = decision.content.strip().lower()
            print(f"Agent decision: {decision_text}")
            print(f"🔍 State check - Tables: {tables_list}, Schema: {schema_of_table}, Query: {query_gen}, Execute: {execute_query}, Viz Required: {visualization_required}, Viz Generated: {bs64_image}")
            
            # Add safety check to prevent calling visualization before execution
            if "visualization_agent" in decision_text and not execute_query:
                print("⚠️ WARNING: Trying to call visualization before execution. Forcing execute_query instead.")
                decision_text = "execute_query"
            
            if "done" in decision_text:
                next_tool = "end"
                agent_msg = "✅ SQL Agent: All tasks complete!"
            elif "list_table_tools" in decision_text:
                next_tool = "list_table_tools"
                agent_msg = "📋 SQL Agent: Listing all tables in database."
            elif "get_schema" in decision_text:
                next_tool = "get_schema"
                agent_msg = "📋 SQL Agent: Getting schema of tables."
            elif "generate_query" in decision_text:
                next_tool = "generate_query"
                agent_msg = "📋 SQL Agent: Generating SQL query."
            # elif "check_query" in decision_text:
            #     next_tool = "check_query"
            #     agent_msg = "📋 SQL Agent: Checking SQL query."
            elif "execute_query" in decision_text:
                next_tool = "execute_query"
                agent_msg = "📋 SQL Agent: Executing query."
            elif "visualization_agent" in decision_text:
                next_tool = "visualization_agent"
                agent_msg = "🎨 SQL Agent: Generating visualization."
            elif "response" in decision_text:
                next_tool = "response"
                agent_msg = "📋 SQL Agent: Creating response."
            else:
                next_tool = "end"
                agent_msg = "✅ SQL Agent: Task complete."
            
            return {
                "messages": [AIMessage(content=agent_msg)],
                "next_tool": next_tool,
                "current_task": task,
                "visualization_required": visualization_required  # Update state
            }
        def visualization_agent(state: SQLAgentState)-> Dict:
            """Creates a visualization agent that generates visualizations based on query results.

                Args:
                    state: The current state containing query execution results.

            Returns:
                Updated state with visualization.
            """
            print("🎨 Generating visualization...")
            # Implement the visualization logic here
            query_execution_results = state.get("execute_query", "")
            user_query = state.get("query", "")
            
            prompt = f"""Generate a visualization for the following query results: {query_execution_results} based on the query: {user_query}.
            Use appropriate libraries like matplotlib or seaborn to create the visualization.
            Ensure the visualization is clear and informative.
            always return the visualization as a base64 encoded string.
            Example generated code :
                import matplotlib.pyplot as plt
                import numpy as np
                import io
                import base64
                import matplotlib
                matplotlib.use('Agg')
                x = np.linspace(0, 10, 100)
                y = np.sin(x)
                plt.figure()
                plt.plot(x, y)
                plt.xlabel("X-axis")
                plt.ylabel("Y-axis")
                plt.title("Simple Sine Wave Plot")
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight')
                plt.close()
                png_bytes = buf.getvalue()
                base64_string = base64.b64encode(png_bytes).decode('utf-8')
                print(base64_string)
            """
            prompt_template=PromptTemplate.from_template(prompt)
            # Create the chain: PromptTemplate -> LLM
            llm_chain = prompt_template | self.llm
            response = llm_chain.invoke({
                "query": user_query,
                "query_execution_results": query_execution_results
            })
            self.code = response.content.removeprefix("```python").removesuffix("```")
            result = self.repl.run(self.code)
            print(result)
            print("✅ Visualization generated successfully!")
            
            return {
                "messages": [AIMessage(content="🎨 Visualization generated successfully!")],
                "bs64_image": result.strip() if result else "",
                "next_tool": "sql_agent"  # Go back to sql_agent to continue workflow
            }
    
        def router(state: SQLAgentState):
            """Route to the next node"""
            print("🔁 Entering router...")
            next_tool = state.get("next_tool", "")
            print(f"➡️ Next tool: {next_tool}")
            
            # Add loop counter to prevent infinite loops
            loop_count = state.get("loop_count", 0) + 1
            state["loop_count"] = loop_count
            
            if loop_count > 20:  # Safety limit
                print("⚠️ WARNING: Too many loops detected, ending workflow")
                return END
            
            if next_tool == "end" or state.get("task_complete", False):
                return END
            
            # Safety check: if visualization is already generated and we're trying to call it again
            if next_tool == "visualization_agent" and state.get("bs64_image", "").strip():
                print("⚠️ WARNING: Visualization already generated, routing to sql_agent instead")
                return "sql_agent"
            
            valid_tools = [
                "sql_agent", "list_table_tools", "get_schema", "generate_query",
                "execute_query", "response", "visualization_agent"
            ]
            
            return next_tool if next_tool in valid_tools else "sql_agent"
        
        # Create workflow
        workflow = StateGraph(SQLAgentState)

        # Add nodes
        workflow.add_node("sql_agent", sql_agent)
        workflow.add_node("list_table_tools", self.db_tools.list_table_tools)
        workflow.add_node("get_schema", self.db_tools.get_schema)
        workflow.add_node("generate_query", self.db_tools.generate_query)
        workflow.add_node("visualization_agent", visualization_agent)
        # workflow.add_node("check_query", self.db_tools.check_query)
        workflow.add_node("execute_query", self.db_tools.execute_query)
        workflow.add_node("response", self.db_tools.create_response)

        # Set entry point
        workflow.set_entry_point("sql_agent")

        # Add routing
        # for node in ["sql_agent", "list_table_tools", "get_schema", "generate_query", "check_query", "execute_query", "response"]:
        for node in ["sql_agent", "list_table_tools", "get_schema", "generate_query", "execute_query", "response","visualization_agent"]:
            workflow.add_conditional_edges(
                node,
                router,
                {
                    "sql_agent": "sql_agent",
                    "list_table_tools": "list_table_tools",
                    "get_schema": "get_schema",
                    "generate_query": "generate_query",
                    # "check_query": "check_query",
                    "execute_query": "execute_query",
                    "visualization_agent": "visualization_agent",
                    "response": "response",
                    END: END
                }
            )

        # Compile the graph
        self.app = workflow.compile()
        self.app.get_graph().draw_mermaid_png(output_file_path="sql_agent_workflow1.png", draw_method=MermaidDrawMethod.API)
                
                
  
    def is_query_relevant(self, query: str) -> bool:
        """Check if the query is relevant to the database using the LLM."""
        
        # Retrieve the schema of the relevant tables
        if self.db_tools.list_tables_tool:
            relevant_tables = self.db_tools.list_tables_tool.invoke("")
            # print(relevant_tables)
        table_list= relevant_tables.split(", ")
        print(table_list)
        # print(agent.get_schema_tool.invoke(table_list[0]))
        schema = ""
        for table in table_list:
            schema+= self.db_tools.get_schema_tool.invoke(table)

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

    ## called from the fastapi endpoint
    def execute_query(self, query: str):
        """Execute a query through the workflow"""
        if self.db is None:
            raise ValueError("Database connection not established. Please set up the connection first.")
        if self.app is None:
            raise ValueError("Workflow not initialized. Please set up the connection first.")
        # First, handle simple queries like "list tables" directly
        query_lower = query.lower()
        print(query_lower)
        if any(phrase in query_lower for phrase in ["list all the tables", "show tables", "name of tables",
                                                    "which tables are present", "how many tables", "list all tables"]):
            if self.db_tools.list_tables_tool:
                tables = self.db_tools.list_tables_tool.invoke("")
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
        # response = self.app.invoke({"messages": [HumanMessage(content=query, role="user")]})
        response = self.app.invoke({
        "messages": [HumanMessage(content=query)],
        "query": query
        })
        ## check if the response contains visualization agent call then return the visualization agent output
        if "visualization_agent" in response["messages"][-1].tool_calls:
            return response["messages"][-1].tool_calls["visualization_agent"]["args"]["bs64_image"]

        return response["messages"][-1].content

        # # More robust final answer extraction
        # if (
        #     response
        #     and response["messages"]
        #     and response["messages"][-1].tool_calls
        #     and len(response["messages"][-1].tool_calls) > 0
        #     and "args" in response["messages"][-1].tool_calls[0]
        #     and "final_answer" in response["messages"][-1].tool_calls[0]["args"]
        # ):
        #     return response["messages"][-1].tool_calls[0]["args"]["final_answer"]
        # else:
        #     return "Error: Could not extract final answer."

