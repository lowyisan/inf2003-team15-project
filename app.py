from flask import Flask, render_template

app = Flask(__name__, template_folder="templates")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/')
def index():
    return render_template("index.html")

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




if __name__ == "__main__":
    app.run(debug=True)