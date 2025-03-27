from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages

# Dummy databases (empty initially)
tuitions = {}  # Format: {"tuition_id": {"name": "Tuition Name", "password": "password"}}
users = {}     # Format: {"username": {"password": "pass", "role": "tutor/parent", "tuition_id": "id", "student_name": "name" (if parent)}}
attendance = {}  # Format: {"tuition_id": {"student_name": {"started": False, "arrived": None}}}

# Home page with tuition search
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        tuition_id = request.form['tuition_id']
        if tuition_id in tuitions:
            return redirect(url_for('role_select', tuition_id=tuition_id))
        else:
            flash("Tuition ID not found!")
    return render_template('home.html')

# Role selection page (requires tuition password)
@app.route('/role_select/<tuition_id>', methods=['GET', 'POST'])
def role_select(tuition_id):
    if request.method == 'POST':
        password = request.form['password']
        if tuitions.get(tuition_id, {}).get("password") == password:
            role = request.form['role']
            if role == "register":
                return redirect(url_for('register', tuition_id=tuition_id))
            elif role == "tutor":
                return redirect(url_for('login', tuition_id=tuition_id, role="tutor"))
            elif role == "parent":
                return redirect(url_for('login', tuition_id=tuition_id, role="parent"))
        else:
            flash("Incorrect tuition password!")
    return render_template('role_select.html', tuition_id=tuition_id)

# New tuition creation (tutors only)
@app.route('/new_tuition', methods=['GET', 'POST'])
def new_tuition():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        tuition_id = request.form['tuition_id']
        tuition_name = request.form['tuition_name']

        if username in users:
            flash("Username already taken!")
            return render_template('new_tuition.html')
        if tuition_id in tuitions:
            flash("Tuition ID already exists!")
            return render_template('new_tuition.html')
        if not tuition_name:
            flash("Tuition name is required!")
            return render_template('new_tuition.html')

        # Create new tuition and register tutor
        tuitions[tuition_id] = {"name": tuition_name, "password": password}
        users[username] = {"password": password, "role": "tutor", "tuition_id": tuition_id}
        attendance[tuition_id] = {}
        flash("New tuition created successfully! Please search for your tuition ID to login.")
        return redirect(url_for('home'))

    return render_template('new_tuition.html')

# Registration page (parents only, for existing tuitions)
@app.route('/register/<tuition_id>', methods=['GET', 'POST'])
def register(tuition_id):
    if tuition_id not in tuitions:
        flash("Tuition ID does not exist! Only tutors can create new tuitions.")
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        student_name = request.form['student_name']

        if username in users:
            flash("Username already taken!")
            return render_template('register.html', tuition_id=tuition_id)
        if not student_name:
            flash("Student name is required!")
            return render_template('register.html', tuition_id=tuition_id)

        # Register parent under existing tuition
        users[username] = {"password": password, "role": "parent", "tuition_id": tuition_id, "student_name": student_name}
        if tuition_id not in attendance:
            attendance[tuition_id] = {}
        attendance[tuition_id][student_name] = {"started": False, "arrived": None}
        flash("Registration successful! Please search for your tuition ID to login.")
        return redirect(url_for('home'))

    return render_template('register.html', tuition_id=tuition_id)

# Login page
@app.route('/login/<tuition_id>/<role>', methods=['GET', 'POST'])
def login(tuition_id, role):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if (username in users and users[username]["password"] == password and 
            users[username]["tuition_id"] == tuition_id and users[username]["role"] == role):
            if role == "tutor":
                return redirect(url_for('tutor_dashboard', username=username))
            elif role == "parent":
                return redirect(url_for('parent_dashboard', username=username))
        else:
            flash("Invalid credentials!")
    return render_template('login.html', tuition_id=tuition_id, role=role)

# Tutor Dashboard
@app.route('/tutor_dashboard/<username>', methods=['GET', 'POST'])
def tutor_dashboard(username):
    tuition_id = users[username]["tuition_id"]
    if request.method == 'POST':
        student_name = request.form['student_name']
        arrived = request.form.get('arrived') == "on"
        attendance[tuition_id][student_name]["arrived"] = arrived
        flash("Attendance updated!")
    tuition_name = tuitions[tuition_id]["name"]
    return render_template('tutor_dashboard.html', username=username, tuition_id=tuition_id, 
                          tuition_name=tuition_name, attendance=attendance[tuition_id])

# Parent Dashboard
@app.route('/parent_dashboard/<username>', methods=['GET', 'POST'])
def parent_dashboard(username):
    tuition_id = users[username]["tuition_id"]
    student_name = users[username]["student_name"]
    if request.method == 'POST':
        started = request.form.get('started') == "on"
        attendance[tuition_id][student_name]["started"] = started
        flash("Status updated!")
    tuition_name = tuitions[tuition_id]["name"]
    return render_template('parent_dashboard.html', username=username, tuition_id=tuition_id, 
                          tuition_name=tuition_name, student_name=student_name, 
                          attendance=attendance[tuition_id])

if __name__ == '__main__':
    app.run(debug=True)