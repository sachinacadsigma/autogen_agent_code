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
    "azure_endpoint": openai_api_base,
    "api_key": openai_api_key,
    "model": azure_deployment_name, # Set model to deployment name
    "temperature": temperature,
}

def generate_chat_history(problem_statement):
    """
    Executes code based on the given problem statement using AutoGen agents and returns the chat history.
    """
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

    chat_result = code_executor_agent.initiate_chat(
        code_writer_agent,
        message=problem_statement,
    )

    return chat_result.chat_history

def process_chat_history(chat_history):
    """
    Processes the chat history to extract the most recent code details.
    """
    x = pprint.pformat(chat_history)

    agent = ConversableAgent(
        name="chatbot",
        llm_config=llm_config,
        human_input_mode="NEVER",
        system_message="""You are an agent who will parse the given chat history and return the most recent code
        along with a neat description and requirements of the code. Answer format should include fields: code (neatly indented), requirements, and description."""
    )

    reply = agent.generate_reply(
        messages=[{"content": x, "role": "user"}]
    )

    # Ensure proper extraction of response
    if isinstance(reply, list) and reply:
        return reply[-1].get("content", reply[-1]) if isinstance(reply[-1], dict) else reply[-1]
    return reply

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
st.title("Code Generation and Analysis")

problem_statement = st.text_area("Enter your problem statement:", height=150)

if st.button("Generate and Process"):
    if problem_statement:
        with st.spinner("Generating and processing..."):
            try:
                chat_history = generate_chat_history(problem_statement)
                response = process_chat_history(chat_history)
                st.write(response)

                output_directory = "./coding"
                cleanup_directory(output_directory, keep_recent=False)
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a problem statement.")
