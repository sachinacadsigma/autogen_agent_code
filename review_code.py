import openai
import sys
import json
import os
from pathlib import Path

# Hardcoded Azure OpenAI credentials
openai.api_key = "2f6e41aa534f49908feb01c6de771d6b"  # Replace with actual API key
openai.api_base = "https://ea-oai-sandbox.openai.azure.com/"  # Replace with Azure endpoint
openai.api_version = "2024-05-01-preview"
deployment_name = "AllegisGPT-4o"  # Replace with your deployment name

def review_code(code, filename):
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
            {"role": "user", "content": f"Review this Python code from {filename}:\n{code}"}
        ],
        temperature=0,
        max_tokens=500
    )

    return response.choices[0].message.content  # Corrected response handling

# Get all Python files in the current directory and subdirectories
python_files = list(Path(".").rglob("*.py"))

if not python_files:
    print("⚠️ No Python files found for review.")
    sys.exit(0)  # No files, exit successfully

critical_issues_found = False
review_results = {}

# Review each file
for py_file in python_files:
    with open(py_file, "r", encoding="utf-8") as file:
        code = file.read()
    
    print(f"🔍 Reviewing {py_file} ...")
    review_output = review_code(code, py_file)

    # Save review output for each file
    review_results[str(py_file)] = review_output

    # Save raw output
    output_filename = f"review_output_{py_file.name}.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(review_output)

    # Parse JSON output
    try:
        review_data = json.loads(review_output)
        if review_data.get("critical_issues", False):  # If critical_issues is True
            print(f"❌ Critical issues detected in {py_file}! Stopping the build.")
            critical_issues_found = True
    except json.JSONDecodeError:
        print(f"⚠️ Error: LLM did not return valid JSON for {py_file}.")
        print(review_output)  # Print for debugging
        critical_issues_found = True

# Stop pipeline if any critical issues were found
if critical_issues_found:
    sys.exit(1)  # Fail the pipeline

print("✅ No critical issues found in any Python file. Proceeding with build.")
sys.exit(0)  # Exit successfully
