from flask import Flask, render_template, g, flash, redirect, url_for
from forms import RegistrationForm, LoginForm
import pymysql
from sshtunnel import SSHTunnelForwarder

app = Flask(__name__, template_folder="templates")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

app.config['SECRET_KEY'] = '1234'

# MySQL configuration
db_config = {
    'user': 'root',
    'password': 'iLoveRoots99',
    'db': 'inf2003projectdb',
}

# SSH Tunnel Setup
def create_ssh_tunnel():
    try:
        server = SSHTunnelForwarder(
            '35.212.167.35',
            ssh_username='dev',
            ssh_password='iLoveDonuts99',
            ssh_port=22,
            remote_bind_address=('127.0.0.1', 3306)
        )
        server.start()
        return server
    
    except Exception as e:
        return None

# Create the SSH tunnel when the application starts
ssh_server = create_ssh_tunnel()

# Function for creating DB Connection
def get_db():
    if not hasattr(g, 'db_connection'):
        g.db_connection = pymysql.connect(
            host='127.0.0.1',
            port=ssh_server.local_bind_port,
            **db_config
        )
    return g.db_connection

# Before the first request, check the SSH tunnel
# @app.before_request
# def check_ssh_tunnel():
#     if not ssh_server.is_active:
#         print("SSH tunnel failed to establish.")
#         # You could raise an exception here or handle it as appropriate
#     else:
#         print("SSH tunnel is active")

# Landing Page
@app.route('/')
def index(): 
    if ssh_server is None:
        flash("SSH tunnel failed to establish. Error: Unable to connect to the SSH server.")
    return render_template("index.html") 

# Registraton Page
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    # Create a DB connection
    # connection = get_db()
    # cursor = connection.cursor()

    # # Example query
    # cursor.execute("SELECT * FROM Users")
    # data = cursor.fetchall()

    # # Close the cursor and the connection
    # cursor.close()

    form = RegistrationForm()

    if form.validate_on_submit():
        # Insert into DB
        # Create a DB connection
        connection = get_db()
        cursor = connection.cursor()

        # Insert new user using prepared statement
        query = "INSERT INTO Users (name, email, password) VALUES (%s, %s, %s)"
        # query = "INSERT INTO Users (name, email, phone, password) VALUES (%s, %s, %s, %s)"
        values = (form.username.data, form.email.data, form.password.data)

        try:
            cursor.execute(query, values)
            connection.commit()
            flash(f'Thank you for registering, {form.username.data}. <a href="{url_for("login")}">Login Here</a>', 'success')
        except pymysql.Error as e:
            connection.rollback()
            flash(f'An error occurred while registering: {e}', 'error')
        finally:
            cursor.close()

    return render_template("register.html", title='Registration', form=form)
    # return render_template("register.html", data=data, title='Registration', form=form)


@app.route('/login.html')
def login():
    return render_template("login.html")

@app.route('/about.html')
def about():
    return render_template("about.html")

@app.route('/contact.html')
def contact():
    return render_template("contact.html")

@app.route('/property-list.html')
def propertylist():
    return render_template("property-list.html")

@app.route('/property-agent.html')
def propertyagent():
    return render_template("property-agent.html")

@app.route('/property-type.html')
def propertytype():
    return render_template("property-type.html")

@app.route('/testimonial.html')
def testimonial():
    return render_template("testimonial.html")

@app.route('/404.html')
def error404():
    return render_template("404.html")

@app.route('/appointment.html')
def appointment():
    return render_template("appointment.html")

# Teardown function to close the database connection
@app.teardown_appcontext
def close_db_connection(exception):
    db_connection = getattr(g, 'db_connection', None)
    if db_connection is not None:
        db_connection.close()

if __name__ == "__main__":
    app.run(debug=True)