## creating database tools 
from langchain_core.tools import tool
from app.schemas.agent_state import SQLAgentState
from typing import Dict
from langchain_core.messages import AIMessage
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from app.schemas.agent_state import DBQuery
from langchain_core.prompts import ChatPromptTemplate

class DatabaseTools:
    def __init__(self,db = None, llm = None):
        self.db = db 
        self.llm = llm
        # self._create_query_tool = self._create_query_tool()
        self.tools = self.get_all_tools()
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
    # @tool
    # def _create_query_tool(self):
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
    def list_tables(self) -> Dict:
            """List all the tables"""
            tables_list = self.list_tables_tool.invoke("")
            print(f"Tables found: {tables_list}")
            return tables_list
    
    def get_schema(self, table_name: list[str]) -> Dict:
            """Get the schema of required tables"""
            print("📘 Getting schema...")
            tables_list = self.list_tables_tool.invoke("")
            if any(table not in tables_list for table in table_name):
                 return "Table not exits in database"
            
            tables = [table.strip() for table in tables_list.split(",")]
            required_schema = ""
            
            for table in tables:
                try:
                    schema = self.get_schema_tool.invoke(table)
                    required_schema += f"\nTable: {table}\n{schema}\n"
                except Exception as e:
                    print(f"Error getting schema for {table}: {e}")
            
            return required_schema
    

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
            
    
    def execute_query(self,query: str) -> Dict:
            """Execute the SQL query
            
            Arguments:
            query -- The SQL query to execute

            returns:
            execution results
            """
            
            try:
                results = self.query_tool.invoke(query)
                print(f"Query results: {results}")
                return results
            except Exception as e:
                print(f"Error executing query: {e}")
                return "Query execution failed."
            
    def get_all_tools(self):
         return [self.list_tables, self.get_schema, self.execute_query]
            