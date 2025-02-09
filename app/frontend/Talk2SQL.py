import streamlit as st
import sqlite3
import requests
import hashlib
import os
from typing import Optional

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
    if result and result[0] == hash_password(password):
        return True
    return False

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

# Login/Signup page
def login_page():
    st.header('TALK2SQL')
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
    st.title('Database Connection')
    
    with st.form('connection_form'):
        connection_string = st.text_input('Connection String')
        submit = st.form_submit_button('Connect')
        
        if submit:
            try:
                response = requests.post(
                    'http://localhost:8000/api/v1/setup-connection',
                    json={'connection_string': connection_string}
                )
                if response.status_code == 200:
                    st.success('Database connected successfully!')
                    st.session_state.db_connected = True
                    st.session_state.current_page = 'chat'
                    st.rerun()
                else:
                    st.error(f'Connection failed: {response.text}')
            except requests.RequestException as e:
                st.error(f'Error connecting to backend: {str(e)}')

# Chat interface page
def chat_page():
    st.title('Chat Interface')
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Query input
    query = st.chat_input("Enter your query")
    
    if query:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": query})
        
        try:
            response = requests.post(
                'http://localhost:8000/api/v1/query',
                json={'query': query}
            )
            
            if response.status_code == 200:
                result = response.json()
                # Add assistant response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": result})
                st.rerun()
            else:
                st.error(f'Query failed: {response.text}')
        except requests.RequestException as e:
            st.error(f'Error connecting to backend: {str(e)}')

# Main app
def main():
    init_db()
    init_session_state()
    
    # Sidebar navigation
    if st.session_state.logged_in:
        st.sidebar.title('Navigation')
        pages = {
            'Database Connection': 'db_connection',
            'Chat Interface': 'chat'
        }
        
        selection = st.sidebar.radio('Go to', list(pages.keys()))
        st.session_state.current_page = pages[selection]
        
        st.sidebar.button('Logout', on_click=lambda: logout())
    
    # Page routing
    if not st.session_state.logged_in:
        login_page()
    elif st.session_state.current_page == 'db_connection':
        db_connection_page()
    elif st.session_state.current_page == 'chat':
        if not st.session_state.get('db_connected', False):
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
