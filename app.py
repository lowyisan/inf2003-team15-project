from flask import Flask, render_template, g, flash, redirect, url_for
from forms import RegistrationForm, LoginForm
import pymysql
from sshtunnel import SSHTunnelForwarder
from passlib.hash import pbkdf2_sha256
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

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
        # Hash password
        hashed_password = pbkdf2_sha256.hash(form.password.data)

        # Create a DB connection
        connection = get_db()
        cursor = connection.cursor()

        # Prepared statement for inserting to Users table
        query = "INSERT INTO Users (name, email, phone, password) VALUES (%s, %s, %s, %s)"
        values = (form.username.data, form.email.data, form.phone.data, hashed_password)

        # Execute the prepared statement to insert user
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


@app.route('/login.html', methods=['GET', 'POST'])
def login():
    # Create login form
    form = LoginForm()

    # Validate login form
    if form.validate_on_submit():
        # Retrieve the user's hashed password from the database
        connection = get_db()
        cursor = connection.cursor()

        query = "SELECT password FROM Users WHERE email = %s"
        cursor.execute(query, (form.email.data,))
        result = cursor.fetchone()

        if result is not None:
            stored_hashed_password = result[0]

            # Check if the provided password matches the stored hashed password
            if pbkdf2_sha256.verify(form.password.data, stored_hashed_password):
                flash(f'Login successful, welcome {form.email.data}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Login failed. Invalid email or password.', 'error')
        else:
            flash('Login failed. Invalid email or password.', 'error')

        cursor.close()

    return render_template("login.html", form=form)

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

@app.route('/analysis.html')
def analysis():
    return render_template("analysis.html")

@app.route('/404.html')
def error404():
    return render_template("404.html")

@app.route('/appointment.html')
def appointment():
    return render_template("appointment.html")

@app.route('/location-analysis.html')
def locationanalysis():
    connection = get_db()
    cursor = connection.cursor()

    # Query for highest sales revenue location
    query = "SELECT transaction_year as Year, town_estate as TownEstate, total_price as TotalCost FROM (SELECT transaction_year, town_estate, SUM(price) AS total_price, ROW_NUMBER() OVER (PARTITION BY transaction_year ORDER BY SUM(price) DESC) AS rowNumber FROM HDB hdb JOIN Transaction t ON hdb.hdb_id = t.hdb_id GROUP BY transaction_year, town_estate ORDER BY transaction_year, total_price DESC) AS t WHERE t.rowNumber = 1 ORDER BY transaction_year;"
    cursor.execute(query)
    result = cursor.fetchall()
    df = pd.DataFrame(result, columns=['Year', 'Town Estate', 'Total Sales Revenue'])
    # Add $ to the 'Cost' column
    df['Total Sales Revenue'] = '$ ' + df['Total Sales Revenue'].astype(str)
    html_table = df.to_html(classes='table table-striped table-bordered table-hover', index=False)

    # Create a new cursor for the second query
    cursor1 = connection.cursor()

    # Query for lowest sales revenue location
    query1 = "SELECT transaction_year as Year, town_estate as TownEstate, total_price as TotalCost FROM (SELECT transaction_year, town_estate, SUM(price) AS total_price, ROW_NUMBER() OVER (PARTITION BY transaction_year ORDER BY SUM(price) ASC) AS rowNumber FROM HDB hdb JOIN Transaction t ON hdb.hdb_id = t.hdb_id GROUP BY transaction_year, town_estate ORDER BY transaction_year, total_price ASC) AS t WHERE t.rowNumber = 1 ORDER BY transaction_year;"
    cursor1.execute(query1)
    result1 = cursor1.fetchall()
    df1 = pd.DataFrame(result1, columns=['Year', 'Town Estate', 'Total Sales Revenue'])
    # Add $ to the 'Cost' column
    df1['Total Sales Revenue'] = '$ ' + df1['Total Sales Revenue'].astype(str)
    html_table1 = df1.to_html(classes='table table-striped table-bordered table-hover', index=False)

    cursor.close()
    cursor1.close()

    return render_template("location-analysis.html", data=html_table, data1=html_table1)



@app.route('/size-analysis.html')
def sizeanalysis():
    connection = get_db()
    cursor = connection.cursor()
    query = "SELECT t.transaction_year,h.town_estate, CASE WHEN h.floorAreaSQM <= 50 THEN '0-50 sqm' WHEN h.floorAreaSQM <= 100 THEN '51-100 sqm' WHEN h.floorAreaSQM <= 150 THEN '101-150 sqm' ELSE '151+ sqm' END AS sqm_range, ROUND(AVG(t.price), 2) AS mean_price FROM Transaction t JOIN HDB h ON t.hdb_id = h.hdb_id GROUP BY t.transaction_year,h.town_estate,sqm_range;"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    df = pd.DataFrame(result, columns=['transaction_year', 'town_estate', 'sqm_range', 'mean_price'])
    figures = []
    for town_estate in df['town_estate'].unique():
        fig = px.line(
            df[df['town_estate'] == town_estate],
            x='transaction_year',
            y='mean_price',
            color='sqm_range',
            markers=True,
            title=f'Mean Price Over Years - {town_estate}'
        )
    
        figures.append(fig)

    # Convert the Plotly figures to HTML
    chart_html = [fig.to_html(full_html=False) for fig in figures]
    return render_template("size-analysis.html", chart_html = chart_html)

@app.route('/outlier-analysis.html')
def outlieranalysis():
    return render_template("outlier-analysis.html")

@app.route('/time-series-analysis.html')
def timeseriesanalysis():
    connection = get_db()
    cursor = connection.cursor()
    query = "SELECT h.town_estate, t.transaction_year,CASE WHEN t.transaction_month IN (1, 2, 3) THEN 'Q1' WHEN t.transaction_month IN (4, 5, 6) THEN 'Q2' WHEN t.transaction_month IN (7, 8, 9) THEN 'Q3' WHEN t.transaction_month IN (10, 11, 12) THEN 'Q4' END AS quarter, AVG(t.price) AS mean_price FROM Transaction t JOIN HDB h ON t.hdb_id = h.hdb_id WHERE t.transaction_month IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12) GROUP BY h.town_estate, t.transaction_year, quarter ORDER BY h.town_estate, t.transaction_year, quarter;"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    df = pd.DataFrame(result, columns=['town_estate', 'transaction_year','quarter','mean_price'])
    figures = []
    for town_estate in df['town_estate'].unique():
        fig = px.line(
            df[df['town_estate'] == town_estate],
            x='quarter',
            y='mean_price',
            color='transaction_year',
            markers=True,
            title=f'Mean Price Over Years - {town_estate}'
        )
    
        figures.append(fig)
    # Convert the Plotly figures to HTML
    chart_html = [fig.to_html(full_html=False) for fig in figures]
    return render_template("time-series-analysis.html", chart_html = chart_html)

@app.route('/price-trend-analysis.html')
def pricetrendanalysis():
    return render_template("price-trend-analysis.html")

@app.route('/rooms-analysis.html')
def roomsanalysis():
    connection = get_db()
    cursor = connection.cursor()
    query = "SELECT t.transaction_year, h.town_estate, ROUND(AVG(t.price), 2) AS mean_price, h.flat_type FROM Transaction t JOIN HDB h ON t.hdb_id = h.hdb_id GROUP BY t.transaction_year, h.town_estate, h.flat_type;"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    df = pd.DataFrame(result, columns=['transaction_year', 'town_estate', 'mean_price', 'flat_type'])
    figures = []
    for town_estate in df['town_estate'].unique():
        fig = px.line(
            df[df['town_estate'] == town_estate],
            x='transaction_year',
            y='mean_price',
            color='flat_type',
            markers=True,
            title=f'Mean Price Over Years - {town_estate}'
        )
    
        figures.append(fig)
    # Convert the Plotly figures to HTML
    chart_html = [fig.to_html(full_html=False) for fig in figures]
    return render_template("rooms-analysis.html", chart_html = chart_html)

# Teardown function to close the database connection
@app.teardown_appcontext
def close_db_connection(exception):
    db_connection = getattr(g, 'db_connection', None)
    if db_connection is not None:
        db_connection.close()

if __name__ == "__main__":
    app.run(debug=True)