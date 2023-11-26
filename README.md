**User Manual for SingaEstate**

**Environment Setup**

**Prerequisites**
1. Python 3.6 or higher
2. pip (Python package installer)
3. MySQL Server and Client
4. Access to an SSH server (for SSH Tunneling)

**Installation**
1. Install Python and pip on your machine.
   
2. Install the required Python packages using pip:
pip install bcrypt blinker cffi click colorama contourpy cryptography cycler distlib dnspython
email-validator filelock Flask flask-mysql-connector Flask-WTF fonttools idna itsdangerous
Jinja2 kiwisolver MarkupSafe matplotlib mysql-connector-python numpy packaging pandas paramiko
passlib Pillow platformdirs plotly protobuf pycparser pymongo PyMySQL PyNaCl pyparsing python-dateutil
pytz setuptools six sshtunnel tenacity tzdata virtualenv Werkzeug WTForms

3. Ensure MySQL is installed and running on your machine

**Configuration & Running the Application**

1. Establish a connection with MySQL with the credentials.

2. Start the Flask app: flask run --debug

Note: The server may be down by the time of grading, please refer to the demo in our presentation video.
