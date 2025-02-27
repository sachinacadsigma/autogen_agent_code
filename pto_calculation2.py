

from flask import Flask, request, jsonify, json
from langchain.chat_models import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import re
import os
from datetime import datetime
import logging



global vacation_hours_available
vacation_hours_available=None
# Initialize the Azure OpenAI LLM
llm = AzureChatOpenAI(
    deployment_name="AllegisGPT-4o",
    model="gpt-4o",
    temperature=0,
    openai_api_key="2f6e41aa534f49908feb01c6de771d6b",
    openai_api_base="https://ea-oai-sandbox.openai.azure.com/",
    openai_api_version="2024-05-01-preview",
)
# query_engine = index.as_query_engine()


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



import json
import re

# Function to remove markdown formatting, including numbered lists
def remove_markdown(text):
    # Remove links and images (e.g., [text](url))
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    # Remove inline code (e.g., `code`)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    # Remove bold or italic (e.g., **bold**, *italic*, _italic_)
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
    # Remove headings (e.g., # Heading)
    text = re.sub(r'^\s*#+\s*', '', text)
    # Remove unordered list markers (e.g., -, *, +)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    # Remove blockquotes (e.g., > text)
    text = re.sub(r'^\s*>+\s*', '', text, flags=re.MULTILINE)
    # Remove numbered list markers (e.g., 1., 2., 3.)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    return text.strip()

def remove_newlines(input_text):
    # Remove all newlines in the text
    cleaned_text = re.sub(r'\n', ' ', input_text)
    return cleaned_text

# # Function to split sentences and format step4
# def format_data(input_data):
#     formatted = {}
    
#     # Split sentences for step1, step2, and step3
#     for key in ["leaves_policy_breakdown", "leaves_accrued_calculation"]:
#         # Remove markdown and split sentences
#         clean_text = remove_markdown(input_data[key])
#         formatted[key] = [sentence.strip() for sentence in clean_text.replace("\n", " ").split(". ") if sentence.strip()]
    
#     # Format step4 with variables and sentences
#     step4_sentences = [sentence.strip() for sentence in remove_markdown(input_data["leaves_available_calculation"]).replace("\n", " ").split(". ") if sentence.strip()]
#     formatted["leaves_available_calculation"] = step4_sentences  # Directly assign the array of strings
    
#     # Extract vacation_hours_available from the step4_sentences
#     vacation_hours_available = None
#     for sentence in step4_sentences:
#         match = re.search(r"\"?available vacation hours\"?\s*[:=]\s*(-?\d+(?:\.\d+)?)", sentence)
#         if match:
#             vacation_hours_available = float(match.group(1))
#             break
    
#     # Check if vacation_hours_available was found; if not, raise an error
#     # if vacation_hours_available is None:
#     #     # raise ValueError("Error: 'vacation_hours_available' could not be found in the input data.")
#         # return vacation_hours_available
    
#     # # Add vacation_hours_available to the formatted output
#     formatted["vacation_hours_available"] = vacation_hours_available
    
#     return formatted








def log_api_response(formatted_data, leaves_policy, raw_output_data):
    # Generate a new timestamp for each API call
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    folder_path = "output_logs"
    os.makedirs(folder_path, exist_ok=True)
    log_file_path = os.path.join(folder_path, f"{timestamp}.log")

    # Create a new logger instance
    logger = logging.getLogger(f"Logger_{timestamp}")  # Unique logger per call
    logger.setLevel(logging.INFO)

    # Create file handler
    file_handler = logging.FileHandler(log_file_path)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Clear previous handlers and add the new one
    if logger.hasHandlers():
        logger.handlers.clear()  # Remove any existing handlers

    logger.addHandler(file_handler)

    # API response to be logged
    api_response = {
        "output": formatted_data,
        "leaves_policy": leaves_policy,
        "prompt outputs": raw_output_data
    }

    # Log the JSON data
    logger.info(json.dumps(api_response, indent=4))

    # Remove handlers to prevent duplicate logs
    logger.removeHandler(file_handler)
    file_handler.close()

# Helper function to process text inputs into a single context string
def process_text_inputs(text_inputs):
    """
    Convert the list of dictionaries (text_inputs) into a single context string.
    """
    if isinstance(text_inputs, list) and all("text" in text for text in text_inputs):
        return "\n\n".join(text['text'] for text in text_inputs)
    raise ValueError("Invalid text_inputs format. Must be a list of dictionaries with 'text' keys.")



def extract_vacation_section(input_text, llm):
    # Ensure the input_text is clean and doesn't have extra newlines or special characters
    input_text = input_text.replace('\n', ' ')  # Replace newlines with spaces to avoid issues

    vacation_prompt = f"""
    Task:Extract the content from the vacation_policy_unfiltered which has the information only regarding vacation policy. Extract the sentences having the word vacation or information in and around vacation policy. 1. vacation_policy

    Example 1:
    vacation_policy_unfiltered: required by applicable law.  Client-observed holidays, shutdowns, and regularly scheduled days off shall not be considered  as time worked for purposes of qualifying for premium rate compensation. Except as specifically set forth in this Agreement, you acknowledge and agree that you are not entitled to any other  compensation or benefits (including, but not limited to, vacation or personal leave) from Actalent, Inc. or Client.  Actalent, Inc. agrees to compensate you for 6 legal holidays, those being New Year Day, Memorial Day, July 5.   -Holiday Fourth, Labor Day, Thanksgiving Day, Christmas Day after thirty (30) days of continuous employment on the Assignment.  You are not eligible to earn or accrue any vacation until you have completed 400 regular hours of service 6.  - Vacation  within six months at the initial commencement of employment on this Assignment.  After this initial period of employment,  ✔  AG Onboarding - 00042331974179141 - Generated: 05/31/2024 10:21 AM Actalent, Inc. agrees that you have earned or are eligible to earn 8 hours, for every 400 Regular hours (not including  overtime) of compensated service in a continuous six (6) month period.  Accrued but unused vacation hours may be carried over into the next calendar year, however the maximum amount of accrued vacation may not exceed one hundred and  sixty (160) hours at any given time.  Unless state or applicable law requires otherwise, unused accrued vacation will not be  paid out upon termination and vacation will not accrue on a pro-rata basis. If you work in a sick leave jurisdiction, your eligibility and ability to earn, accrue, and use paid sick leave is 7.  - Sick Leave  governed by applicable law, and you will receive additional information regarding the applicable sick leave policy. Any business related expenses for which you are eligible and request reimbursement must be 8.   - Business Expenses approved in writing by Client and must be substantiated with legible, itemized receipts. Original receipts must be physically  turned in to the Actalent, Inc. office or scanned and submitted electronically to your local Actalent, Inc. representative. Any  receipts turned in after 90 days of transaction will be deemed untimely and not paid. Any expenses submitted to Actalent,  Inc. without itemized receipts will not be reimbursed by Actalent, Inc.. If you would like a copy of the Actalent, Inc. Contract  Employee expense reimbursement policy, please contact your Actalent, Inc. representative. You agree not to disclose to anyone, either during or after your employment with Actalent, Inc., any 9.  - Confidentiality confidential or proprietary information of any kind obtained by you as a result of your employment without the written  consent of executive officers of both the Client and Actalent, Inc., and you further agree that on leaving the employment of

    Extracted Information:You are not eligible to earn or accrue any vacation until you have completed 400 regular hours of service 6.Vacation  within six months at the initial commencement of employment on this Assignment.After this initial period of employment,  ✔  AG Onboarding - 00042331974179141 - Generated: 05/31/2024 10:21 AM Actalent, Inc. agrees that you have earned or are eligible to earn 8 hours, for every 400 Regular hours (not including  overtime) of compensated service in a continuous six (6) month period.Accrued but unused vacation hours may be carried over into the next calendar year, however the maximum amount of accrued vacation may not exceed one hundred and  sixty (160) hours at any given time.Unless state or applicable law requires otherwise, unused accrued vacation will not be  paid out upon termination and vacation will not accrue on a pro-rata basis
    

    Example 2:Holiday - ACTALENT agrees to compensate you for 10 legal holidays, those being New Year’s Day, Martin Luther King Day, President's Day, Memorial Day,, Independence Day,, Labor Day, Thanksgiving,, Christmas, Day after Thanksgiving and Day  after Christmas, after thirty (30) days of continuous employment on the Assignment.  Vacation –Employee earns one day (8 hours) of paid vacation for every 400 Regular hours (not including overtime) of  compensated service up to a maximum of forty (40) hours per year. Unless state or applicable law requires otherwise,  Employee may carry over up to forty (40) hours of accrued unused vacation time to the following year, up to forty (40) hours  of accrued unused vacation time will be paid out.  since you are a common law employee of ACTALENT, and not the Client, you are not eligible for any benefit programs that  may be provided by Client during your Assignment.   By electing to participate in our benefit programs, you authorize  ACTALENT to deduct your portion of the applicable costs directly from your paycheck.  Acknowledgment of Employment Relationship  - In addition to the rules, regulations and policies of ACTALENT, you  agree to be bound by any applicable rules, regulations or policies established by the Client wherever you perform services  under this Agreement.  You recognize and agree that you are an employee of ACTALENT, and you will look solely to  ACTALENT for all employee benefits in connection with your employment under this Agreement.  You hereby waive any  right you have or may have against the Client for benefits arising out of or resulting from employment hereunder, including,  without limitation, rights under any me dical/benefit plan, pension plan or vacation/holiday plan regardless of the length of  Assignment.   Assignment of Claims - In the event Client has filed for bankruptcy or indicated an intent to file for bankruptcy, you hereby  assign to ACTALENT any and all claims you have against the Client for any wages earned and owed to you in connection with  the  work you performed on the Assignment, effective upon payment by ACTALENT to you of such amounts, which assignment  shall be considered as in exchange for ACTALENT’s payment of such amounts.  Limitation of Liability - To the extent permitted by law, you, on your own behalf and on behalf of anyone claiming by or  through you, waive any and all rights you have, or may have, to claim or assert a claim, suit, action or demand of any kind,  nature or description, including without limitation, claims, suits, actions or demands for personal  injury or death whether
    
    Extracted Information: Vacation Employee earns one day (8 hours) of paid vacation for every 400 Regular hours (not including overtime) of  compensated service up to a maximum of forty (40) hours per year. Unless state or applicable law requires otherwise,  Employee may carry over up to forty (40) hours of accrued unused vacation time to the following year, up to forty (40) hours  of accrued unused vacation time will be paid out
   
    
     
    Input:
    {input_text}

    Output:
    Extraced Content
    Return only the part related to vacation, without any additional information. For your understanding, by "the part related to vacation" ,i mean sentences which have "vacation" in them or even the related sentences which have context to vacation.
    """

    # Call the LLM with the vacation prompt and return the response
    try:
        # Use the RAG chain with the context and question
        extraction_of_vacation_policy = rag_chain.invoke({"input_text": input_text, "question": vacation_prompt})
        return extraction_of_vacation_policy
    except Exception as e:
        print(f"Error while extracting vacation section: {e}")
        return None





def format_data_using_llm(data):
    formatting_template =  f"""
    Task: Format the provided text into a JSON array where each element is a grouped set of related sentences that together describe a single concept. Do not split apart sentences that belong together.

    Instructions:
    - Remove newline characters (\n) and all formatting elements such as backslashes, double asterisks, and hashes.
    - Identify and group sentences that form a coherent idea (for example, a header followed by its supporting bullet points or related sentences).
    - Ensure each array element represents a complete idea or topic without unnecessary splitting.
    - The final output must be a JSON array where each element is a string containing the grouped, cleaned-up sentences.

    Context:
    {data}

    Example1 input:
    "Let's think step-by-step.\n\n1. **Earning & Accruing Vacations**: You earn 8 vacation hours for every 400 regular hours of compensated service.\n\n   - Total hours worked: 608\n   - Vacation Earned for 1 hour: 8/400\n   - Vacation Earned for 608 hours: 608 * (8/400)\n\nSo, you have earned 12.16 vacation hours for the 608 hours worked.\n\n**Conclusion**: You have accrued 12.16 vacation hours."

    Example1 output:
    json[
    "Earning & Accruing Vacations: You earn 8 vacation hours for every 400 regular hours of compensated service.",
    "Total hours worked: 608, Vacation Earned for 1 hour: 8/400. Vacation Earned for 608 hours: 608 * (8/400). So, you have earned 12.16 vacation hours for the 608 hours worked.",
    "Conclusion: You have accrued 12.16 vacation hours."
    ]

    Example2 input:
    "Step-by-Step process:\n\n1. **Initial Eligibility**: You need to complete 400 regular hours of service within six months to start earning vacation hours. Since the hire date is 2023-05-19 and today's date is 2024-11-02, you have worked for more than 6 months and have completed 2895 hours, so you have met this initial requirement.\n\n2. **Earning & Accruing Vacations**:\n   - Total hours worked: 2895\n   - Earning Rate: 8 vacation hours for every 400 hours\n   - Z = 2895 / 400 = 7.2375\n   - Y = Round Z down to the nearest whole number = 7\n   - X = Y * 8 = 7 * 8 = 56 vacation hours\n\n**Conclusion**: Yes, the vacation eligibility is met, and you have accrued 56 vacation hours."

    Example2 output:
    json[
      "Initial Eligibility: You need to complete 400 regular hours of service within six months to start earning vacation hours. Since the hire date is 2023-05-19 and today's date is 2024-11-02, you have worked for more than 6 months and have completed 2895 hours, so you have met this initial requirement.",
      "Earning & Accruing Vacations: Total hours worked: 2895, Earning Rate: 8 vacation hours for every 400 hours, Z = 2895 / 400 = 7.2375, Y = Round Z down to the nearest whole number = 7, X = Y * 8 = 56 vacation hours.",
      "Conclusion: Yes, the vacation eligibility is met, and you have accrued 56 vacation hours."
    ]

    Formatted Output:
    """
    try:
        formatted_data = rag_chain.invoke({"context": data, "question": formatting_template})
        return formatted_data
    except Exception as e:
        print(f"Error while extracting formatted data: {e}")
        return None


@app.route('/calculate_vacation3', methods=['POST'])
def calculate_vacation3():
    data = request.get_json()

    try:
        # Extract inputs from the request payload
        start_date = data['start_date']
        end_date = data['end_date']
        regular_hours_worked = data['regular_hours_worked']
        state = data['state']
        used_vacations = float(data['used_vacations'])
        text_inputs = data['text_inputs']

        # Normalize the state
        state = "CA-IL" if state.upper() in ["CA", "IL"] else "non CA-IL"

        # Convert text_inputs to context string
        context = process_text_inputs(text_inputs)
        

        # Formulate the first question
        question1 = f"""Task: Extract the following pieces of information from a PTO vacation policy: 1. Initial Eligibility, 2. Earning & accruing vacations, 3. Carryovers, and 4. Termination & payouts. \n

        Example:

        Vacation Policy:  You are not eligible to earn or accrue any vacation until you have completed 200 regular hours of service within six months at the initial commencement of employment on this Assignment. After this initial period of employment, ACTALENT agrees that you have earned or are eligible to earn 8 vacation hours, for every 200 Regular hours (not including overtime) of compensated service in a continuous six (6) month period. Accrued but unused vacation hours may be carried over into the next calendar year, however the maximum amount of accrued vacation may not exceed one hundred and sixty (160) hours at any given time. Unless state or applicable law requires otherwise, unused accrued vacation will not be paid out upon termination and vacation will not accrue on a pro-rata basis.

        Extracted Information:
        Initial Eligibility: You are not eligible to earn or accrue any vacation until you have completed 200 regular hours of service within six months at the initial commencement of employment on this Assignment.
        Earning & accruing vacations: After this initial period of employment, ACTALENT agrees that you have earned or are eligible to earn 8 vacation hours, for every 200 Regular hours (not including overtime) of compensated service in a continuous six (6) month period.
        Carryovers: Accrued but unused vacation hours may be carried over into the next calendar year, however the maximum amount of accrued vacation may not exceed one hundred and sixty (160) hours at any given time.
        Termination & payouts: Unless state or applicable law requires otherwise, unused accrued vacation will not be paid out upon termination and vacation will not accrue on a pro-rata basis.

        Input:

        {context}

        Output:

        Initial Eligibility:
        Earning & accruing vacations:
        Carryovers:
        Termination & payouts:
        """

        # Use the RAG chain with the context and question
        result1 = rag_chain.invoke({"context": context, "question": question1})
        # result1 = llm.generate_prompt([
        #     {"role": "system", "content": "You are a helpful assistant."},
        #     {"role": "user", "content": f"Context: {context}\nQuestion: {question1}"}
        # ])
        # print(result1)


        # Process result1 for the second question
        question2 = f"""
        Task: Extract information as given in the examples below.

        Example 1 :

        Initial Eligibility: You are not eligible to earn or accrue any vacation until you have completed 200 regular hours of service within six months at the initial commencement of employment on this Assignment.
        Earning & accruing vacations: After this initial period of employment, ACTALENT agrees that you have earned or are eligible to earn 8 vacation hours, for every 200 Regular hours (not including overtime) of compensated service in a continuous six (6) month period.
        Carryovers: Accrued but unused vacation hours may be carried over into the next calendar year, however the maximum amount of accrued vacation may not exceed one hundred and sixty (160) hours at any given time.
        Termination & payouts: Unless state or applicable law requires otherwise, unused accrued vacation will not be paid out upon termination and vacation will not accrue on a pro-rata basis.


        Extracted Information:
        Initial Eligibility (Eligible Time : 6 months , Eligible hours : 200 , Start Bonus : 0)
        Earning & accruing vacations (Time type allowed : Regular , Continuity Period : 6 months , Earning Rate : 8 vacation hours for every 400 )
        Carryover (Max hours allowed : 160 vacation hours)


        Example 2 :


        Initial Eligibility: You are granted forty (40) hours of Paid Time Off (PTO) upfront for the first nine (9) months on assignment. 
        Earning & accruing vacations: If your assignment is to be extended, every six (6) months you will receive sixty (60) hours of PTO to be used during that six (6) month period. 
        Carryovers: Accrued but unused vacation hours may not be carried over into the next six (6) month period but, may be carried over into the next calendar year, if within the same six (6) month period. Unless state or applicable law requires otherwise, 
        Termination & payouts: unused accrued vacation will not be paid out upon termination and vacation will not accrue on a pro-rata basis  

        Extracted Information:
        Initial Eligibility (Eligible Time : 0 months , Eligible hours : 0 , Start Bonus : 40)
        Earning & accruing vacations (Time type allowed : Regular , Continuity Period : 6 months , Earning Rate : 60 vacation hours for every 6 months )
        Carryover (Max hours allowed : 0 vacation hours)

        Input:
        {result1}

        Output:
        Initial Eligibility:
        Earning & accruing vacations:
        Carryovers:
        """
        result2 = rag_chain.invoke({"context": result1, "question": question2})
        # result2 = llm.generate_prompt({"context": result1, "question": question2})


        if state == "CA-IL":
            question_cail=f"""
             Based on Example below , calculate vacation hours of the Input. Let's think step-by-step

            Example 1:
            Task : Calculate PTO/Vacation accruals based on hire date 27-Mar-2024 and today's date for 27-Sep-2024. YTD Regular Hours worked 784.

            1. Earning & accruing vacations (Time type allowed : Regular ,  Earning Rate : 8 vacation hours for every 400 )
            2. Carryover (Max hours allowed : 160 vacation hours)

            Step-by-Step process


            1. **Earning & Accruing Vacations**: You earn 8 vacation hours for every 400 regular hours of compensated service. 

               - Total hours worked: 784
               - Vacation Earned for 1 hour : 8/400
               - Vacation Earned for 784 hours : 784 * Vacation Earned for 1 hour 

            So, you have earned 15.68 vacation hours for the 784 hours worked. 

            **Conclusion**: You have accrued 15.68 vacation hours.


            Input:

            Task : Calculate PTO/Vacation accruals based on hire date {start_date} and today's date for {end_date}. YTD Regular Hours worked {regular_hours_worked}.
             {result2}.Keep the output in string format and not markdown format.

            Let's think step-by-step
            """
            result_cail = rag_chain.invoke({"context": result2, "question": question_cail})
            # result_cail = llm.generate_prompt({"context": result2, "question": question_cail})

        else:
            question_cail=f"""
            Based on Example below , calculate vacation hours of the Input. Lets think step-by-step
            Example 1
            Task : Calculate PTO/Vacation accruals based on hire date 27-Mar-2024 and today's date for 27-Sep-2024. YTD Regular Hours worked 784.
            1. Initial Eligibility (Eligible Time : 6 months , Eligible hours : 400 , Start Bonus : 0)
            2. Earning & accruing vacations (Time type allowed : Regular , Continuity Period : 6 months , Earning Rate : 8 vacation hours for every 400 )
            3. Carryover (Max hours allowed : 160 vacation hours)

            Step-by-Step process

            1. **Initial Eligibility**: You need to complete 400 regular hours of service within six months to start earning vacation hours. You have worked for 8 months and 1000 hours, so you have met this initial requirement.

            2. **Earning & Accruing Vacations**: 

                - Total hours worked: 784
                - Earning Rate : 8 vacation hours for every 400
                - Z =  784/400
                - Y =  Round Z down to the nearest multiple of the significance 1
               -  X = Y * 8 (8 is the earning rate for every 400 hours)
            So, you have earned 8 vacation hours for the 600 hours worked after the initial 400 hours.

            **Conclusion**: Yes, the vacation eligibility is met, and you have accrued 8 vacation hours.


            Input:

            Task : Calculate PTO/Vacation accruals based on hire date {start_date} and today's date for {end_date}. YTD Regular Hours worked {regular_hours_worked}.
             {result2}. Keep the output in string format and not markdown format.

            Lets think step-by-step.
            """
            result_cail = rag_chain.invoke({"context": result2, "question": question_cail})
            # result_cail = llm.generate_prompt({"context": result2, "question": question_cail})
        question_calculation = f"""
            Task : 
            Input:Calculate available vacation for an employee by subtracting used vacation hours from total vacation hours using the following steps:

            T = Extract total accured vacation hours from this : {result_cail}.
            Z = Subtract {used_vacations} from T.
            
            For reference here are the examples
            Example1: If total accrued vacation hours are 16. That is if T is equal to 16.
            To get the available vacation hours, subtract used vacations from total accrued vacations, that is T. If used vacation hours are 16. Available vacation hours are- Z = T - 16.
            Here in this case Z = 16 - 16. Which is equal to 0. So Z = 0.

            Conclusion of example 1:  
            {{
                "Calculation": "16 - 16 = 0",
                "available vacation hours": 0
            }}

            Example 2:If total accrued vacation hours are 16. That is if T is equal to 16.
            To get the available vacation hours, subtract used vacations from total accrued vacations, that is T. If used vacation hours are 16. Available vacation hours are- Z = T - 16.
            Here in this case Z = 16 - 32. Which is equal to -16. So Z = -16.

            Conclusion of example 2:
            {{
                "Calculation": "16 - 32 = -16",
                "available vacation hours": -16
            }}





            Output:
            Now, return the output strictly in the given JSON format.
            **Expected JSON Output Format:**
            {{
                "Calculation": "T - used_vacation_hours = Z",
                "available vacation hours": Z
            }}
        """
        result_calculation = rag_chain.invoke({"context": result_cail, "question": question_calculation})
        # result_calculation = llm.generate_prompt({"context": result_cail, "question": question_calculation})
        print(result_calculation)

        input_string = result_calculation

        # Regular expression to extract the value after "available vacation hours" (handles both integers and floats)
        # match = re.search(r'"available vacation hours":\s*([\d\.]+)', input_string)
        match = re.search(r'"available vacation hours":\s*(-?\d+\.\d{1,2}|\-?\d+)', input_string)

        # If a match is found, assign the value to vacation_hours_available
        if match:
            vacation_hours_available = float(match.group(1))  # This stores the value as float
            print(f"Vacation hours available: {vacation_hours_available}")
        else:
            vacation_hours_available=0
            print("No match found.")



        raw_output_data = {"leaves_policy": result1, "leaves_policy_breakdown": result2,"leaves_accrued_calculation":result_cail,"leaves_available_calculation":result_calculation}
        data = {"leaves_policy_breakdown": result1,"leaves_accrued_calculation":result_cail,"leaves_available_calculation":result_calculation}


        # vacation_hours_available = None
        # for sentence in result_calculation:
        #     match = re.search(r"\"?available vacation hours\"?\s*[:=]\s*(-?\d+(?:\.\d+)?)", sentence)
        #     if match:
        #         vacation_hours_available = float(match.group(1))
        #         break






        # Call the format_data function
        # formatted_data = format_data(data)
        formatted_data=[]
        format1=format_data_using_llm(result1)
        format1_mrkdwn=remove_markdown(format1)
        format1_nl=remove_newlines(format1_mrkdwn)
        format2=format_data_using_llm(result_cail)
        format2_mrkdwn=remove_markdown(format2)
        format2_nl=remove_newlines(format2_mrkdwn)
        format3=format_data_using_llm(result_calculation)
        format3_mrkdwn=remove_markdown(format3)
        format3_nl=remove_newlines(format3_mrkdwn)
        leaves_available_calculation_standard_lines ={"To get the available vacation hours, subtract used vacations from total accrued vacations"}
        formatted_data=({"leaves_policy_breakdown":format1_nl,"leaves_accrued_calculation":format2_nl,"leaves_available_calculation":f"To get the available vacation hours, subtract used vacations from total accrued vacations.  {format3_nl}"})
        # formatted_data2=remove_markdown(formatted_data1)
        # formatted_data=remove_newlines(formatted_data2)



        leaves_policy_unfiltered_with_new_line_characters = remove_markdown(context)
        leaves_policy_unfiltered = remove_newlines(leaves_policy_unfiltered_with_new_line_characters)
        leaves_policy = extract_vacation_section(leaves_policy_unfiltered, llm)
        leaves_policy = leaves_policy.replace('\n', ' ')  # Replace newlines with spaces to avoid issues



        log_api_response(formatted_data, leaves_policy, raw_output_data)

        # Return the final result
        # return jsonify({"r1": result1, "r2": result2,"cail":result_cail,"calc":result_calculation}), 200
        return jsonify({"leaves_policy_breakdown":format1_nl,"leaves_accrued_calculation":format2_nl,"leaves_available_calculation":f"To get the available vacation hours, subtract used vacations from total accrued vacations.  {format3_nl}","leaves_policy":leaves_policy,"vacation_hours_available":vacation_hours_available,"leaves_available_calculation_raw_json":result_calculation}), 200
        # return jsonify({"leaves_policy_unfiltered":leaves_policy_unfiltered})


    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":

    app.run(debug=True)
