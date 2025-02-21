import openai
import sys
import json

# Hardcoded Azure OpenAI credentials
openai.api_key = "2f6e41aa534f49908feb01c6de771d6b"  # Replace with actual API key
openai.api_base = "https://ea-oai-sandbox.openai.azure.com/"  # Replace with Azure endpoint
openai.api_version = "2024-05-01-preview"
deployment_name = "AllegisGPT-4o"  # Replace with your deployment name

def review_code(code):
    client = openai.AzureOpenAI(
        api_key=openai.api_key,
        api_version=openai.api_version,
        azure_endpoint=openai.api_base
    )

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": """You are a strict senior code reviewer.
            Your task is to analyze the given Python code and return a structured JSON response.
            Identify syntax errors, security vulnerabilities, and bad practices.
            Your response MUST be in JSON format like this:

            {
                "critical_issues": true/false,
                "issues": [
                    {
                        "type": "Syntax Error/Security Risk/Bad Practice",
                        "description": "Explain the issue clearly",
                        "line_number": 10
                    }
                ],
                "recommendations": "Provide fixes if possible."
            }

            If no issues are found, return:
            {
                "critical_issues": false,
                "issues": [],
                "recommendations": "No critical issues detected."
            }
            """},
            {"role": "user", "content": f"Review this Python code:\n{code}"}
        ],
        temperature=0,
        max_tokens=500
    )

    return response.choices[0].message.content  # Corrected response handling

# Read the latest code
with open("main.py", "r") as file:
    code = file.read()

# Get AI review comments
review_output = review_code(code)

# Save raw output
with open("review_output.json", "w") as f:
    f.write(review_output)

# Print raw output for debugging
print("🔍 AI Response:")
print(review_output)

# Parse JSON output
try:
    review_data = json.loads(review_output)
    if review_data.get("critical_issues", False):  # If critical_issues is True
        print("❌ Critical issues detected! Stopping the build.")
        sys.exit(1)  # Fail the pipeline
    else:
        print("✅ No critical issues found. Proceeding with build.")
except json.JSONDecodeError:
    print("⚠️ Error: LLM did not return valid JSON. Here is the raw response:")
    print(review_output)  # Print for debugging
    sys.exit(1)  # Fail pipeline if LLM response is not valid JSON
