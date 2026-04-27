import os,sys
import logging
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import mysql.connector
from werkzeug.security import generate_password_hash



def load_config(secret, default =None):
    
    secret_path = f'/run/secrets/{secret}'
    if os.path.exists(secret_path):
        with open(secret_path, 'r') as f:
            return f.read().strip()
        
    return os.getenv(secret, default)
        


db_password = load_config("MYSQL_PASSWORD")


#create connection to db on docker container
def get_db_connection():
    return mysql.connector.connect(    
        host = os.getenv("MYSQL_HOST"),
        user = os.getenv("MYSQL_USER"),
        password = db_password,
        database = os.getenv("MYSQL_DATABASE"))



#intialize login_manager and flask app
app = Flask(__name__)
app.secret_key = load_config('FLASK_SECRET_KEY', 'dev-key-only')
app.logger.setLevel(logging.DEBUG)





@app.route('/', methods=['GET'])
def home():
    return redirect(url_for("login"))




@app.route('/register', methods = ['GET','POST'])
def register():
    if session.get("logged_in"):
        return redirect(url_for('dashboard'))
    
    if request.method == "GET":
        return render_template("register.html")
    
    #get values submited with form
    username = request.form["username"]
    password = request.form["password"]
    first_name = request.form["firstName"]
    last_name = request.form["lastName"]
    address = request.form["address"]
    phoneNum = request.form["phoneNumber"]
    licenseNum = request.form["licenseNumber"]

    #establish connection to db
    cnx = get_db_connection()
    cursor = cnx.cursor()

    #attempt user registration  
    try: 
        #adding user to users table of db
        add_user = ("INSERT INTO USERS "
                    "(username, password, address, phoneNumber, licenseNumber, firstName, lastName) "
                    "VALUES (%s, %s,%s, %s,%s, %s, %s)")
        
        new_user = (username, password, 
                    None if address=="" else address, 
                    None if phoneNum=="" else phoneNum, 
                    None if licenseNum=="" else licenseNum,
                    None if first_name=="" else first_name, 
                    None if last_name=="" else last_name,
                )
        cursor.execute(add_user, new_user)

        cnx.commit()

        #check insertion was successful
        if cursor.rowcount ==1:
            '''return jsonify({"status":"success",
                    "message":"User successfully registered",
                    "userId":cursor.lastrowid
                    }),201'''
            return redirect(url_for("login"))
        return jsonify({
            "status":"fail",
            "message": "user registration failed",
        }),500
    
    #return exepction message
    except Exception as e:
        return jsonify({ "status":"error",
                "message": str(e)
        }),500

    finally:
        cursor.close()
        cnx.close()






@app.route('/login', methods=['GET','POST'])
def login():

    app.logger.debug("login route hit")

    #redirect user to dahsboard if theyre logged in
    if session.get("logged_in"):
        return redirect(url_for('dashboard'))
    

    if request.method == 'GET':
        return render_template("login.html")

    username_ = request.form["username"]
    password_ = request.form["password"]

    #establish connection to db
    cnx = get_db_connection()
    cursor = cnx.cursor()

    try:                                                               #='admin' OR '1'='1'
        query = f"SELECT username, password FROM USERS WHERE username = '{username_}' AND password = '{password_}'"
        #print("YOOOOOOOOOOOOO", flush=True)
        print(query, flush=True)
        cursor.execute(query)
        row = cursor.fetchall()


        if row:
            #if (username_ == row[0] and check_password_hash(str(row[1]),password_)):
            session["logged_in"] = True
            session["username"] = username_
            return redirect(url_for('dashboard'))
        else:
            return jsonify({"status": "Login Failed",
                            "message": "Username or password is incorrect. Please try again."}),401
    
    except Exception as e:
        return jsonify({
            "status":"Data Base Error",
            "Error": str(e)
        }),500
    
    finally:
        cursor.close()
        cnx.close()
        
        



@app.route('/dashboard', methods=['GET'])
def dashboard():
    if (not session.get("logged_in")):
        return redirect(url_for("login"))

    
    cnx = get_db_connection()
    cursor = cnx.cursor()

    if (session.get("username")):
        try:
            query = f"SELECT firstName, lastName FROM USERS WHERE username = '{session.get('username')}'"
            
            cursor.execute(query)
            row = cursor.fetchone()

            if row: #if query resulted in retireved data return it to user

            #return html page dispplaying user data  in DB
                return render_template(
                    "dashboard.html",
                    username= session.get("username"),
                    first_name=row[0],
                    last_name=row[1]
                )
                            

            else: 
                #user not found in db
                return jsonify({
                    "status":"Failed to find user",
                    "message":"User does not exist"
                }),404

        except Exception as e:
            return jsonify({
                "status":"User retrieval failed",
                "Error": str(e)
            }),500
        
        finally:
            cursor.close()
            cnx.close()

    else:
        return jsonify({"status":"Error","message":"Missing session username"}),400



#endpoint for looking for users: is vulnerable to SQL injection
@app.route('/search', methods=['GET','POST'])
def search():
    if (not session.get("logged_in")):
        return redirect(url_for("login"))

    if request.method == 'GET':
        return render_template("search.html")
    


    firstName = request.form["firstName"]
    lastName = request.form["lastName"]


    #establish db connection
    cnx = get_db_connection()
    cursor = cnx.cursor()

   
    #sql injection vulnerable string
    query = f"SELECT firstName, lastName, address, phoneNumber, licenseNumber FROM USERS WHERE firstName = '{firstName}' AND lastName = '{lastName}'"
    print(query, flush=True)

    try:

        cursor.execute(query)
        rows = cursor.fetchall()

        if len(rows)>0:
            persons = []

            for (first_, last_, address, phoneNum, licenseNum) in rows: #if query resulted in retireved data return it to user
                persons.append({
                        "status": "User found",
                        "Name": first_ + " " + last_,
                        "Address": address,
                        "Phone Number": phoneNum,
                        "License Number": licenseNum
                    })
            
            return jsonify(persons),200  #return json object of user data  in DB
        

        else: 
            #user not found in db
            return jsonify({
                "status":"Failed to find user",
                "message":"User does not exist"
            }),404
        

    except Exception as e:
        return jsonify({
            "status":"User retrieval failed",
            "Error": str(e)
        }),500
    
    finally:
        cursor.close()
        cnx.close()







#parameterized end to show a solution to prevent sql injection
@app.route('/update_phone_number', methods=['GET', 'POST'])
def update_phoneNum():
    if (not session.get("logged_in")):
        return redirect(url_for("login"))
    
    if (request.method == 'GET'):
        return render_template("updatePhone.html")
    
    


    new_number = request.form["new_number"]

    #establish db connection
    cnx = get_db_connection()
    cursor = cnx.cursor()


    if(session.get("username")):


        #attempt to update user phonenumber  
        try: 
            #updating user to phone num in users table of db
            query = "UPDATE USERS set phoneNumber = %s WHERE username = %s"
            values = (new_number, session.get("username"))
            cursor.execute(query, values)
            cnx.commit()


            #check update was successful
            if cursor.rowcount ==1:
                return jsonify({"status":"success",
                        "message":"Update successfull",
                        "userId":cursor.lastrowid
                        }),201
            else:
                return jsonify({
                    "status":"fail",
                    "message": "Update registration failed",
                }),500
        
        #return exepction message
        except Exception as e:
            return jsonify({ "status":"error",
                    "message": str(e)
            }),500

        finally:
            cursor.close()
            cnx.close()
    else:
        return jsonify({"status":"Error",
                        "message": "Missing session username"})

    



#GET end point for retreiving a user
@app.route('/lookup/<username>', methods=['GET'])
def lookup(username):
    if (not session.get("logged_in")):
        return redirect(url_for("login"))
    
    #establish db connection
    cnx = get_db_connection()
    cursor = cnx.cursor()

    #sql injection vulnerable string
    query = f"SELECT firstName, lastName, address, phoneNumber, licenseNumber FROM USERS WHERE username = '{username}'"
    print(query, flush=True)

    try:

        cursor.execute(query)
        row = cursor.fetchone()

        if row: #if query resulted in retireved data return it to user
                first_name, last_name, address, phone_num, license_num = row
                return jsonify({
                    "status": "User found",
                    "Name": f"{first_name} {last_name}",
                    "Address": address,
                    "Phone Number": phone_num,
                    "License Number": license_num
                }), 200
        

        else: 
            #user not found in db
            return jsonify({
                "status":"Failed to find user",
                "message":"User does not exist"
            }),404

    except Exception as e:
        return jsonify({
            "status":"User retrieval failed",
            "Error": str(e)
        }),500
    
    finally:
        cursor.close()
        cnx.close()



@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)