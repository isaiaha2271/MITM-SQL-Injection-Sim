from flask import Flask, render_template, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash


host = "db"
user = "user"
password = "password_1"
database = "labDB"

app = Flask(__name__)


@app.route('/')
def home():
    return jsonify({"hello":"This is main page"})


@app.route('/register', methods = ['GET','POST'])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    username = request.form["username"]
    passowrd = request.form["password"]



    #MAKE CALL TO DOCKER CONTAIN DB HERE TO ADD USER TO DB

    return ""

@app.route('/login', methods=['GET, POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]




    #****make a call to docker container storing db to verify/authetnicate user
    
    
    
    
    
    
    
    return ""




#get endpoint for looking for users
@app.route('/search', methods=['GET'])
def search():
    pass



#post end point for searching for users
@app.route('/lookup/<username>', methods=['POST'])
def lookup(username):
    pass






