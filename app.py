import textwrap
from flask import (
    Flask,
    render_template,
    g,
    flash,
    redirect,
    url_for,
    request,
    jsonify,
    session,
    
)

from flask import Flask, request, jsonify
import pymongo, re
from forms import RegistrationForm, LoginForm, AddListingForm
import pymysql
from sshtunnel import SSHTunnelForwarder
from passlib.hash import pbkdf2_sha256
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


app = Flask(__name__, template_folder="templates")
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

app.config["SECRET_KEY"] = "1234"

# MySQL configuration
db_config = {
    "user": "root",
    "password": "iLoveRoots99",
    "db": "inf2003projectdb",
}


# SSH Tunnel Setup
def create_ssh_tunnel():
    try:
        server = SSHTunnelForwarder(
            "35.212.167.35",
            ssh_username="dev",
            ssh_password="iLoveDonuts99",
            ssh_port=22,
            remote_bind_address=("127.0.0.1", 3306),
        )
        server.start()
        return server

    except Exception as e:
        return None


# Create the SSH tunnel when the application starts
ssh_server = create_ssh_tunnel()


# Function for creating DB Connection
def get_db():
    if not hasattr(g, "db_connection"):
        ssh_server = create_ssh_tunnel()

        if ssh_server is None:
            # Handle the case where the SSH tunnel failed to establish
            flash(
                "SSH tunnel failed to establish. Error: Unable to connect to the SSH server."
            )
            return None

        g.db_connection = pymysql.connect(
            host="127.0.0.1", port=ssh_server.local_bind_port, **db_config
        )

    return g.db_connection


# # Landing Page
# @app.route("/")
# def index():
#     if ssh_server is None:
#         flash(
#             "SSH tunnel failed to establish. Error: Unable to connect to the SSH server."
#         )
#     return render_template("index.html")


@app.route("/toggle_favorites/<int:listing_id>", methods=["POST"])
def toggle_favorites(listing_id):
    # Connect to database and set cursor
    connection = get_db()
    cursor = connection.cursor()

    user_id = session["user_id"]

    if user_id is None:
        # Handle the case when user is not logged in
        return jsonify({"success": False, "message": "User not logged in"})

    # Check if the listing is already a favorite for the user
    cursor.execute("SELECT * FROM Favorites WHERE user_id = %s AND listing_id = %s", (user_id, listing_id))
    existing_favorite = cursor.fetchone()

    if existing_favorite:
        # Listing is already a favorite, handle accordingly
        return jsonify({"success": False, "message": "Listing is already in favorites"})
    
    # Add the listing to favorites
    cursor.execute("INSERT INTO Favorites (user_id, listing_id) VALUES (%s, %s)", (user_id, listing_id))
    connection.commit()

    return jsonify({"success": True, "is_favorite": True})

@app.route("/favorites", methods=["GET"])
def favorites():
    # Connect to database and set cursor
    connection = get_db()
    cursor = connection.cursor()

    user_id = session.get("user_id")

    # Fetch the favorites for the current user directly from the Favorites table
    favorites_query = """
    SELECT *
    FROM Favorites
    WHERE user_id = %s
    """
    cursor.execute(favorites_query, (user_id,))
    favorites = cursor.fetchall()

    cursor.close()

    return jsonify({"status": "success", "favorites": favorites})

@app.route("/", methods=["GET", "POST"])
def propertylist():
    # Connect to database and set cursor
    connection = get_db()
    cursor = connection.cursor()

    listings_query = """
                     SELECT listingID, block, street_name, price, floorAreaSQM, flat_type 
                     FROM Listings
    """

    # Fetch listings from the database
    cursor.execute(listings_query)
    listings = cursor.fetchall()

    # Fetch distinct flat types for displaying form options
    cursor.execute("SELECT DISTINCT flat_type FROM Listings")
    flat_types = cursor.fetchall()

    # Fetch distinct town estates for displaying location options
    cursor.execute("SELECT DISTINCT town_estate FROM Listings")
    locations = cursor.fetchall()

    # Fetch the favorites for the current user directly from the Favorites table
    user_id = session.get("user_id")

    favorites_query = """
                      SELECT L.listingID, L.block, L.street_name, L.price, L.floorAreaSQM, L.flat_type
                      FROM Listings L
                      JOIN Favorites F ON L.listingID = F.listing_id
                      WHERE F.user_id = %s
    """
    
    cursor.execute(favorites_query, (user_id,))
    favorites = cursor.fetchall()

    # Get search/filter inputs
    search_keyword = request.form.get("search_keyword")
    flat_type = request.form.get("flat_type")
    location = request.form.get("location")

    # Handling form submission for search and filter
    if request.method == "POST":
        query = """
                SELECT listingID, block, street_name, price, floorAreaSQM, flat_type 
                FROM Listings 
                WHERE 1=1
        """
        params = {}

        conditions = []

        if search_keyword:
            conditions.append("(block LIKE %(search)s OR street_name LIKE %(search)s)")
            params["search"] = f"%{search_keyword}%"

        if flat_type != "Flat Type":
            conditions.append("flat_type = %(flat_type)s")
            params["flat_type"] = flat_type

        if location != "Location":
            conditions.append("town_estate = %(location)s")
            params["location"] = location

        if conditions:
            query += " AND " + " AND ".join(conditions)

        # Execute the filtered query with parameters
        cursor.execute(query, params)
        listings = cursor.fetchall()

    cursor.close()   

    return render_template(
        "property-list.html",
        listings=listings,
        flat_types=flat_types,
        locations=locations,
        search_keyword=search_keyword,
        selected_flat_type=flat_type,
        selected_location=location,
        favorites=favorites
    )

@app.route("/listing-details/<int:listing_id>", methods=["GET", "POST"])
def listing_details(listing_id):
   # Connect to database and set cursor
    connection = get_db()
    cursor = connection.cursor()
        
    # Fetch listings
    cursor.execute(
        "SELECT * FROM Listings WHERE listingID = %s", (listing_id)
    )

    listing = cursor.fetchone()

    if listing:
        listing_id, block, street_name, floor_area_sqm, town_estate, flat_type, price, desc, cea_num = listing


    # Fetch agent's title and name based on the CEA number by joining Agents and Users tables
    agent_query = """
                  SELECT Agents.agentTitle, Users.name 
                  FROM Agents 
                  JOIN Users ON Agents.userID = Users.userID 
                  WHERE Agents.CEANumber = %s
    """
    cursor.execute(agent_query, (cea_num,))
    
    agent_info = cursor.fetchone()  # Fetch agent's title and name

    if agent_info:
        agent_title, agent_name = agent_info  # Extract agent's title and name
    else:
        agent_title, agent_name = None, None  # Set to none if agent not found

    cursor.close()

    # Retrieve reviews from MongoDB
    db = client["agent_reviews"]
    collection = db["agent_reviews"]

    pipeline = [
        {"$match": {"agentName": {"$regex": agent_name, "$options": "i"}}},
        {
            "$project": {
                "agentName": 1,
                "reviews": 1,
                "agencyLicenseNo": 1,
                "CEANumber": 1,
                "_id": 0,
                "averageRating": {"$avg": "$reviews.rating"},
            }
        },
    ]

    results = collection.aggregate(pipeline)

    reviews = []

    for result in results:
        reviews = result['reviews']

    return render_template("listing-details.html",
                           listing_id=listing_id, 
                           block=block, 
                           street_name=street_name, 
                           floor_area_sqm=floor_area_sqm, 
                           town_estate=town_estate, 
                           flat_type=flat_type, 
                           price=price, 
                           desc=desc,
                           cea_num=cea_num,
                           agent_title=agent_title,
                           agent_name=agent_name,
                           reviews=reviews
                           )


@app.route("/register.html", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = pbkdf2_sha256.hash(form.password.data)

        # Connect to your database
        connection = get_db()
        cursor = connection.cursor()

        # Insert user into Users table
        user_query = (
            "INSERT INTO Users (name, email, phone, password) VALUES (%s, %s, %s, %s)"
        )
        user_values = (
            form.username.data,
            form.email.data,
            form.phone.data,
            hashed_password,
        )
        cursor.execute(user_query, user_values)
        user_id = cursor.lastrowid
        connection.commit()

        if form.role.data == "agent":
            # Insert additional agent details into Agents table
            agent_query = "INSERT INTO Agents (CEANumber, agencyLicenseNo, agentTitle, userID) VALUES (%s, %s, %s, %s)"
            agent_values = (
                form.CEANumber.data,
                form.agencyLicenseNo.data,
                form.agentTitle.data,
                user_id,
            )
            cursor.execute(agent_query, agent_values)
            connection.commit()

        flash("Thank you for registering! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login.html", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        connection = get_db()
        cursor = connection.cursor()

        # Query to check user credentials
        query = """
                SELECT userID, password
                FROM Users WHERE email = %s
        """
        cursor.execute(query, (form.email.data,))
        result = cursor.fetchone()

        if result is not None:
            user_id, stored_hashed_password = result

            # if pbkdf2_sha256.verify(form.password.data, stored_hashed_password):
            if True:
                # Check if the user is an agent
                agent_query = """
                              SELECT CEANumber 
                              FROM Agents 
                              WHERE userID = %s
                """
                cursor.execute(agent_query, (user_id,))
                agent_result = cursor.fetchone()

                # Set user type in session
                session["user_id"] = user_id
                if agent_result is not None:
                    session["user_type"] = "agent"
                    session["agent_id"] = user_id
                    session["CEANumber"] = agent_result[0]
                else:
                    session["user_type"] = "normal_user"

                flash(f"Login successful, welcome {form.email.data}!", "success")
                return redirect(url_for("propertylist"))
            else:
                flash("Invalid email or password.", "error")
        else:
            flash("Invalid email or password.", "error")

        cursor.close()

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    # Remove user_id and other user-related information from session
    session.pop("user_id", None)
    session.pop("user_type", None)
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("login"))


@app.route("/add_listing.html", methods=["GET", "POST"])
def add_listing():
    form = AddListingForm()

    if form.validate_on_submit():
        # Connect to your database
        connection = get_db()
        cursor = connection.cursor()

        # Insert listing details into Listings table
        new_listing_query = """
                        INSERT INTO Listings (block, street_name, floorAreaSQM, town_estate, flat_type, price, listing_desc, CEANumber)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        listing_values = (
            form.block.data,
            form.street_name.data,
            form.floorAreaSQM.data,
            form.town_estate.data,
            form.flat_type.data,
            form.price.data,
            form.listing_desc.data,
            session["CEANumber"],
        )
        cursor.execute(new_listing_query, listing_values)
        connection.commit()
        cursor.close()

        flash("Listing Successfully Added", "success")
        return redirect(url_for("propertylist"))

    return render_template("add_listing.html", form=form)


@app.route("/about.html")
def about():
    return render_template("about.html")


@app.route("/contact.html")
def contact():
    return render_template("contact.html")


@app.route("/property-agent.html")
def propertyagent():
    return render_template("property-agent.html")


@app.route("/property-type.html")
def propertytype():
    return render_template("property-type.html")


@app.route("/analysis.html")
def analysis():
    return render_template("analysis.html")


@app.route("/404.html")
def error404():
    return render_template("404.html")


@app.route("/appointment.html", methods=["GET", "POST"])
def appointment():
    # Initialize MongoDB connection
    client = pymongo.MongoClient(uri)
    db = client["agent_reviews"]
    collection = db["agent_reviews"]

    # Initialize MySQL connection
    connection = get_db()
    cursor = connection.cursor()

    # Retrieve available agency names and agent titles for dropdowns
    cursor.execute("SELECT DISTINCT agencyName FROM Agency")
    agency_names = cursor.fetchall()
    cursor.execute("SELECT DISTINCT agentTitle FROM Agents")
    agent_titles = cursor.fetchall()

    # Handle filters and search query from the form
    filter_agency_name = request.form.get("filter_agency_name")
    filter_agent_title = request.form.get("filter_agent_title")
    review_filter = request.form.get("review_filter")
    search_query = request.args.get("search_query", "").strip()
    print()

    # Base query for MySQL
    base_query = "SELECT u.name, a.agentTitle, a.CEANumber, ag.agencyName FROM Users u JOIN Agents a ON u.userID = a.userID JOIN Agency ag ON a.agencyLicenseNo = ag.agencyLicenseNo"

    # Apply filters
    conditions = []
    params = []
    if filter_agency_name:
        conditions.append("ag.agencyName = %s")
        params.append(filter_agency_name)
    if filter_agent_title:
        conditions.append("a.agentTitle = %s")
        params.append(filter_agent_title)
    if search_query:
        conditions.append("u.name LIKE %s")
        params.append(f"%{search_query}%")

    # Adding WHERE clause if there are filter conditions
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    cursor.execute(base_query, params)
    agents = cursor.fetchall()

    # Combine MySQL and MongoDB data
    combined_agents = []
    for agent in agents:
        agent_name = agent[0]  # The agent's name
        safe_agent_name = re.escape(agent_name.strip())

        # Fetch the average rating from MongoDB
        avg_rating_pipeline = [
            {"$match": {"agentName": {"$regex": f"^{safe_agent_name}$", "$options": "i"}}},
            {"$unwind": "$reviews"},
            {"$group": {"_id": None, "averageRating": {"$avg": "$reviews.rating"}}}
        ]

        avg_rating_result = list(collection.aggregate(avg_rating_pipeline))
        avg_rating = avg_rating_result[0]["averageRating"] if avg_rating_result else None

        # Filter based on review rating, if specified
        if review_filter and (avg_rating is None or avg_rating < float(review_filter)):
            continue  # Skip this agent if average rating is below the filter threshold

        # Append agent details with average rating
        combined_agents.append((*agent, avg_rating))

    return render_template("appointment.html", agents=combined_agents, agency_names=agency_names, agent_titles=agent_titles)



@app.route("/create-appointment", methods=["POST"])
def create_appointment():
    if "user_id" not in session or session.get("user_type") != "normal_user":
        flash("You need to be logged in as a homebuyer to view appointments.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    agent_name = request.form["agentName"]
    date = request.form["date"]
    time = request.form["time"]

    connection = get_db()
    cursor = connection.cursor()

    # Combine date and time into a single datetime object
    appt_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    # Check if the appointment time is on the hour
    if appt_datetime.minute != 0 or appt_datetime.second != 0:
        flash(
            "Appointments can only be booked on the hour (e.g., 1:00, 2:00).", "error"
        )
        return redirect(url_for("appointment"))

    # Check if the appointment time is in the past
    if appt_datetime < datetime.now():
        flash(
            "Cannot book an appointment in the past. Please select a future time.",
            "error",
        )
        return redirect(url_for("appointment"))

    # Query the database to check if the appointment slot is already taken
    cursor.execute(
        """
        SELECT Appointments.* FROM Appointments
        JOIN Agents ON Appointments.CEANumber = Agents.CEANumber
        JOIN Users ON Agents.userID = Users.userID
        WHERE Users.name = %s AND Appointments.ApptDateTime = %s
    """,
        (agent_name, appt_datetime),
    )
    existing_appointment = cursor.fetchone()

    # If an existing appointment is found, flash a message and redirect
    if existing_appointment:
        flash(
            "This appointment slot is already taken. Please choose another date or time.",
            "error",
        )
        return redirect(url_for("appointment"))

    else:
        cursor.execute(
            """
             INSERT INTO Appointments (ApptDateTime, CEANumber, UserID)
         VALUES (%s, (SELECT CEANumber FROM Agents WHERE userID = (SELECT userID FROM Users WHERE name = %s)), %s)
     """,
            (appt_datetime, agent_name, user_id),
        )
        connection.commit()

    # Flash success message and redirect to the appointments view page
    flash("Your appointment has been successfully booked.", "success")
    return redirect(url_for("appointment"))


def parse_datetime(date_str, time_str):
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")


@app.route("/update-appointment", methods=["POST"])
def update_appointment():
    if request.method == "POST":
        # Create a DB connection
        connection = get_db()
        cursor = connection.cursor()

        # Get the edited appointment details from the form
        appt_id = request.form.get("apptId")
        date = request.form.get("date")
        time = request.form.get("time")
        agent_name = request.form.get("agentName")

        # Combine date and time into a single datetime object
        appt_datetime = parse_datetime(date, time)
        print(appt_datetime)

        # Check if the appointment time is on the hour
        if appt_datetime.minute != 0 or appt_datetime.second != 0:
            flash(
                "Appointments can only be booked on the hour (e.g., 1:00, 2:00).",
                "error",
            )
            return redirect(url_for("view_appointments"))

        # Check if the appointment time is in the past
        if appt_datetime < datetime.now():
            flash(
                "Cannot book an appointment in the past. Please select a future time.",
                "error",
            )
            return redirect(url_for("view_appointments"))

        # Check if the new appointment time is already booked
        cursor.execute(
            """
            SELECT Appointments.* FROM Appointments
            JOIN Agents ON Appointments.CEANumber = Agents.CEANumber
            JOIN Users ON Agents.userID = Users.userID
            WHERE Users.name = %s AND Appointments.ApptDateTime = %s AND Appointments.ApptID != %s
        """,
            (agent_name, appt_datetime, appt_id),
        )
        if cursor.fetchone():
            flash(
                "This appointment time is already booked. Please choose another time.",
                "error",
            )
            return redirect(url_for("view_appointments"))
        else:
            # Update the appointment in the database
            query = "UPDATE Appointments SET ApptDateTime = %s WHERE ApptID = %s"
            cursor.execute(query, (appt_datetime, appt_id))
            connection.commit()
            flash("Appointment updated successfully.", "success")

        return redirect(url_for("view_appointments"))


@app.route("/delete-appointment", methods=["POST"])
def delete_appointment():
    if request.method == "POST":
        try:
            # Extract appointment data from the form
            apptId = request.form.get("apptId")

            connection = get_db()
            cursor = connection.cursor()

            query = "DELETE FROM Appointments WHERE ApptID = %s"
            print(apptId)
            cursor.execute(query, apptId)
            connection.commit()
            flash("Appointment deleted successfully.", "success")

            # Return a JSON response indicating success
            response = {
                "status": "success",
                "message": "Appointment deleted successfully",
            }

        except pymysql.Error as e:
            connection.rollback()
            flash(f"Error deleting appointment: {e}", "error")
            response = {
                "status": "error",
                "message": f"Error deleting appointment: {e}",
            }

        finally:
            cursor.close()

        return jsonify(response)


@app.route("/view-appointments.html")
def view_appointments():
    if "user_id" not in session or session.get("user_type") != "normal_user":
        flash("You need to be logged in as a homebuyer to view appointments.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    connection = get_db()
    cursor = connection.cursor()

    search_query = request.args.get("search_query", "").strip()
    appointment_filter = request.args.get("filter", "upcoming")

    try:
        base_query = """
        SELECT ap.ApptID, ap.ApptDateTime, u.name, a.agentTitle, a.CEANumber
        FROM Appointments ap
        JOIN Agents a ON a.CEANumber = ap.CEANumber
        JOIN Users u ON a.userID = u.userID
        WHERE ap.UserID = %s
        """

        search_query_part = ""
        if search_query:
            search_query_part = (
                " AND (u.name LIKE %s OR a.agentTitle LIKE %s OR a.CEANumber LIKE %s)"
            )
            search_term = f"%{search_query}%"

        filter_query = ""
        if appointment_filter == "past":
            filter_query = " AND ap.ApptDateTime < NOW()"
        elif appointment_filter == "upcoming":
            filter_query = " AND ap.ApptDateTime > NOW()"

        final_query = base_query + search_query_part + filter_query
        final_query += " ORDER BY ap.ApptDateTime"

        if search_query:
            cursor.execute(
                final_query, (user_id, search_term, search_term, search_term)
            )
        else:
            cursor.execute(final_query, (user_id,))

        appointments = cursor.fetchall()
        print(appointments)

        if not appointments:
            flash("You currently have no appointments.", "info")

        return render_template(
            "view-appointments.html",
            appointments=appointments,
            filter=appointment_filter,
        )

    except pymysql.Error as e:
        flash(f"An error occurred while retrieving your appointments: {e}", "error")

    finally:
        cursor.close()

    return render_template("view-appointments.html")


@app.route("/agent/appointments", methods=["GET"])
def agent_appointments():
    if "agent_id" not in session:
        flash("You need to log in as an agent to view appointments.", "error")
        return redirect(url_for("login"))

    agent_cea = session["CEANumber"]
    connection = get_db()
    cursor = connection.cursor()

    search_query = request.args.get("search_query", "").strip()
    appointment_filter = request.args.get("filter", "upcoming")

    try:
        base_query = """
        SELECT ap.ApptID, ap.ApptDateTime, u.name, u.email, u.phone 
        FROM Appointments ap 
        JOIN Users u ON ap.userID = u.userID 
        WHERE ap.CEANumber = %s
        """

        filter_query = ""
        if appointment_filter == "past":
            filter_query = " AND ap.ApptDateTime < NOW()"
        elif appointment_filter == "upcoming":
            filter_query = " AND ap.ApptDateTime > NOW()"

        search_query_part = ""
        if search_query:
            search_query_part = " AND (u.name LIKE %s OR u.email LIKE %s)"
            search_term = f"%{search_query}%"

        final_query = base_query + filter_query + search_query_part

        if search_query:
            cursor.execute(final_query, (agent_cea, search_term, search_term))
        else:
            cursor.execute(final_query, (agent_cea,))

        appointments = cursor.fetchall()
        return render_template("agent-appointments.html", appointments=appointments)

    except pymysql.Error as e:
        flash(f"An error occurred while retrieving appointments: {e}", "error")

    finally:
        cursor.close()

    return render_template("agent-appointments.html")


@app.route("/location-analysis.html")
def locationanalysis():
    connection = get_db()
    cursor = connection.cursor()

    # Query for highest sales revenue location
    query = "SELECT transaction_year as Year, town_estate as TownEstate, total_price as TotalCost FROM (SELECT transaction_year, town_estate, SUM(price) AS total_price, ROW_NUMBER() OVER (PARTITION BY transaction_year ORDER BY SUM(price) DESC) AS rowNumber FROM HDB hdb JOIN Transaction t ON hdb.hdb_id = t.hdb_id GROUP BY transaction_year, town_estate ORDER BY transaction_year, total_price DESC) AS t WHERE t.rowNumber = 1 ORDER BY transaction_year;"
    cursor.execute(query)
    result = cursor.fetchall()
    df = pd.DataFrame(result, columns=["Year", "Town Estate", "Total Sales Revenue"])
    # Add $ to the 'Cost' column
    df["Total Sales Revenue"] = "$ " + df["Total Sales Revenue"].astype(str)
    html_table = df.to_html(
        classes="table table-striped table-bordered table-hover", index=False
    )

    # Create a new cursor for the second query
    cursor1 = connection.cursor()

    # Query for lowest sales revenue location
    query1 = "SELECT transaction_year as Year, town_estate as TownEstate, total_price as TotalCost FROM (SELECT transaction_year, town_estate, SUM(price) AS total_price, ROW_NUMBER() OVER (PARTITION BY transaction_year ORDER BY SUM(price) ASC) AS rowNumber FROM HDB hdb JOIN Transaction t ON hdb.hdb_id = t.hdb_id GROUP BY transaction_year, town_estate ORDER BY transaction_year, total_price ASC) AS t WHERE t.rowNumber = 1 ORDER BY transaction_year;"
    cursor1.execute(query1)
    result1 = cursor1.fetchall()
    df1 = pd.DataFrame(result1, columns=["Year", "Town Estate", "Total Sales Revenue"])
    # Add $ to the 'Cost' column
    df1["Total Sales Revenue"] = "$ " + df1["Total Sales Revenue"].astype(str)
    html_table1 = df1.to_html(
        classes="table table-striped table-bordered table-hover", index=False
    )

    cursor.close()
    cursor1.close()

    return render_template("location-analysis.html", data=html_table, data1=html_table1)


@app.route("/size-analysis.html")
def sizeanalysis():
    connection = get_db()
    cursor = connection.cursor()
    query = "SELECT t.transaction_year,h.town_estate, CASE WHEN h.floorAreaSQM <= 50 THEN '0-50 sqm' WHEN h.floorAreaSQM <= 100 THEN '51-100 sqm' WHEN h.floorAreaSQM <= 150 THEN '101-150 sqm' ELSE '151+ sqm' END AS sqm_range, ROUND(AVG(t.price), 2) AS mean_price FROM Transaction t JOIN HDB h ON t.hdb_id = h.hdb_id GROUP BY t.transaction_year,h.town_estate,sqm_range;"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    df = pd.DataFrame(
        result, columns=["transaction_year", "town_estate", "sqm_range", "mean_price"]
    )
    figures = []
    for town_estate in df["town_estate"].unique():
        fig = px.line(
            df[df["town_estate"] == town_estate],
            x="transaction_year",
            y="mean_price",
            color="sqm_range",
            markers=True,
            title=f"Mean Price Over Years - {town_estate}",
        )

        figures.append(fig)

    # Convert the Plotly figures to HTML
    chart_html = [fig.to_html(full_html=False) for fig in figures]
    return render_template("size-analysis.html", chart_html=chart_html)


@app.route("/outlier-analysis.html")
def outlieranalysis():
    connection = get_db()
    cursor = connection.cursor()

    start_year = 2012
    end_year = 2021

    df_all_years = pd.DataFrame(
        columns=["Year", "Price", "Street Name", "Block", "Town Estate", "Flat Type"]
    )

    # do a query loop because if do all at once will crash, once do query loop, concat the dataframe

    for selected_year in range(start_year, end_year + 1):
        # Query for highest sales revenue location
        query = f"SELECT T.transaction_year, T.price, hdb.street_name, hdb.block, hdb.town_estate, hdb.flat_type FROM (SELECT transaction_year, hdb_id, price,STDDEV_POP(price) OVER (PARTITION BY transaction_year) AS stddev FROM Transaction WHERE transaction_year = {selected_year}) AS T JOIN HDB hdb ON T.hdb_id = hdb.hdb_id WHERE T.price > T.stddev * 3 OR T.price < T.stddev / 3 ORDER BY T.transaction_year, T.price DESC LIMIT 1;"
        cursor.execute(query)
        result = cursor.fetchall()
        df_year = pd.DataFrame(
            result,
            columns=[
                "Year",
                "Price",
                "Street Name",
                "Block",
                "Town Estate",
                "Flat Type",
            ],
        )
        # Concatenate the current year's results to the overall DataFrame
        df_all_years = pd.concat([df_all_years, df_year], ignore_index=True)

    df_all_years["Price"] = "$ " + df_all_years["Price"].astype(str)
    html_table = df_all_years.to_html(
        classes="table table-striped table-bordered table-hover", index=False
    )

    return render_template("outlier-analysis.html", data=html_table)


@app.route("/time-series-analysis.html")
def timeseriesanalysis():
    connection = get_db()
    cursor = connection.cursor()
    query = "SELECT h.town_estate, t.transaction_year,CASE WHEN t.transaction_month IN (1, 2, 3) THEN 'Q1' WHEN t.transaction_month IN (4, 5, 6) THEN 'Q2' WHEN t.transaction_month IN (7, 8, 9) THEN 'Q3' WHEN t.transaction_month IN (10, 11, 12) THEN 'Q4' END AS quarter, AVG(t.price) AS mean_price FROM Transaction t JOIN HDB h ON t.hdb_id = h.hdb_id WHERE t.transaction_month IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12) GROUP BY h.town_estate, t.transaction_year, quarter ORDER BY h.town_estate, t.transaction_year, quarter;"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    df = pd.DataFrame(
        result, columns=["town_estate", "transaction_year", "quarter", "mean_price"]
    )
    figures = []
    for town_estate in df["town_estate"].unique():
        fig = px.line(
            df[df["town_estate"] == town_estate],
            x="quarter",
            y="mean_price",
            color="transaction_year",
            markers=True,
            title=f"Mean Price Over Years - {town_estate}",
        )

        figures.append(fig)
    # Convert the Plotly figures to HTML
    chart_html = [fig.to_html(full_html=False) for fig in figures]
    return render_template("time-series-analysis.html", chart_html=chart_html)


@app.route("/price-trend-analysis.html")
def pricetrendanalysis():
    connection = get_db()
    cursor = connection.cursor()
    query = "SELECT t.transaction_year, hdb.town_estate, AVG(price) as sumOfPrices FROM Transaction t, HDB hdb WHERE t.hdb_id = hdb.hdb_id GROUP BY transaction_year, town_estate;"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    df = pd.DataFrame(result, columns=["Year", "town_estate", "Average Price"])
    figures = []
    for town_estate in df["town_estate"].unique():
        fig = go.Figure()

        # Add traces for lines and markers
        fig.add_trace(
            go.Scatter(
                x=df[df["town_estate"] == town_estate]["Year"],
                y=df[df["town_estate"] == town_estate]["Average Price"],
                mode="lines+markers",
                name=f"Price Trend - {town_estate}",
            )
        )

        # Update layout and styling if needed
        fig.update_layout(
            title=f"Price Trend Over Years (2012 - 2021) - {town_estate}",
            xaxis_title="Year",
            yaxis_title="Average Price",
        )

        figures.append(fig)
    chart_html = [fig.to_html(full_html=False) for fig in figures]
    return render_template("price-trend-analysis.html", chart_html=chart_html)


@app.route("/rooms-analysis.html")
def roomsanalysis():
    connection = get_db()
    cursor = connection.cursor()
    query = "SELECT t.transaction_year, h.town_estate, ROUND(AVG(t.price), 2) AS mean_price, h.flat_type FROM Transaction t JOIN HDB h ON t.hdb_id = h.hdb_id GROUP BY t.transaction_year, h.town_estate, h.flat_type;"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    df = pd.DataFrame(
        result, columns=["transaction_year", "town_estate", "mean_price", "flat_type"]
    )
    figures = []
    for town_estate in df["town_estate"].unique():
        fig = px.line(
            df[df["town_estate"] == town_estate],
            x="transaction_year",
            y="mean_price",
            color="flat_type",
            markers=True,
            title=f"Mean Price Over Years - {town_estate}",
        )

        figures.append(fig)
    # Convert the Plotly figures to HTML
    chart_html = [fig.to_html(full_html=False) for fig in figures]
    return render_template("rooms-analysis.html", chart_html=chart_html)


# Teardown function to close the database connection
@app.teardown_appcontext
def close_db_connection(exception):
    db_connection = getattr(g, "db_connection", None)
    if db_connection is not None:
        db_connection.close()


# if __name__ == "__main__":
#     app.run(debug=True)


# ------------------------------------------------------------------------------------------------------------------------------------
# MongoDB
# ------------------------------------------------------------------------------------------------------------------------------------
# MongoDB


uri = "mongodb+srv://Team15Database:coldplay@dbproject.9wftjq5.mongodb.net/"
client = pymongo.MongoClient(uri)
db = client.test

# app = Flask(__name__)


@app.route("/search_agents", methods=["GET"])
def search_agents():
    print("Connected to MongoDB")
    query = request.args.get("query")

    db = client["agent_reviews"]
    collection = db["agent_reviews"]
    print(f"Searching for: {query}")

    pipeline = [
        {"$match": {"agentName": {"$regex": query, "$options": "i"}}},
        {
            "$project": {
                "agentName": 1,
                "reviews": 1,
                "agencyLicenseNo": 1,
                "CEANumber": 1,
                "_id": 0,
                "averageRating": {"$avg": "$reviews.rating"},
            }
        },
    ]

    results = collection.aggregate(pipeline)

    results_list = list(results)
    print(f"Found {len(results_list)} results")
    return jsonify(results_list)


@app.route("/add_review", methods=["POST"])
def add_review():
    agent_name = request.form.get(
        "agentName"
    )  # Use the 'name' attribute of the form inputs to access the data
    review_content = request.form.get("review")
    review_rating = request.form.get("rating")

    if agent_name and review_content and review_rating:
        # Your logic to insert the review into MongoDB
        db = client["agent_reviews"]
        collection = db["agent_reviews"]
        new_review = {
            "content": review_content,
            "rating": float(review_rating),  # Ensure rating is a float
        }
        collection.update_one(
            {"agentName": agent_name}, {"$push": {"reviews": new_review}}
        )
        return jsonify({"message": "Review added successfully"}), 200
    else:
        return jsonify({"error": "Missing data"}), 400


@app.route("/delete_review", methods=["DELETE"])
def delete_review():
    agent_name = request.args.get("agentName")
    review_content = request.args.get("reviewContent")
    review_rating = float(request.args.get("reviewRating"))

    db = client["agent_reviews"]
    collection = db["agent_reviews"]
    result = collection.update_one(
        {"agentName": agent_name},
        {"$pull": {"reviews": {"content": review_content, "rating": review_rating}}},
    )

    if result.modified_count > 0:
        return jsonify({"message": "Review deleted successfully"}), 200
    else:
        return jsonify({"error": "Review not found or deletion failed"}), 400

@app.route("/update_review", methods=["POST"])
def update_review():
    agent_name = request.form.get("agentName")
    updated_content = request.form.get("updatedReview")  # Use "updatedReview" as the name attribute in the form
    updated_rating = float(request.form.get("rating"))

    if agent_name and updated_content and updated_rating:
        db = client["agent_reviews"]
        collection = db["agent_reviews"]
        
        # Update the review with matching agent name and review content
        result = collection.update_one(
            {"agentName": agent_name, "reviews.content": request.form.get("review")},  # Use "review" as the name attribute in the form
            {
                "$set": {
                    "reviews.$.content": updated_content,
                    "reviews.$.rating": updated_rating,
                }
            }
        )

        if result.modified_count > 0:
            return jsonify({"message": "Review updated successfully"}), 200
        else:
            return jsonify({"error": "Review not found or update failed"}), 400
    else:
        return jsonify({"error": "Missing data"}), 400

if __name__ == "__main__":
    app.run(debug=True)

# ------------------------------------------------------------------------------------------------------------------------------------
