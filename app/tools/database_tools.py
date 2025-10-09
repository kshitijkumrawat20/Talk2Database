## creating database tools 
from langchain_core.tools import tool
from app.schemas.agent_state import SQLAgentState
from typing import Dict
from langchain_core.messages import AIMessage, HumanMessage
from app.utils.database_connection import DatabaseConnection
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from app.schemas.agent_state import DBQuery
from langchain_core.prompts import ChatPromptTemplate

class DatabaseTools:
    def __init__(self,db = None, llm = None):
        self.db = db 
        self.llm = llm
        self._create_query_tool = self._create_query_tool()
        try:
                # Initialize toolkit and tools
                self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
                self.tools = self.toolkit.get_tools()
                for tool in self.tools:
                    print(f"Initialized tool: {tool.name}")

                # Create instances of the tools
                self.list_tables_tool = next((tool for tool in self.tools if tool.name == "sql_db_list_tables"), None)
                self.query_tool = next((tool for tool in self.tools if tool.name == "sql_db_query"), None)
                self.get_schema_tool = next((tool for tool in self.tools if tool.name == "sql_db_schema"), None)
                self.query_checker_tool = next((tool for tool in self.tools if tool.name == "sql_db_query_checker"), None)
                if not all([self.list_tables_tool, self.query_tool, self.get_schema_tool, self.query_checker_tool]):
                    raise ValueError("Failed to initialize one or more required database tools")

                # # Initialize workflow and compile it into an app
                # self.initialize_workflow()
                
        except Exception as e:
            print(f"Error initializing tools and workflow: {str(e)}")
            raise ValueError(f"Failed to initialize database tools: {str(e)}")
    
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

    def list_table_tools(self, state: SQLAgentState = None) -> Dict:
            """List all the tables"""
            tables_list = self.list_tables_tool.invoke("")
            print(f"Tables found: {tables_list}")
            return {
                "messages": [AIMessage(content=f"Tables found: {tables_list}")],
                "tables_list": tables_list,
                "next_tool": "sql_agent"
            }
    
    def get_schema(self,state: SQLAgentState) -> Dict:
            """Get the schema of required tables"""
            print("📘 Getting schema...")
            tables_list = state.get("tables_list", "")
            if not tables_list:
                tables_list = self.list_tables_tool.invoke("")
            
            tables = [table.strip() for table in tables_list.split(",")]
            full_schema = ""
            
            for table in tables:
                try:
                    schema = self.get_schema_tool.invoke(table)
                    full_schema += f"\nTable: {table}\n{schema}\n"
                except Exception as e:
                    print(f"Error getting schema for {table}: {e}")
            
            print(f"📘 Schema collected for tables: {tables}")
            return {
                "messages": [AIMessage(content=f"Schema retrieved: {full_schema}")],
                "schema_of_table": full_schema,
                "tables_list": tables_list,
                "next_tool": "sql_agent"
            }
    def generate_query(self, state: SQLAgentState) -> Dict:
            """Generate a SQL Query according to the user query"""
            schema = state.get("schema_of_table", "")
            human_query = state.get("query", "")
            tables = state.get("tables_list", "")
            
            print(f"Generating query for: {human_query}")
            
            generate_query_system_prompt = """You are a SQL expert that generates precise SQL queries based on user questions.
            
            You will be provided with:
            - User's question
            - Available tables
            - Complete schema information
            
            Generate a SQL query that:
            - Uses correct column names from schema
            - Properly joins tables if needed
            - Includes appropriate WHERE clauses
            - Uses proper aggregation functions when needed
            
            Respond ONLY with the SQL query. Do not explain."""
            
            combined_input = f"""
            User Question: {human_query}
            Tables: {tables}
            Schema: {schema}
            """
            
            generate_query_prompt = ChatPromptTemplate.from_messages([
                ("system", generate_query_system_prompt),
                ("human", "{input}")
            ])
            
            try:
                formatted_prompt = generate_query_prompt.invoke({"input": combined_input})
                generate_query_llm = self.llm.with_structured_output(DBQuery)
                result = generate_query_llm.invoke(formatted_prompt)
                
                print(f"✅ Query generated: {result.query}")
                return {
                    "messages": [AIMessage(content=f"Query generated: {result.query}")],
                    "query_gen": result.query,
                    "next_tool": "sql_agent"
                }
            except Exception as e:
                print(f"❌ Failed to generate query: {e}")
                return {
                    "messages": [AIMessage(content="⚠️ Failed to generate SQL query.")],
                    "query_gen": "",
                    "next_tool": "sql_agent"
                }
            
    def check_query(self,state: SQLAgentState) -> Dict:
            """Check if the query is correct"""
            query = state.get("query_gen", "")
            print(f"Checking query: {query}")
            
            if not query:
                return {
                    "messages": [AIMessage(content="No query to check")],
                    "check_query": "",
                    "next_tool": "sql_agent"
                }
            
            try:
                checked_query = self.query_checker_tool.invoke(query)
                ## if checked query contains ``` anywhere remove it 
                if "```" in checked_query:
                    checked_query = checked_query.replace("```", "")
                print(f"Query checked: {checked_query}")
                return {
                    "messages": [AIMessage(content=f"Query checked: {checked_query}")],
                    "check_query": checked_query if checked_query else query,
                    "next_tool": "sql_agent"
                }
            except Exception as e:
                print(f"Error checking query: {e}")
                return {
                    "messages": [AIMessage(content="Query check failed, using original query")],
                    "check_query": query,
                    "next_tool": "sql_agent"
                }
            
    def execute_query(self,state: SQLAgentState) -> Dict:
            """Execute the SQL query"""
            query = state.get("check_query", "") or state.get("query_gen", "")
            print(f"Executing query: {query}")
            
            if not query:
                return {
                    "messages": [AIMessage(content="No query to execute")],
                    "execute_query": "",
                    "next_tool": "sql_agent"
                }
            
            try:
                results = self.query_tool.invoke(query)
                print(f"Query results: {results}")
                return {
                    "messages": [AIMessage(content=f"Query executed successfully: {results}")],
                    "execute_query": results,
                    "next_tool": "sql_agent"
                }
            except Exception as e:
                print(f"Error executing query: {e}")
                return {
                    "messages": [AIMessage(content=f"Query execution failed: {e}")],
                    "execute_query": "",
                    "next_tool": "sql_agent"
                }
    def create_response(self,state: SQLAgentState) -> Dict:
            """Create a final response for the user"""
            print("Creating final response...")
            
            query = state.get("check_query", "") or state.get("query_gen", "")
            result = state.get("execute_query", "")
            human_query = state.get("query", "")
            
            response_prompt = f"""Create a clear, concise response for the user based on:
            
            User Question: {human_query}
            SQL Query: {query}
            Query Result: {result}
            
            Provide a natural language answer that directly addresses the user's question. Make sure to provide only answer to human question, no any internal process results and explaination, just answer related to the human query."""
            
            try:
                response = self.llm.invoke([HumanMessage(content=response_prompt)])
                print(f"Response created: {response.content}")
                
                return {
                    "messages": [response],
                    "response_to_user": response.content,
                    "next_tool": "sql_agent",
                    "task_complete": True
                }
            except Exception as e:
                print(f"Error creating response: {e}")
                return {
                    "messages": [AIMessage(content="Failed to create response")],
                    "response_to_user": "",
                    "next_tool": "sql_agent",
                    "task_complete": True
                }