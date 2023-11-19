import textwrap
from flask import Flask, render_template, g, flash, redirect, url_for, request, jsonify, session
from forms import RegistrationForm, LoginForm
import pymysql
from sshtunnel import SSHTunnelForwarder
from passlib.hash import pbkdf2_sha256
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime



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
        ssh_server = create_ssh_tunnel()

        if ssh_server is None:
            # Handle the case where the SSH tunnel failed to establish
            flash("SSH tunnel failed to establish. Error: Unable to connect to the SSH server.")
            return None

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
    

@app.route('/register.html', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = pbkdf2_sha256.hash(form.password.data)

        # Connect to your database
        connection = get_db()
        cursor = connection.cursor()

        # Insert user into Users table
        user_query = "INSERT INTO Users (name, email, phone, password) VALUES (%s, %s, %s, %s)"
        user_values = (form.username.data, form.email.data, form.phone.data, hashed_password)
        cursor.execute(user_query, user_values)
        user_id = cursor.lastrowid
        connection.commit()

        if form.role.data == 'agent':
            # Insert additional agent details into Agents table
            agent_query = "INSERT INTO Agents (CEANumber, agencyLicenseNo, agentTitle, userID) VALUES (%s, %s, %s, %s)"
            agent_values = (form.CEANumber.data, form.agencyLicenseNo.data, form.agentTitle.data, user_id)
            cursor.execute(agent_query, agent_values)
            connection.commit()

        flash('Thank you for registering! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login.html', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        connection = get_db()
        cursor = connection.cursor()

        # Query to check user credentials
        query = "SELECT userID, password FROM Users WHERE email = %s"
        cursor.execute(query, (form.email.data,))
        result = cursor.fetchone()

        if result is not None:
            user_id, stored_hashed_password = result

            if pbkdf2_sha256.verify(form.password.data, stored_hashed_password):
                # Check if the user is an agent
                agent_query = "SELECT CEANumber FROM Agents WHERE userID = %s"
                cursor.execute(agent_query, (user_id,))
                agent_result = cursor.fetchone()

                # Set user type in session
                session['user_id'] = user_id
                if agent_result is not None:
                    session['user_type'] = 'agent'
                    session['agent_id'] = user_id
                    session['CEANumber'] = agent_result[0]
                else:
                    session['user_type'] = 'normal_user'

                flash(f'Login successful, welcome {form.email.data}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid email or password.', 'error')
        else:
            flash('Invalid email or password.', 'error')

        cursor.close()

    return render_template("login.html", form=form)

@app.route('/logout')
def logout():
    # Remove user_id and other user-related information from session
    session.pop('user_id', None)
    session.pop('user_type', None) 
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('index'))



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


@app.route('/appointment.html', methods=['GET', 'POST'])
def appointment():
    connection = get_db()
    cursor = connection.cursor()

    if request.method == 'POST':
        filter_agency_name = request.form.get('filter_agency_name')
        filter_agent_title = request.form.get('filter_agent_title')

        query = "SELECT DISTINCT u.name, a.agentTitle, a.CEANumber, ag.agencyName " \
                "FROM Users u, Agency ag, Agents a " \
                "WHERE u.userID = a.userID AND ag.agencyLicenseNo = a.agencyLicenseNo"

        if filter_agency_name:
            query += f" AND ag.agencyName = '{filter_agency_name}'"

        if filter_agent_title:
            query += f" AND a.agentTitle = '{filter_agent_title}'"

        cursor.execute(query)
    else:
        # If it's a GET request without filters, retrieve all agents
        query = "SELECT DISTINCT u.name, a.agentTitle, a.CEANumber, ag.agencyName " \
                "FROM Users u, Agency ag, Agents a " \
                "WHERE u.userID = a.userID AND ag.agencyLicenseNo = a.agencyLicenseNo"
        cursor.execute(query)

    result = cursor.fetchall()

    # Retrieve available agency names and agent titles for populating the filter dropdowns
    cursor.execute("SELECT DISTINCT agencyName FROM Agency")
    agency_names = cursor.fetchall()

    cursor.execute("SELECT DISTINCT agentTitle FROM Agents")
    agent_titles = cursor.fetchall()

    return render_template("appointment.html", agents=result, agency_names=agency_names, agent_titles=agent_titles)


@app.route('/create-appointment', methods=['POST'])
def create_appointment():

    if 'user_id' not in session or session.get('user_type') != 'normal_user':
        flash("You need to be logged in as a homebuyer to view appointments.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    agent_name = request.form['agentName']
    date = request.form['date']
    time = request.form['time']

    # Create a DB connection
    connection = get_db()
    cursor = connection.cursor()
    
    # Combine date and time into a single datetime object
    appt_datetime = datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')

    # Check if the appointment time is on the hour
    if appt_datetime.minute != 0 or appt_datetime.second != 0:
        flash('Appointments can only be booked on the hour (e.g., 1:00, 2:00).', 'error')
        return redirect(url_for('appointment'))
    
     # Check if the appointment time is in the past
    if appt_datetime < datetime.now():
        flash('Cannot book an appointment in the past. Please select a future time.', 'error')
        return redirect(url_for('appointment'))
    
    # Query the database to check if the appointment slot is already taken
    cursor.execute("""
        SELECT Appointments.* FROM Appointments
        JOIN Agents ON Appointments.CEANumber = Agents.CEANumber
        JOIN Users ON Agents.userID = Users.userID
        WHERE Users.name = %s AND Appointments.ApptDateTime = %s
    """, (agent_name, appt_datetime))
    existing_appointment = cursor.fetchone()
    
    # If an existing appointment is found, flash a message and redirect
    if existing_appointment:
        flash('This appointment slot is already taken. Please choose another date or time.', 'error')
        return redirect(url_for('appointment'))
    
    else:
        cursor.execute("""
             INSERT INTO Appointments (ApptDateTime, CEANumber, UserID)
         VALUES (%s, (SELECT CEANumber FROM Agents WHERE userID = (SELECT userID FROM Users WHERE name = %s)), %s)
     """, (appt_datetime, agent_name, user_id))
        connection.commit()
    
    # Flash success message and redirect to the appointments view page
    flash('Your appointment has been successfully booked.', 'success')
    return redirect(url_for('appointment'))

def parse_datetime(date_str, time_str):
    try:
        return datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')


@app.route('/update-appointment', methods=['POST'])
def update_appointment():
    if request.method == 'POST':
        # Create a DB connection
        connection = get_db()
        cursor = connection.cursor()

        # Get the edited appointment details from the form
        appt_id = request.form.get('apptId')
        date = request.form.get('date')
        time = request.form.get('time')
        agent_name = request.form.get('agentName')  # Ensure this field is included in your form

        # Combine date and time into a single datetime object
        appt_datetime = parse_datetime(date, time)
        print(appt_datetime)

        # Check if the appointment time is on the hour
        if appt_datetime.minute != 0 or appt_datetime.second != 0:
            flash('Appointments can only be booked on the hour (e.g., 1:00, 2:00).', 'error')
            return redirect(url_for('view_appointments'))

        # Check if the appointment time is in the past
        if appt_datetime < datetime.now():
            flash('Cannot book an appointment in the past. Please select a future time.', 'error')
            return redirect(url_for('view_appointments'))

        # Check if the new appointment time is already booked
        cursor.execute("""
            SELECT Appointments.* FROM Appointments
            JOIN Agents ON Appointments.CEANumber = Agents.CEANumber
            JOIN Users ON Agents.userID = Users.userID
            WHERE Users.name = %s AND Appointments.ApptDateTime = %s AND Appointments.ApptID != %s
        """, (agent_name, appt_datetime, appt_id))
        if cursor.fetchone():
            flash('This appointment time is already booked. Please choose another time.', 'error')
            return redirect(url_for('view_appointments'))
        else: 
            # Update the appointment in the database
            query = "UPDATE Appointments SET ApptDateTime = %s WHERE ApptID = %s"
            cursor.execute(query, (appt_datetime, appt_id))
            connection.commit()
            flash('Appointment updated successfully.', 'success')
    
       

        return redirect(url_for('view_appointments'))


@app.route('/delete-appointment', methods=['POST'])
def delete_appointment():
    if request.method == 'POST':
        try:
            # Extract appointment data from the form
            apptId = request.form.get('apptId')  # Adjust this based on your form field
            
            # Create a DB connection
            connection = get_db()
            cursor = connection.cursor()

            query = "DELETE FROM Appointments WHERE ApptID = %s"
            print(apptId)
            cursor.execute(query, apptId)
            connection.commit()
            flash('Appointment deleted successfully.', 'success')

            # Return a JSON response indicating success
            response = {'status': 'success', 'message': 'Appointment deleted successfully'}
    

    
        except pymysql.Error as e:
            connection.rollback()
            flash(f"Error deleting appointment: {e}", "error")
            response = {'status': 'error', 'message': f"Error deleting appointment: {e}"}


        finally:
            cursor.close()

        return jsonify(response)
            

@app.route('/view-appointments.html')
def view_appointments():

    # Retrieve the user's bookings from the database
    connection = get_db()
    cursor = connection.cursor()

    try:

        if 'user_id' not in session or session.get('user_type') != 'normal_user':
            flash("You need to be logged in as a homebuyer to view appointments.", "error")
            return redirect(url_for('login'))

        user_id = session['user_id']

        # Displays all agents
        query = "SELECT ap.ApptID, ap.ApptDateTime, u.name FROM Users u, Agents a, Appointments ap WHERE u.UserID = a.UserID AND a.CEANumber = ap.CEANumber AND ap.UserID = %s"
        cursor.execute(query, (user_id,))

        # Fetch all the user's appointments
        appointments = cursor.fetchall()
        
        if not appointments:
            flash("You currently have no appointments.", "info")

        return render_template("view-appointments.html", appointments=appointments)

    except pymysql.Error as e:
        flash(f"An error occurred while retrieving your appointments: {e}", "error")

    finally:
        cursor.close()

    return render_template("view-appointments.html")


@app.route('/agent/appointments')
def agent_appointments():
    if 'agent_id' not in session:
        flash("You need to log in as an agent to view appointments.", "error")
        return redirect(url_for('login'))

    agent_id = session['agent_id']
    connection = get_db()
    cursor = connection.cursor()

    # Query to fetch upcoming appointments for the agent
    query = """
    SELECT a.ApptID, a.ApptDateTime, u.name, u.email, u.phone
    FROM Appointments a
    JOIN Users u ON a.UserID = u.UserID
    WHERE a.CEANumber = %s AND a.ApptDateTime > NOW()
    ORDER BY a.ApptDateTime
    """
    cursor.execute(query, (agent_id,))
    appointments = cursor.fetchall()
    cursor.close()

    return render_template("agent-appointments.html", appointments=appointments)



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
    connection = get_db()
    cursor = connection.cursor()

    start_year = 2012
    end_year = 2021

    df_all_years = pd.DataFrame(columns=['Year', 'Price', 'Street Name', 'Block', 'Town Estate', 'Flat Type'])

    # do a query loop because if do all at once will crash, once do query loop, concat the dataframe

    for selected_year in range(start_year, end_year + 1):
    # Query for highest sales revenue location
        query = f"SELECT T.transaction_year, T.price, hdb.street_name, hdb.block, hdb.town_estate, hdb.flat_type FROM (SELECT transaction_year, hdb_id, price,STDDEV_POP(price) OVER (PARTITION BY transaction_year) AS stddev FROM Transaction WHERE transaction_year = {selected_year}) AS T JOIN HDB hdb ON T.hdb_id = hdb.hdb_id WHERE T.price > T.stddev * 3 OR T.price < T.stddev / 3 ORDER BY T.transaction_year, T.price DESC LIMIT 1;"
        cursor.execute(query)
        result = cursor.fetchall()
        df_year = pd.DataFrame(result, columns=['Year', 'Price', 'Street Name', 'Block', 'Town Estate', 'Flat Type'])
        # Concatenate the current year's results to the overall DataFrame
        df_all_years = pd.concat([df_all_years, df_year], ignore_index=True)

    df_all_years['Price'] = '$ ' + df_all_years['Price'].astype(str)
    html_table = df_all_years.to_html(classes='table table-striped table-bordered table-hover', index=False)


    return render_template("outlier-analysis.html", data=html_table)

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
    connection = get_db()
    cursor = connection.cursor()
    query = "SELECT t.transaction_year, hdb.town_estate, AVG(price) as sumOfPrices FROM Transaction t, HDB hdb WHERE t.hdb_id = hdb.hdb_id GROUP BY transaction_year, town_estate;"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    df = pd.DataFrame(result, columns=['Year', 'town_estate','Average Price'])
    figures = []
    for town_estate in df['town_estate'].unique():
        fig = go.Figure()

        # Add traces for lines and markers
        fig.add_trace(go.Scatter(
            x=df[df['town_estate'] == town_estate]['Year'],
            y=df[df['town_estate'] == town_estate]['Average Price'],
            mode='lines+markers',
            name=f'Price Trend - {town_estate}'
        ))

        # Update layout and styling if needed
        fig.update_layout(
            title=f'Price Trend Over Years (2012 - 2021) - {town_estate}',
            xaxis_title='Year',
            yaxis_title='Average Price',
        )

        figures.append(fig)
    chart_html = [fig.to_html(full_html=False) for fig in figures]
    return render_template("price-trend-analysis.html", chart_html = chart_html)

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