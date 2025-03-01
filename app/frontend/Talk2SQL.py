import os
import streamlit as st
import sqlite3
import requests
import hashlib
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get backend URL from environment variable, fallback to localhost for local development
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')

logger.info(f"Using backend URL: {BACKEND_URL}")

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()

# Hash password
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# User authentication
def authenticate_user(username: str, password: str) -> bool:
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username=?', (username,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == hash_password(password)

# User registration
def register_user(username: str, password: str) -> bool:
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('INSERT INTO users VALUES (?, ?)', (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# Initialize session state
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'login'
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'db_connected' not in st.session_state:
        st.session_state.db_connected = False

# Login/Signup page
def login_page():
    st.set_page_config(page_title="Talk2SQL👨🏼‍💻🛢", layout="wide")
    st.header('Talk2SQL👨🏼‍💻🛢')
    st.title('Login / Sign Up')

    tab1, tab2 = st.tabs(['Login', 'Sign Up'])

    with tab1:
        with st.form('login_form'):
            username = st.text_input('Username')
            password = st.text_input('Password', type='password')
            submit = st.form_submit_button('Login')

            if submit:
                if authenticate_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.current_page = 'db_connection'
                    st.rerun()
                else:
                    st.error('Invalid username or password')

    with tab2:
        with st.form('signup_form'):
            new_username = st.text_input('Username')
            new_password = st.text_input('Password', type='password')
            confirm_password = st.text_input('Confirm Password', type='password')
            submit = st.form_submit_button('Sign Up')

            if submit:
                if new_password != confirm_password:
                    st.error('Passwords do not match')
                elif register_user(new_username, new_password):
                    st.success('Registration successful! Please login.')
                else:
                    st.error('Username already exists')

# Database connection page
def db_connection_page():
    st.set_page_config(page_title="Talk2SQL👨🏼‍💻🛢", layout="wide")
    st.header('Talk2SQL👨🏼‍💻🛢')
    st.title('Database Connection')

    # Sidebar content
    with st.sidebar:
        st.header("Sample Data")

        # Sample connection string
        st.subheader("Sample Connection String")
        st.sidebar.subheader("Sample Connection String")
        st.sidebar.code("mysql+pymysql://admin:9522359448@mydatabase.cf8u2cy0a4h6.us-east-1.rds.amazonaws.com:3306/mydb")

        st.sidebar.subheader("Sample Table")
        sample_data = pd.DataFrame({
            "id": [1, 2, 3, 4],
            "first_name": ["John", "Jane", "Tom", "Jerry"],
            "last_name": ["Doe", "Doe", "Smith", "Jones"],
            "email": ["johnD@abc.com", "JaneD@abc.com", "toms@abc.com", "Jerry@abc.com"],
            "hire_date": ["2020-01-01", "2020-05-01", "2020-03-01", "2020-02-01"],
            "salary": [50000, 60000, 70000, 80000]
        })
        st.sidebar.dataframe(sample_data)

        # Sample questions
        st.subheader("Sample Questions")
        questions = [
            "What is the email of John?",
            "What is the lastname of Tom?",
            "Hiredate of the Jerry?"
        ]
        for q in questions:
            st.markdown(f"- {q}")

        # Logout button
        st.divider()
        if st.button("Logout", type="primary"):
            logout()

    # Main content
    db_options = ["MySQL", "PostgreSQL"]
    db_type = st.selectbox("Select Database Type", db_options)
    placeholder_text = "" 
    if db_type == "PostgreSQL":
        placeholder_text = "postgresql://user:password@host:port/database"
    elif db_type == "MySQL":
        placeholder_text = "mysql+pymysql://user:password@host:port/database"

    with st.form('connection_form'):
        connection_string = st.text_input('Connection String', placeholder=placeholder_text, disabled=not db_type)
        submit = st.form_submit_button('Connect')

        if submit and connection_string:
            response = setup_connection(connection_string)
            if "error" in response:
                st.error(f'Connection failed: {response["error"]}')
            else:
                st.success('Database connected successfully!')
                st.session_state.db_connected = True
                st.session_state.current_page = 'chat'
                st.rerun()

def setup_connection(connection_string):
    try:
        api_url = f"{BACKEND_URL}/api/v1/setup-connection"
        logger.info(f"Making request to: {api_url}")
        
        response = requests.post(
            api_url,
            json={"connection_string": connection_string},
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"Response status: {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to backend: {str(e)}")
        return {"error": str(e)}

# Chat interface page
def chat_page():
    st.set_page_config(page_title="Talk2SQL👨🏼‍💻🛢", layout="wide")
    st.title('Chat Interface')

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    query = st.chat_input("Enter your query")

    if query:
        st.session_state.chat_history.append({"role": "user", "content": query})

        try:
            response = requests.post(
                'http://localhost:8000/api/v1/query',
                json={'query': query}
            )

            if response.status_code == 200:
                result = response.json().get("result", "No result")
                st.session_state.chat_history.append({"role": "assistant", "content": result})
                st.rerun()
            else:
                st.error(f'Query failed: {response.text}')
        except requests.RequestException as e:
            st.error(f'Error connecting to backend: {str(e)}')

    if st.button("End Chat"):
        st.session_state.current_page = 'db_connection'
        st.rerun()

# Main app
def main():
    init_db()
    init_session_state()

    if not st.session_state.logged_in:
        login_page()
    elif st.session_state.current_page == 'db_connection':
        db_connection_page()
    elif st.session_state.current_page == 'chat':
        if not st.session_state.db_connected:
            st.error('Database not connected. Redirecting to Database Connection page')
            st.session_state.current_page = 'db_connection'
            st.rerun()
        chat_page()

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.current_page = 'login'
    st.session_state.db_connected = False
    st.rerun()

if __name__ == '__main__':
    main()