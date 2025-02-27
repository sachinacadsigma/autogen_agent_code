from flask import Flask, request, jsonify, json
from langchain.chat_models import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import re
# Initialize the Azure OpenAI LLM
llm = AzureChatOpenAI(
    deployment_name="AllegisGPT-4o",
    model="gpt-4o",
    temperature=0,
    openai_api_key="2f6e41aa534f49908feb01c6de771d6b",
    openai_api_base="https://ea-oai-sandbox.openai.azure.com/",
    openai_api_version="2024-05-01-preview",
)

# Flask app initialization
app = Flask(__name__)

# Define the prompt template
template = """Answer the question based only on the following context:
{context}
Question: {question}
Answer: """

prompt = ChatPromptTemplate.from_template(template)

# Define the RAG chain
rag_chain = (
    {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Helper function to process text inputs into a single context string
def process_text_inputs(text_inputs):
    """
    Convert the list of dictionaries (text_inputs) into a single context string.
    """
    if isinstance(text_inputs, list) and all("text" in text for text in text_inputs):
        return "\n\n".join(text['text'] for text in text_inputs)
    raise ValueError("Invalid text_inputs format. Must be a list of dictionaries with 'text' keys.")

@app.route('/calculate_vacation_hours', methods=['POST'])
def calculate_vacation():
    # """
    # Constructs the vacation hours question and invokes the RAG chain.

    # Parameters:
    # - start_date: str, the hire date in "dd-MMMM-yyyy" format.
    # - end_date: str, the current date in "dd-MMMM-yyyy" format.
    # - regular_hours_worked: float, total regular hours worked.
    # - state: str, the state identifier ("non ca-il", "ca-il", etc.).
    # - used_vacations: float, vacation hours already used.

    # Returns:
    # - response: The result from `rag_chain.invoke`.
    # """
    data = request.get_json()

    try:
        # Extract inputs from the request payload
        start_date = data['start_date']
        end_date = data['end_date']
        regular_hours_worked = data['regular_hours_worked']
        state = data['state']
        used_vacations = float(data['used_vacations'])
        text_inputs = data['text_inputs']


            # Logic to set the value of state
        if state.upper() in ["CA", "IL"]:  # Check if input is either "CA" or "IL" (case insensitive)
            state = "CA-IL"
        else:
            state= "non CA-IL"

        # Convert text_inputs to context string
        context = process_text_inputs(text_inputs)

        # Formulate the question
    #     question = f"""
    # Non CA-IL
    # Weeks Accrued Equation
    # 1 Week = FLOOR(Hours / 400, 1) * 8
    # 2 Weeks = FLOOR(Hours / 200, 1) * 8
    # 3 Weeks = FLOOR(Hours / 133, 1) * 8
    # 4 Weeks = FLOOR(Hours / 100, 1) * 8

    # CA-IL
    # Weeks Accrued Rate In Agreement
    # Accrual Rate:
    # 1 Week = 8 for 400 → Hours * 0.02
    # 2 Weeks = 8 for 200 / 16 for 400 → Hours * 0.04
    # 3 Weeks = 24 for 400 / 8 for 133 → Hours * 0.06
    # 4 Weeks = 8 for 100 / 32 for 400 → Hours * 0.08

    # start_date = {start_date}
    # end_date = {end_date}
    # regular_hours_worked = {regular_hours_worked}
    # state = {state}
    # used_vacations = {used_vacations}
    # I want to know how many vacation hours are left as per agreement.
    # """




        question = f"""You are tasked with calculating vacation hours accrued and available for an employee based on the following details:

        Start Date: {start_date}
        Today’s Date: {end_date}
        Regular Hours Worked: {regular_hours_worked}
        State: {state}
        Used Vacation Hours: {used_vacations}
        Accrual Policies:

        For Non CA-IL:
        1 Week: FLOOR(Hours / 400, 1) * 8
        2 Weeks: FLOOR(Hours / 200, 1) * 8
        3 Weeks: FLOOR(Hours / 133, 1) * 8
        4 Weeks: FLOOR(Hours / 100, 1) * 8

        For CA-IL:
        1 Week = 8 for 400 → Hours * 0.02
        2 Weeks = 8 for 200 / 16 for 400 → Hours * 0.04
        3 Weeks = 24 for 400 / 8 for 133 → Hours * 0.06
        4 Weeks = 8 for 100 / 32 for 400 → Hours * 0.08
                                           
        
        Output Format:
        Always provide the following variables separately at the end for quick reference, along with a brief explanation of how they were calculated:

        Vacation Hours Accrued: Total hours accrued based on the applicable policy.
        Vacation Hours Available: Hours remaining after subtracting used vacation hours.
        Explanation:
        Explain the calculation of Vacation Hours Accrued based on the policy.
        Explain how Vacation Hours Available was calculated.
        End of Output:
        After all explanations, include the following variables separately for clarity:

        Vacation_Hours_Accrued = numerical value
        Vacation_Hours_Available = numerical value

        """

        # Use the RAG chain with the context and question
        result = rag_chain.invoke({"context": context, "question": question,})







    
        
        # Extract important values using regex
        important_values = {}
        patterns = {
            "regular_hours_worked": r"Regular Hours Worked: ([\d.]+)",
            "vacation_hours_accrued": r"Vacation_Hours_Accrued = ([\d.]+)",
            "vacation_hours_available": r"Vacation_Hours_Available = ([\d.]+)",
            "Used vacation hours": r"Used Vacation Hours: ([\d.]+)",
            "Remaining vacation hours": r"Remaining vacation hours: .*? = ([\d.]+)"
        }


        for key, pattern in patterns.items():
            match = re.search(pattern, result)
            if match:
                important_values[key] = float(match.group(1)) if '.' in match.group(1) else int(match.group(1))

        # Overwrite `result` with the reformatted version
        result1 = important_values

 




        # Return the result
        return jsonify({"answer": result,"important values":important_values}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
