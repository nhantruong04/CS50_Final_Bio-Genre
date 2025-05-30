
from cs50 import SQL
from flask import Flask, redirect, render_template, flash, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, gc_content, transcript, translate, find_motif, orf_search, isRNA

# from helpers import

# Configure application
app = Flask(__name__)

# Configure session to use filesystem instead of signed cookies
app.config["SESSION_PERMARNENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to apply SQLite database
db = SQL("sqlite:///bio-genre.db")



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

@app.route("/genes")
@login_required
def genes():
    return

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        find_user = db.execute("SELECT * FROM users WHERE username = ?", username)

        if find_user and check_password_hash(find_user[0]["password_hash"], password):
            flash("Logged in!")
            # store user's id in cookies
            session["user_id"] = db.execute(
            "SELECT id FROM users WHERE username = ?", username)[0]["id"]
            return redirect("/")

        else:
            flash("Username or password incorrect!")
            return render_template("login.html")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
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
        flash("Registered!")
        return render_template("homepage.html")


