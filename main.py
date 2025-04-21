import streamlit as st
import psycopg2
from autogen import ConversableAgent, AssistantAgent
from autogen.coding import LocalCommandLineCodeExecutor
import os
import glob
import pprint

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host="aws-0-ap-southeast-1.pooler.supabase.com",
        port="5432",
        dbname="postgres",
        user="postgres.gdpjagpvnnvazhhhgpzc",
        password="1234"
    )
    return conn

# Executor setup
executor = LocalCommandLineCodeExecutor(timeout=60, work_dir="coding")

# Azure OpenAI config
azure_deployment_name = "AllegisGPT-4o"
model = "gpt-4"
temperature = 0
openai_api_key = "2f6e41aa534f49908feb01c6de771d6b"
openai_api_base = "https://ea-oai-sandbox.openai.azure.com/"
openai_api_version = "2024-05-01-preview"

llm_config = {
    "api_type": "azure",
    "api_version": openai_api_version,
    "base_url": openai_api_base,
    "api_key": openai_api_key,
    "model": azure_deployment_name, # Set model to deployment name
    "temperature": temperature,
}

# Agents
code_executor_agent = ConversableAgent(
    name="code_executor_agent",
    llm_config=False,
    code_execution_config={"executor": executor},
    human_input_mode="NEVER"
)

code_writer_agent = AssistantAgent(
    name="code_writer_agent",
    llm_config=llm_config,
    code_execution_config=False,
    human_input_mode="NEVER",
)

# Helper: Parse chat history
def process_chat_history(chat_history):
    x = pprint.pformat(chat_history)
    parser_agent = ConversableAgent(
        name="chatbot",
        llm_config=llm_config,
        human_input_mode="NEVER",
        system_message="""You are an agent who parses the chat history and returns the most recent code,
        requirements, and description. Output must include 'code', 'requirements', and 'description'. The code should be clean and Pythonic.""" 
    )
    reply = parser_agent.generate_reply(messages=[{"content": x, "role": "user"}])
    if isinstance(reply, list) and reply:
        return reply[-1].get("content", reply[-1]) if isinstance(reply[-1], dict) else reply[-1]
    return reply

# Main Code Generator
def generate_code(problem_statement):
    refined_prompt = f"""
    APIs are not in scope. If the user mentions APIs, generate only the core logic, without any Flask or FastAPI or routing code.
    If the problem is complex, break it down into helper functions.
    Only return logic, no API code, no UI code.

    Problem:
    {problem_statement}
    """
    chat = code_executor_agent.initiate_chat(code_writer_agent, message=refined_prompt)
    return process_chat_history(chat)

# Cleanup
def cleanup_directory(directory, keep_recent=False):
    try:
        files = glob.glob(os.path.join(directory, "*.py"))
        if keep_recent:
            file_times = sorted([(f, os.path.getmtime(f)) for f in files], key=lambda x: x[1])
            files_to_delete = [f for f, _ in file_times[:-1]]
        else:
            files_to_delete = files
        for file_path in files_to_delete:
            os.remove(file_path)
    except Exception as e:
        st.error(f"Cleanup failed: {e}")

# Streamlit UI
st.set_page_config(page_title="AutoCode", layout="wide")
st.title("AutoCode - Your Smart Coding Assistant")

st.markdown("""Welcome to *AutoCode*   
- Converts problem statements into Python code""")

# User login
def user_login(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    if user:
        return True
    return False

# Register new user
def register_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()

# UI for login
username = st.text_input("Username")
password = st.text_input("Password", type="password")

# Login form
login_button = st.button("Login")
if login_button:
    if user_login(username, password):
        st.session_state.username = username
        st.success("Login successful!")
    else:
        st.error("Invalid credentials.")

# Sign up form
sign_up_button = st.button("Sign Up")
if sign_up_button:
    if username and password:
        register_user(username, password)
        st.success("Sign up successful! You can now log in.")
    else:
        st.error("Please enter a valid username and password to sign up.")

# Problem statement and code generation
if 'username' in st.session_state:
    problem_statement = st.text_area("📌 Enter your problem statement:", height=150)

    if st.button("🚀 Generate Code"):
        if not problem_statement.strip():
            st.warning("⚠️ Please enter a problem statement.")
        else:
            with st.spinner("🧠 Thinking and generating..."):
                try:
                    response = generate_code(problem_statement)
                    st.markdown("### ✅ Generated Python Code")
                    st.code(response, language="python")
                    # Save to log table
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO log (username, prompt, output) VALUES (%s, %s, %s)", 
                                   (st.session_state.username, problem_statement, response))
                    conn.commit()
                    cleanup_directory("./coding", keep_recent=False)
                except Exception as e:
                    st.error(f"❌ Error: {e}")

   # Feedback (Thumbs up/down)
thumbs = st.radio("Do you like the generated code?", ["👍", "👎"])
if thumbs:
    feedback_value = "positive" if thumbs == "👍" else "negative"
    comments = ""
    if feedback_value == "negative":
        comments = st.text_area("Please provide a reason for thumbs down:", "")
    
    if st.button("Submit Feedback"):
        # Save feedback in the same log table
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE log SET feedback = %s, comments = %s WHERE username = %s AND prompt = %s", 
                (feedback_value, comments, st.session_state.username, problem_statement)
            )
            conn.commit()
            st.success("Feedback submitted!")
        except Exception as e:
            st.error(f"Failed to submit feedback: {e}")
else:
    st.info("Please log in to start generating code.")
