from flask import Flask
from saml import saml_login, saml_callback, extract_token
import os
#
app = Flask(__name__)


app.config["SAML_PATH"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saml")
app.config["SECRET_KEY"] = os.getenv('JWT_SECRET_KEY')

# SAML routes
@app.route('/saml/login')
def login():
    return saml_login(app.config["SAML_PATH"])

@app.route('/saml/callback', methods=['POST'])
def login_callback():
    return saml_callback(app.config["SAML_PATH"])

@app.route('/saml/token/extract', methods=['POST'])
def func_get_data_from_token():
    return extract_token()



@app.route('/')
def hello():
    return "Hi"

from pto_upload_file import process_document
@app.route('/process_doc', methods=['POST'])
def call_process_document():
    return process_document()

from pto_erp_call import get_erp_data
@app.route('/erp_call', methods=['POST'])
def call_get_erp_data():
    return get_erp_data()

from pto_calculation import calculate_vacation
@app.route('/calculate_vacation_hours', methods=['POST'])
def call_calculate_vacation():
    return calculate_vacation()

from pto_calculation2 import calculate_vacation3
@app.route('/calculate_vacation_hours_new', methods=['POST'])
def call_calculate_vacation3():
    return calculate_vacation3()

from pto_feedback import add_feedback
@app.route('/pto_feedback', methods=['POST'])
def call_pto_feedback():
    return add_feedback()

from pto_logging import add_logs
@app.route('/pto_logging', methods=['POST'])
def call_pto_logging():
    return add_logs()

from pto_user_login_log import add_user_login
@app.route('/pto_user_login_log', methods=['POST'])
def call_pto_user_login_log():
    return add_user_login()


if __name__ == "__main__":
    app.run(debug=True)
