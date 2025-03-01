from setuptools import setup, find_packages

setup(
    name='talk2sql',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'uvicorn',
        'streamlit',
        'pydantic',
        'SQLAlchemy',
        'pymysql',
        'python-dotenv',
        'langchain',
        'langchain_community',
        'langchain_groq',
        'langgraph',
        'beautifulsoup4',
        'lxml'
    ],
)