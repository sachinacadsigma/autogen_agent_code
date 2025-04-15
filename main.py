import streamlit as st
import os
import glob
import pprint
from autogen import ConversableAgent, AssistantAgent
from autogen.coding import LocalCommandLineCodeExecutor

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

st.markdown("""
Welcome to **AutoCode**   
- Converts problem statements into Python code  
""")

problem_statement = st.text_area("📌 Enter your problem statement:", height=150)

# Track confirmation
generate_logic = st.session_state.get("generate_logic", False)
confirmed_api_logic = st.session_state.get("confirmed_api_logic", False)

# Check if API mentioned
api_detected = "api" in problem_statement.lower()

if st.button("🚀 Generate Code"):
    if not problem_statement.strip():
        st.warning("⚠️ Please enter a problem statement.")
    elif api_detected and not confirmed_api_logic:
        st.session_state.confirmed_api_logic = True
        st.warning("⚠️ APIs are currently out of scope. Do you still want to generate just the core logic (no API)?")
        st.session_state.show_confirm_button = True
    else:
        with st.spinner("🧠 Thinking and generating..."):
            try:
                response = generate_code(problem_statement)
                st.markdown("### ✅ Generated Python Code")
                st.code(response, language="python")
                cleanup_directory("./coding", keep_recent=False)
            except Exception as e:
                st.error(f"❌ Error: {e}")

# Confirm logic generation for API-based input
if st.session_state.get("show_confirm_button", False):
    if st.button("✅ Yes, generate core logic"):
        st.session_state.confirmed_api_logic = False
        st.session_state.show_confirm_button = False
        with st.spinner("🧠 Thinking and generating core logic..."):
            try:
                response = generate_code(problem_statement)
                st.markdown("### ✅ Generated Core Logic (API-free)")
                st.code(response, language="python")
                cleanup_directory("./coding", keep_recent=False)
            except Exception as e:
                st.error(f"❌ Error: {e}")
    elif st.button("❌ No, cancel"):
        st.session_state.confirmed_api_logic = False
        st.session_state.show_confirm_button = False
        st.info("API-based problem skipped. Please enter a new one.")
