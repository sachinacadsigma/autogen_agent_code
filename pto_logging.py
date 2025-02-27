import psycopg2
from flask import Flask, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT')
}


# Function to get database connection
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Route to insert data into the PTO_logging table
@app.route('/add_logs', methods=['POST'])
def add_logs():
    print(DB_CONFIG)
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['user_name', 'employee_id', 'start_date', 'end_date', 
                           'employee_name', 'client_name', 'total_hours', 
                           'total_leaves_used', 'state', 'leaves_available','file_name','session_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f"'{field}' is required."}), 400

        # Parse dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        employee_id = str(data.get('employee_id', ''))


        try:
            total_hours = float(data['total_hours'])  # Changed from int to float
            total_leaves_used = float(data['total_leaves_used'])  # Changed from int to float
            leaves_available = float(data['leaves_available'])  # Changed from int to float
        except ValueError:
            return jsonify({'error': "'total_hours', 'total_leaves_used', and 'leaves_available' must be decimal numbers."}), 400


        # Handle optional session_id
        session_id = data.get('session_id')
        if session_id is not None:
            if not str(session_id).isdigit():
                return jsonify({'error': "session_id must be a numeric value"}), 400
            session_id = int(session_id)  # Convert to integer



        # Insert data into the database
        connection = get_db_connection()
        cursor = connection.cursor()
        insert_query = """
            INSERT INTO PTO_logging (
                user_name, employee_id, start_date, end_date, 
                employee_name, client_name, total_hours, total_leaves_used, 
                state, leaves_available, file_name,session_id,date_and_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            data['user_name'],employee_id, 
            start_date, end_date, data['employee_name'], data['client_name'], 
            total_hours, total_leaves_used, data['state'], 
            leaves_available,data['file_name'],session_id, datetime.utcnow()
        ))
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'message': 'Log added successfully!'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

