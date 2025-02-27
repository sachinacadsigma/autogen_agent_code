from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT')
}

# Function to get a database connection
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

@app.route('/add_user_login', methods=['POST'])
def add_user_login():
    try:
        # Get the request data
        data = request.get_json()
        user_name = data.get('user_name')

        if not user_name:
            return jsonify({'error': 'user_name is required'}), 400

        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert user login into the database
        query = """
            INSERT INTO pto_user_login_log (user_name, login_date_and_time)
            VALUES (%s, %s) RETURNING session_id;
        """
        login_date_and_time = datetime.now()
        cursor.execute(query, (user_name, login_date_and_time))

        # Get the auto-generated login_id
        session_id = cursor.fetchone()[0]

        # Commit the transaction
        conn.commit()

        # Close the connection
        cursor.close()
        conn.close()

        return jsonify({'message': 'User login added successfully', 'session_id': session_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
