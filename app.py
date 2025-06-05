
from cs50 import SQL
from flask import Flask, redirect, render_template, flash, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, gc_content, transcript, translate, find_motif, orf_search, isRNA, valid_str_parameter

# from helpers import

# Configure application
app = Flask(__name__)

# Configure session to use filesystem instead of signed cookies
app.config["SESSION_PERMARNENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to apply SQLite database
db = SQL("sqlite:///bio-genre.db")

# admin log in key
security_key = "123456"

@app.route("/")
def homepage():
    return render_template("homepage.html")


@app.route("/sequence", methods = ['GET', 'POST'])
def sequence():
    if request.method == 'POST':
        options = request.form.getlist("option")
        sequence = request.form.get("sequence").strip().upper()
        motif = request.form.get("motif").strip().upper()
        # handle blank input
        if not sequence or not options:
            return redirect("/")

        result = {}
        result["input_sequence"] = sequence
        # process valid input:
        # handle selected option
        if 'length' in options:
            # calculate sequence length
            result["length"] = f"{len(sequence):,} bp"

        if 'gc_content' in options:
            result["gc"] = str(gc_content(sequence)) + " %"

        if 'transcript' in options:
            if isRNA(sequence):
                result["transcript"] = "Your sequence is RNA"
            else:
                result["transcript"] =transcript(sequence)

        if 'translate' in options: # just read frame 1
            result["translate"] = translate(sequence)


        if 'orf' in options: # read all 3 frames
            output = orf_search(sequence) # return a list of orf, dict frame [5'3', 3'5']
            result["orf"] = f"5'-3' Frame 1: {', '.join(output[1][0]["Frame 1"])}\n5'-3' Frame 2: {', '.join(output[1][0]["Frame 2"])}\n5'-3' Frame 3: {', '.join(output[1][0]["Frame 3"])}\n\n3'-5' Frame 1: {', '.join(output[1][1]["Frame 1"])}\n3'-5' Frame 2: {', '.join(output[1][1]["Frame 2"])}\n3'-5' Frame 3: {', '.join(output[1][1]["Frame 3"])}"
            print(output)
        if motif:
            output = find_motif(sequence, motif)
            result["motif"] = f"Motif: {output[2]}\nFrequency: {output[1]}\nPosition (1-based index): {output[0]}"

        return render_template("sequence.html", display_result=True, result=result)
    else:
        return render_template("sequence.html", display_result=False)


@app.route("/blast", methods = ['GET', 'POST'])
def blast():
    if request.method == 'GET':
        return render_template("blast.html")


@app.route("/login", methods = ['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        find_user = db.execute("SELECT * FROM users WHERE username = ?", username)

        if find_user and check_password_hash(find_user[0]["password_hash"], password):
            flash("Logged in!")
            # store user's id in cookies
            session["user_id"] = find_user[0]["id"]
            #db.execute("SELECT id FROM users WHERE username = ?", username)[0]["id"]
            session["role"] = find_user[0]["role"]
            return redirect("/")

        else:
            flash("Username or password incorrect!")
            return render_template("login.html")
    else:
        return render_template("login.html")


@app.route("/species-manage", methods = ['GET', 'POST'])
@login_required
def admin_login():
    if session["role"] == 'admin' and request.method == 'GET':
        if not session.get("access_granted",""):
            return redirect("/admin-access")
        if session["access_granted"] == True:
            return render_template("species-manage.html")
    elif session["role"] == 'admin' and request.method == 'POST' and session["access_granted"] == True:
        # UPDATE DATA to DATABASE

        sci_name =  request.form.get("sci_name")
        common_name = request.form.get("common_name")
        habitat = request.form.get("habitat")
        life_span = request.form.get("life_span")
        location_value = request.form.get("location_value")
        description = request.form.get("description")

        if not valid_str_parameter(sci_name) or not valid_str_parameter(common_name):
            flash("Scientific name, common name, and geographic distribution must contain only alphabet and space!")
            print(sci_name, common_name, location_value)
            return redirect("/species-manage")

        db.execute('''INSERT INTO species (sci_name, common_name, habitat, life_span, location, description)
                    VALUES(?,?,?,?,?,?)''', sci_name,common_name,habitat,life_span,location_value,description)
        flash("Species inserting success!")
        return redirect("/species-manage")

    else:
        flash("Only admin can use this feature!")
        return redirect("/")



@app.route("/admin-access", methods = ['GET', 'POST'])
@login_required
def admin_access():
    if session["role"] == 'admin' and request.method == 'GET':
        return render_template("admin-access.html")
    elif session["role"] == 'admin' and request.method == 'POST':
        if request.form.get("security_key") == security_key:
            session["access_granted"] = True
            flash("Access granted!")
            return redirect("/species-manage")
        else:
            flash("Incorrect security key!")
            return redirect("/admin-access")
    else:
        flash("Only admin can use this feature!")
        return redirect("/")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash("Logged out")
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()
    if request.method == 'GET':
        return render_template("register.html")
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')

        # validate empty username or password:
        if not username or not password or not confirmation:
            flash("Please fullfill the register fields!")
            return None

        # check password and confirmation are the same:
        if password != confirmation:
            flash("Password and confirmation are not match!")
            return None


        hash_password = generate_password_hash(password)
        users = db.execute("SELECT * FROM users")

        # check whether the user's register infors are alredy exist
        for user in users:
            if user["username"] == username:
                flash("Username already exist!")
                return render_template("register.html")
            if check_password_hash(user["password_hash"], password):
                flash("Password already used!")
                return render_template("register.html")

        # if user's register infors are unique, add infors into users database, then log them into server
        db.execute("INSERT INTO users (username, password_hash) VALUES (?,?)", username, hash_password)

        # save user's id into cookies and keep them logging-in
        session["user_id"] = db.execute(
            "SELECT id FROM users WHERE username = ?", username)[0]["id"]
        session["role"] = "user"
        flash("Registered!")
        return render_template("homepage.html")

@app.route("/species-query")
@login_required
def species():
    return render_template("species-query.html")


@app.route("/api/species")
def api_species():
    sci_name = request.args.get("sci_name")
    common_name = request.args.get("common_name")
    id = request.args.get("id")
    location = request.args.get("location")
    year = request.args.get("year")

    # Year parameter must be included
    if not year:
        return {"Error": "year parameter is required"}
    if year:
        if not year.isdigit():
            return jsonify({"Error": "Invalid year parameter"})
        if int(year) < 2025:
            return jsonify({"Error": "Years before 2025 is not accepted"})

    query_string = f"SELECT * FROM species WHERE updated_time LIKE '%{year}%' "

    # Validate other parameter
    # allow 1 space between word, case insensitive: sci_name, common_name, location
    # allow digit only: id
    respond = {}

    if sci_name:
        if not valid_str_parameter(sci_name):
            respond["respond status"] = 400
            respond["error"] = "sci_name (scientific name) parameter must contain alphabet and space only; and words are separeated by only one space"
            return jsonify(respond)
        query_string += f"AND sci_name LIKE '%{sci_name}%' "

    if common_name:
        if not valid_str_parameter(common_name):
            respond["respond status"] = 400
            respond["error"] = "common_name parameter must contain alphabet and space only; and words are separeated by only one space"
            return jsonify(respond)
        query_string += f"AND common_name LIKE '%{common_name}%' "

    if id:
        if not id.isdigit():
            respond["respond status"] = 400
            respond["error"] = "id parameter must contain digit only"
            return jsonify(respond)
        query_string += f"AND id = {id} "

    if location: # not allow space
        if not valid_str_parameter(location):
            respond["respond status"] = 400
            respond["error"] = "location (geographic distribution) parameter must contain alphabet and space only; and words are separeated by only one space"
            return jsonify(respond)
        query_string += f"AND location LIKE '%{location}%' "

    # Query data from species database
    species = db.execute(query_string)
    if not species:
        respond["respond status"] = 404
        respond["error"] = "No matching results found"
        return jsonify(respond)

    respond["respond status"] = 200
    respond["result"] = species
    return jsonify(respond)
