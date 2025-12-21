"""
SQLAgent singleton instance module.
This creates and maintains a single instance of the SQLAgent class
that can be imported and used throughout the application.
"""
# from app.services.sql_agent import SQLAgent
from app.agents.sql_agent_v2 import SQLAgent
# Create a singleton instance
sql_agent = SQLAgent()