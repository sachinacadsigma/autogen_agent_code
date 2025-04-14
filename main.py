import streamlit as st
import os
import glob
import shutil
import datetime
import pprint
from autogen import ConversableAgent, AssistantAgent
from autogen.coding import LocalCommandLineCodeExecutor

# Initialize Code Executor
executor = LocalCommandLineCodeExecutor(
    timeout=60,
    work_dir="coding",
)


# Hardcoded credentials (VERY STRONGLY DISCOURAGED for production)
azure_deployment_name = "AllegisGPT-4o"  # Replace with your deployment name
model = "gpt-4"  # Replace with your base model name (e.g. gpt-4, gpt-3.5-turbo)
temperature = 0
openai_api_key = "2f6e41aa534f49908feb01c6de771d6b"  # Replace with your actual API key
openai_api_base = "https://ea-oai-sandbox.openai.azure.com/"  # Replace with your Azure endpoint URL
openai_api_version = "2024-05-01-preview"  # Replace with your API version

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

def process_chat_history(chat_history):
    """
    Processes the chat history to extract final code and explanation.
    """
    x = pprint.pformat(chat_history)

    parser_agent = ConversableAgent(
        name="chatbot",
        llm_config=llm_config,
        human_input_mode="NEVER",
        system_message="""You are an agent who will parse the given chat history and return the most recent code
        along with a neat description and requirements of the code. Answer format should include fields: 
        code (neatly indented), requirements, and description."""
    )

    reply = parser_agent.generate_reply(messages=[{"content": x, "role": "user"}])

    if isinstance(reply, list) and reply:
        return reply[-1].get("content", reply[-1]) if isinstance(reply[-1], dict) else reply[-1]
    return reply

def generate_function_then_api(problem_statement):
    """
    First generate internal function logic, test it, then wrap it in a Flask API.
    Returns both blocks: function + Flask API.
    """
    # PHASE 1: Generate Internal Function Only
    logic_prompt = f"""
    Create only the core function logic for the following problem.
    Do NOT create an API. Just return the function. Do not wrap it in main or add UI code.

    Problem: {problem_statement}
    """
    logic_chat = code_executor_agent.initiate_chat(code_writer_agent, message=logic_prompt)
    logic_response = process_chat_history(logic_chat)

    # PHASE 2: Wrap in API
    api_prompt = f"""
    Now wrap the following function into a Flask API. Return only two sections:
    1. Internal Function (clean and tested)
    2. Flask API Code

    python
    {logic_response}
    
    """
    api_chat = code_writer_agent.initiate_chat(code_writer_agent, message=api_prompt)
    api_response = process_chat_history(api_chat)

    return {
        "function_logic": logic_response,  # Return function logic as a separate part
        "flask_api_code": api_response,    # Return Flask API code
    }


def generate_regular_code(problem_statement):
    """
    Default code generation flow when API is not mentioned.
    """
    chat_result = code_executor_agent.initiate_chat(code_writer_agent, message=problem_statement)
    return process_chat_history(chat_result)

def cleanup_directory(directory, keep_recent=False):
    """Cleans up a directory, optionally keeping the most recent file."""
    try:
        files = glob.glob(os.path.join(directory, "*.py"))
        if not files:
            return

        if keep_recent:
            file_times = sorted([(f, os.path.getmtime(f)) for f in files], key=lambda x: x[1])
            files_to_delete = [f for f, _ in file_times[:-1]]
        else:
            files_to_delete = files

        for file_path in files_to_delete:
            os.remove(file_path)
    except Exception as e:
        st.error(f"Error during cleanup: {e}")

# Streamlit UI
st.title("AutoCode")
st.markdown("""
Hi! I'm AutoCode, your personal coding assistant.
**Happy coding!** 
""")

problem_statement = st.text_area("Enter your problem statement:", height=150)

if st.button("Generate Code"):
    if problem_statement:
        with st.spinner("Working on it..."):
            try:
                # Check if user asked for API
                if "api" in problem_statement.lower():
                    response = generate_function_then_api(problem_statement)

                    # Display the logic and Flask API code separately
                    st.markdown("### ✅ Generated Internal Function Logic")
                    st.code(response["function_logic"], language="python")

                    st.markdown("### ✅ Generated Flask API Code")
                    st.code(response["flask_api_code"], language="python")
                else:
                    response = generate_regular_code(problem_statement)
                    st.markdown("### ✅ Generated Code")
                    st.code(response, language="python")

                cleanup_directory("./coding", keep_recent=False)
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
    else:
        st.warning("⚠️ Please enter a problem statement.")
