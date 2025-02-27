# import psycopg2
# from flask import Flask, request, jsonify
# from datetime import datetime
# import os

# app = Flask(__name__)

# # Database configuration
# DB_CONFIG = {
#     'host': os.getenv('DB_HOST'),
#     'database': os.getenv('DB_NAME'),
#     'user': os.getenv('DB_USER'),
#     'password': os.getenv('DB_PASSWORD'),
#     'port': os.getenv('DB_PORT')
# }

# def get_db_connection():
#     return psycopg2.connect(**DB_CONFIG)

# @app.route('/add_feedback', methods=['POST'])
# def add_feedback():
#     try:
#         data = request.get_json()

#         # Validate required fields
#         required_fields = ['user_name', 'employee_id', 'start_date', 'end_date', 
#                            'employee_name', 'client_name', 'total_hours', 
#                            'total_leaves_used', 'state', 'leaves_available', 'feedback_type', 'file_name']
        
#         for field in required_fields:
#             if field not in data:
#                 return jsonify({'error': f"'{field}' is required."}), 400

#         # Parse dates
#         start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
#         end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()

#         # Ensure employee_id is an integer
    
#         employee_id = str(data.get('employee_id', ''))
#         if not employee_id.isdigit():
#             return jsonify({'error': "employee_id must contain only numbers"}), 400




#         # employee_id = str(data['employee_id'])
        
        


#         try:
#             total_hours = float(data['total_hours'])  # Changed from int to float
#             total_leaves_used = float(data['total_leaves_used'])  # Changed from int to float
#             leaves_available = float(data['leaves_available'])  # Changed from int to float
#         except ValueError:
#             return jsonify({'error': "'total_hours', 'total_leaves_used', and 'leaves_available' must be decimal numbers."}), 400

#         connection = get_db_connection()
#         cursor = connection.cursor()
        
#         insert_query = """
#             INSERT INTO PTO_feedback (
#                 employee_id,
#                 start_date,
#                 end_date,
#                 employee_name,
#                 client_name,
#                 total_hours,
#                 total_leaves_used,
#                 state,
#                 leaves_available,
#                 date_and_time,
#                 feedback,
#                 user_name,
#                 feedback_type,
#                 file_name
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """
        
#         values = (
#             str(employee_id),
#             start_date,
#             end_date,
#             str(data['employee_name']),
#             str(data['client_name']),
#             total_hours,  # Now supports decimals
#             total_leaves_used,  # Now supports decimals
#             str(data['state']),
#             leaves_available,  # Now supports decimals
#             datetime.utcnow(),
#             str(data.get('feedback', '')),
#             str(data['user_name']),
#             str(data['feedback_type']),
#             str(data['file_name'])
#         )
        
#         cursor.execute(insert_query, values)
#         connection.commit()
#         cursor.close()
#         connection.close()

#         return jsonify({'message': 'Feedback added successfully!'}), 201

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=True)



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

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.route('/add_feedback', methods=['POST'])
def add_feedback():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['user_name', 'employee_id', 'start_date', 'end_date', 
                           'employee_name', 'client_name', 'total_hours', 
                           'total_leaves_used', 'state', 'leaves_available', 'feedback_type', 'file_name','session_id']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f"'{field}' is required."}), 400

        # Parse dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()

        # Ensure employee_id is an integer
    
        employee_id = str(data.get('employee_id', ''))
        if not employee_id.isdigit():
            return jsonify({'error': "employee_id must contain only numbers"}), 400




        # employee_id = str(data['employee_id'])
        
        


        try:
            total_hours = float(data['total_hours'])  # Changed from int to float
            total_leaves_used = float(data['total_leaves_used'])  # Changed from int to float
            leaves_available = float(data['leaves_available'])  # Changed from int to float
            session_id = int(data['session_id'])
        except ValueError:
            return jsonify({'error': "'total_hours', 'total_leaves_used', and 'leaves_available' must be decimal numbers."}), 400

        # Handle optional session_id
        session_id = data.get('session_id')
        if not str(session_id).isdigit():
            return jsonify({'error': "session_id must be a numeric value"}), 400
        session_id = int(session_id)  # Convert to integer





        connection = get_db_connection()
        cursor = connection.cursor()
        
        insert_query = """
            INSERT INTO PTO_feedback (
                employee_id,
                start_date,
                end_date,
                employee_name,
                client_name,
                total_hours,
                total_leaves_used,
                state,
                leaves_available,
                date_and_time,
                feedback,
                user_name,
                feedback_type,
                file_name,
                session_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            str(employee_id),
            start_date,
            end_date,
            str(data['employee_name']),
            str(data['client_name']),
            total_hours,  # Now supports decimals
            total_leaves_used,  # Now supports decimals
            str(data['state']),
            leaves_available,  # Now supports decimals
            datetime.utcnow(),
            str(data.get('feedback', '')),
            str(data['user_name']),
            str(data['feedback_type']),
            str(data['file_name']),
            session_id
        )
        
        cursor.execute(insert_query, values)
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'message': 'Feedback added successfully!'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
