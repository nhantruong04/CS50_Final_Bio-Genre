
import os
import uuid
from cs50 import SQL
from flask import Flask, redirect, render_template, flash, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, gc_content, transcript, translate, find_motif, orf_search, isRNA, valid_sci_name, valid_common_name, valid_location
from alignment import blastn

# Configure application
app = Flask(__name__)

# allow upload image to folder
UPLOAD_FOLDER = 'static/images/species'
ALLOWED_EXTENSIONS = { 'png'}

# Configure session to use filesystem instead of signed cookies
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["SESSION_PERMARNENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to apply SQLite database
db = SQL("sqlite:///bio-genre.db")

# admin key to access species-data/add species
security_key = "123456"
# Generate a random UUID (UUID4); using for asscess granted key after admin has enter correct security key
random_uuid = uuid.uuid4() # session["access_granted"] = random_uuid


print("Random UUID:", random_uuid)
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
    else:
        score = request.form.get("match-mismatch").split(',')
        query = request.form.get("query").upper().strip()
        gap = request.form.get("gap")

        if not query or not score or not gap:
            flash("Please fill all parameters")
            return render_template("blast.html")
        if len(query) > 200:
            flash("Not support query sequence larger than 200 bp")
            return render_template("blast.html")
        match = int(score[0])
        mismatch = int(score[1])
        gap = int(gap)

        # collect sequence database:
        sequences = db.execute("SELECT * FROM db_sequence")

        # blast the query sequence to each seq in database
        all_result = []
        for seq in sequences:
            result_of_each_chromosome = blastn(query,seq["seq_nu"], match, mismatch, gap) # -> [{'align': {..}}]
            if result_of_each_chromosome == ["No significant similarity found!"]:
                continue
            else:
                sci_name = db.execute("SELECT sci_name FROM species WHERE id = ?", seq["species_id"])[0]['sci_name']
                description = f'{sci_name}, {seq["name"]}'
                all_result.append({
                    'description': description,
                    'sci_name':sci_name,
                    'max_score': result_of_each_chromosome['max_score'],
                    'species_id': seq["species_id"],
                    'total_score': result_of_each_chromosome['total_score'],
                    'alignment_result': result_of_each_chromosome['result'],
                    'number_of_matches': len(result_of_each_chromosome['result']),
                    'sequence_id': seq['seq_id'],
                    'sequence_length': seq['seq_length']
                    })
        all_result = sorted(all_result, key=lambda x:x["max_score"],reverse=True)
        return render_template("blast-result.html", all_result = all_result, query=query, score=request.form.get("match-mismatch"), gap=gap)


@app.route("/login", methods = ['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form.get('username').strip()
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

# function to valid file name and allowed extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/species-manage", methods = ['GET', 'POST'])
@login_required
def admin_login():
    if session["role"] == 'admin':
        if request.method == 'GET':
            if session.get("access_granted", "") == random_uuid:
                return render_template("species-manage.html")
            else:
                return redirect("/admin-access")
        elif request.method == 'POST':
            if session.get("access_granted", "") == random_uuid:
                # UPDATE DATA to DATABASE
                sci_name =  request.form.get("sci_name")
                common_name = request.form.get("common_name")
                habitat = request.form.get("habitat")
                life_span = request.form.get("life_span")
                location_value = request.form.get("location_value")
                description = request.form.get("description")

                if not valid_sci_name(sci_name):
                    flash("Scientific name can contain only alphabet, hyphen and space!")
                    return redirect("/species-manage")

                if not valid_common_name(common_name):
                    flash("Common name can contain only alphabet, hyphen, single quote and space!")
                    return redirect("/species-manage")

                # check if the post request has the file
                if 'image' not in request.files:
                    flash('No image file part')
                    return redirect("/species-manage")

                file = request.files.get("image")

                # If the user does not select a file, the browser submits an empty file without a filename.
                if not file or file.filename == '':
                    flash('No image selected. Species image is required')
                    return redirect("/species-manage")

                if file and allowed_file(file.filename):
                    db.execute('''INSERT INTO species (sci_name, common_name, habitat, life_span, location, description)
                            VALUES(?,?,?,?,?,?)''', sci_name,common_name,habitat,life_span,location_value,description)

                    new_species_id = db.execute("SELECT id FROM species WHERE sci_name = ? AND common_name = ?", sci_name, common_name)[0]["id"]
                    filename = f'{new_species_id}.png'
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                flash("Species adding success!")
                return redirect("/species-manage")
            else:
                flash("Incorrect security key")
                return redirect("/admin-access")

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
            session["access_granted"] = random_uuid
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
        username = request.form.get('username').strip()
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

    respond = {}
    # Year parameter must be included. Contain digit only and >= 2025
    if not year:
        respond["respond status"] = 400
        respond["error"] = "year parameter is required"
        return jsonify(respond)

    if year:
        if not year.isdigit() or len(str(year)) != 4: # reject negative string number or invalid number
            respond["respond status"] = 400
            respond["error"] = "Year parameter must be four digit positive integer"
            return jsonify(respond)

        if int(year) < 2025:
            respond["respond status"] = 400
            respond["error"] = "Years before 2025 is not accepted"
            return jsonify(respond)

    query_string = f"SELECT * FROM species WHERE updated_time LIKE '%{year}%' "

    # Validate other parameter:
    # Scientific name allow alphabet, hyphen and space. Each word is seperated by spaces
    if sci_name:
        sci_name = " ".join(sci_name.split()) # escape multiple spaces between words to query data
        if not valid_sci_name(sci_name) or len(sci_name) < 4:
            respond["respond status"] = 400
            respond["error"] = "sci_name (scientific name) parameter has at least 4 characters and just contain alphabet, hyphen and space only"
            return jsonify(respond)
        query_string += f"AND sci_name LIKE '%{sci_name}%' "

    # Common name allow alphabet, hyphen, single quote and space. Each word is seperated by spaces
    if common_name:
        common_name = " ".join(common_name.split()) #escape multiple spaces
        if not valid_common_name(common_name) or len(common_name) < 4:
            respond["respond status"] = 400
            respond["error"] = "common_name parameter has at least 4 characters and just contain alphabet, hyphen, single quote and space only"
            return jsonify(respond)
        query_string += f"AND common_name LIKE '%{common_name}%' "

    # id must contain digit only
    if id:
        if not id.isdigit():
            respond["respond status"] = 400
            respond["error"] = "id parameter must contain digit only"
            return jsonify(respond)
        query_string += f"AND id = {id} "

    # Locaion allow alphabet, hyphen, single quote, dot, semicolon, open/close parentheses, comma and space.
    if location: # not allow space
        location = " ".join(location.split())
        if not valid_location(location) or len(location) < 4:
            respond["respond status"] = 400
            respond["error"] = "location parameter has at least 4 characters and just contain alphabet, hyphen, single quote and space only"
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


@app.route("/api-docs")
def api_docs():
    return render_template("api-docs.html")


@app.route("/species-details")
def species_details():
    species_id = request.args.get("species_id")
    if species_id:
        species = db.execute("SELECT * FROM species WHERE id = ?", int(species_id))
        if species:
            return render_template("species-details.html", species=species[0], species_id=species[0]["id"])
        elif not species:
            flash("Error 404 specie id not found!")
            return render_template("species-details.html")

    flash("Error 400: id parameter is required!")
    return render_template("species-details.html")
