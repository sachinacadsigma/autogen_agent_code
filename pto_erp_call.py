from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# OAuth credentials
TENANT_ID = "371cb917-b098-4303-b878-c182ec8403ac"
CLIENT_ID = "95faa8e8-8062-4e79-bd72-93d0ab4d0bf4"
CLIENT_SECRET = "qYn8Q~4P05hz~hLOiqleInGu8AgOCTHhuNyqEaMh"
RESOURCE = "45fedc21-15c5-40d8-83d2-0a5d20694717"

# API endpoint
API_URL = "https://allegismulesoft.allegisgroup.com/allegis-prod-psemployeetimedataapi/v1/timecode/summary"

def get_access_token():
    """Fetches the access token."""
    token_url = f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/token'

    payload = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'resource': RESOURCE,
    }

    response = requests.post(token_url, data=payload)
    response.raise_for_status()  # Raise an error for bad responses
    token_response = response.json()

    if 'access_token' in token_response:
        return token_response['access_token']
    else:
        raise Exception("Failed to obtain access token")

def fetch_employee_data(access_token, employee_id, start_date, end_date):
    """Fetches employee data from the API."""
    params = {
        'EmployeeId': employee_id,
        'StartDate': start_date,
        'EndDate': end_date
    }

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    response = requests.get(API_URL, params=params, headers=headers)

    if response.status_code == 404:  # Handle not found errors
        raise ValueError(f"Employee ID {employee_id} not found.")
    elif response.status_code != 200:  # Handle other errors
        response.raise_for_status()

    # Check if the response contains valid data
    data = response.json()
    if not data:  # API returned empty or no data
        raise ValueError(f"No data found for Employee ID {employee_id}.")

    return data



def transform_employee_data(employee_data):
    """Transforms the API response to the desired variable names."""
    transformed_data = []
    for record in employee_data:
        transformed_data.append({
            "employee_id": record.get("EmployeeId"),
            "employee_name": record.get("EmployeeName"),
            "used_vacations": record.get("TotalHrsVacUsed"),
            "regular_hours_worked": record.get("TotalHrsWorked"),
            "state": record.get("State"),
            "customer_name": record.get("CustomerName"),
            "customer_id": record.get("CustomerId"),
            "remote_worker":record.get("RemoteWorker"),
            "home_state":record.get("HomeState"),
            "job_req_status":record.get("JobReqStatus")
        })
    return transformed_data

# @app.route('/erp_data', methods=['POST'])
def get_erp_data():
    """API endpoint to fetch employee data."""
    try:
        # Parse input JSON
        input_data = request.get_json()
        employee_id = input_data.get("employee_id")
        start_date = input_data.get("start_date")
        end_date = input_data.get("end_date")

        # Validate input
        if not all([employee_id, start_date, end_date]):
            return jsonify({"error": "employee_id, start_date, and end_date are required"}), 400

        # Step 1: Fetch the access token
        access_token = get_access_token()

        # print("prod", access_token)

        # Step 2: Fetch employee data
        employee_data = fetch_employee_data(access_token, employee_id, start_date, end_date)
       
        # print("prod", employee_data)         

        # Step 3: Transform employee data
        transformed_data = transform_employee_data(employee_data)

        return jsonify(transformed_data), 200
    
    except ValueError as ve:
        # Handle known errors (e.g., invalid employee ID)
        return jsonify({"error": str(ve)}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
