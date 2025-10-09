## creating an class design first 

## top view
Database connection  --> Initialize tools --> Inititalize workflow --> compile into a app(with memory) --> using app into fastapi 

## detailed view
1. Database Connection(utils) class (formed) includes creation of database tools as well 
2. Database tools (formed) includes 
    - ListTablesTool
    - QueryCheckerTool
    - QuerySQLDataBaseTool
    - GetSchemaTool

3. Workflow class or sql_agent_class 

## how data flows between the classes 

1. database connection class creates a database connection and initializes the tools 
2. this tools are then passed to the database tools class to wrap up into functions so that we can create a langgraph node of them 
3. the workflow class or sql_agent_class takes in the tools and llm to create a workflow and compile it into an app