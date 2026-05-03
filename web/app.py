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
app.config['JSON_SORT_KEYS'] = False
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
    company = request.form["company"]

    if not first_name or not last_name or not company or not phoneNum or not licenseNum or not company:
        return "Missing required fields", 400
    #establish connection to db
    cnx = get_db_connection()
    cursor = cnx.cursor()
    rowCount = None

    #attempt user registration  
    try: 
        #adding user to users table of db
        add_user = ("INSERT INTO USERS "
                    "(username, password, address, phoneNumber, licenseNumber, firstname, lastname, company) "
                    "VALUES (%s, %s,%s, %s,%s, %s, %s, %s)")
        
        new_user = (username, password, 
                    None if address=="" else address, 
                    phoneNum, 
                    licenseNum,
                    first_name, 
                    last_name,
                    company
                )
        cursor.execute(add_user, new_user)

        cnx.commit()
        print(cursor)
        rowCount = cursor.rowcount
        
    
    #return exepction message
    except Exception as e:
        return jsonify({ "status":"error",
                "message": str(e)
        }),500

    finally:
        cursor.close()
        cnx.close()

        #check insertion was successful
        if rowCount ==1:
            '''return jsonify({"status":"success",
                    "message":"User successfully registered",
                    "userId":cursor.lastrowid
                    }),201'''
            return redirect(url_for("login"))
        
        return jsonify({
            "status":"fail",
            "message": "user registration failed",
        }),500
    
        






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
    cursor = cnx.cursor(buffered=True)

    try:                                                               #=admin' OR '1'='1
        query = "SELECT username, password FROM USERS WHERE username = '" + str(username_) + "' AND password = '" + str(password_) + "'"
        #print("YOOOOOOOOOOOOO", flush=True)
        print(query, flush=True)
        cursor.execute(query)
        rows = cursor.fetchall()


        if len(rows)>0:

            #create a cookie flag  for user lgoin status
            session["logged_in"] = True
            session["username"] = username_
            
    except Exception as e:
        return jsonify({
            "status":"Data Base Error",
            "Error": str(e)
        }),500
    
    finally:
        print(f"rows fetched: {len(rows)}", flush = True)
        for row in rows:
            print(str(row))   
        cursor.close()
        cnx.close()

        if session.get("logged_in"):
            return redirect(url_for('dashboard'))
        else:
            return jsonify({"status": "Login Failed",
                            "message": "Username or password is incorrect. Please try again."}),401
    
        
        
        



@app.route('/dashboard', methods=['GET'])
def dashboard():
    if (not session.get("logged_in")):
        return redirect(url_for("login"))

    
    cnx = get_db_connection()
    cursor = cnx.cursor(buffered=True)
    result = None
    if (session.get("username")):
        try:
            query = "SELECT firstname, lastname FROM USERS WHERE username = '" + str(session.get('username')) + "'"
            
            cursor.execute(query)
            rows = cursor.fetchall()

            if len(rows)>0: #if query resulted in retireved data return it to user
                result = rows[0]
            #return html page dispplaying user data  in DB

                

        except Exception as e:
            return jsonify({
                "status":"User retrieval failed",
                "Error": str(e)
            }),500
        
        finally:

            cursor.close()
            cnx.close()

            if result:
                return render_template(
                        "dashboard.html",
                        username= session.get("username"),
                        first_name=result[0],
                        last_name=result[1]
                    )
                            
            else: 
                #user not found in db
                return jsonify({
                    "status":"Failed to find user",
                    "message":"User does not exist"
                }),404

            

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
    cursor = cnx.cursor(buffered=True)
    rows = None
   
    #sql injection vulnerable string

    query = "SELECT firstname, lastname, address, phoneNumber, licenseNumber FROM USERS WHERE firstname = '" + str(firstName)  + "' AND lastname = '" + str(lastName) + "'"
    print(query, flush=True)

    try:

        cursor.execute(query)
        rows = cursor.fetchall()

       
        

    except Exception as e:
        cursor.close()
        cnx.close()

        return jsonify({
            "status":"User retrieval failed",
            "Error": str(e)
        }),500
    
    finally:
        cursor.close()
        cnx.close()

        if len(rows)>0:
            persons = []

            for (first_, last_, address, phoneNum, licenseNum) in rows: #if query resulted in retireved data return it to user
                persons.append({
                        "status": "User found",
                        "Name": "" if not first_ or not last_ else first_ + " " + last_,
                        "Address": "" if not address else address ,
                        "Phone Number": "" if not phoneNum else phoneNum,
                        "License Number": "" if not licenseNum else licenseNum
                    })
                
            
            
            return jsonify(persons),200  #return json object of user data  in DB
        

        else: 
            #user not found in db
            return jsonify({
                "status":"Fail",
                "message":"Person not Found"
            }),404

    
        







#parameterized end to show a solution to prevent sql injection
@app.route('/update_contact_info', methods=['GET', 'POST'])
def update_contact_info():
    if (not session.get("logged_in")):
        return redirect(url_for("login"))
    
    if (request.method == 'GET'):
        return render_template("updateContact.html")
    
    


    new_number = request.form["phoneNumber"]
    new_address = request.form["address"]

    #establish db connection
    cnx = get_db_connection()
    cursor = cnx.cursor()


    if(session.get("username")):


        #attempt to update user phonenumber  
        try: 
            #updating user to phone num in users table of db
            query = "UPDATE USERS set phoneNumber = %s, address = %s WHERE username = %s"
            values = (new_number,new_address, session.get("username"))
            
            cursor.execute(query, values)
            cnx.commit()

            
            
           
                
        
        #return exepction message
        except Exception as e:

            cursor.close()
            cnx.close()

            return jsonify({ "status":"error",
                    "message": str(e)
            }),500
    
        finally:
            numAffectedRows = cursor.rowcount
            cursor.close()
            cnx.close()

            if numAffectedRows > 0:
                return jsonify({"status":"success",
                        "message":"Update successfull"
                        }),201
            else:
                

                return jsonify({
                    "status":"fail",
                    "message": "Update registration failed",
                }),500

    
    else:
        return jsonify({"status":"Error",
                        "message": "Missing session username"})

    
#parameterized end to show a solution to prevent sql injection
@app.route('/update_company', methods=['GET', 'POST'])
def update_company():
    if (not session.get("logged_in")):
        return redirect(url_for("login"))
    
    if (request.method == 'GET'):
        return render_template("updateCompany.html")
    
    


    new_company = request.form["new_company"]

    #establish db connection
    cnx = get_db_connection()
    cursor = cnx.cursor()


    if(session.get("username")):


        #attempt to update user phonenumber  
        try: 
            #updating user to phone num in users table of db
            query = "UPDATE USERS set company = '" + str(new_company) + "' WHERE username = '" + str(session["username"]) + "'"   
            print(query, flush=True)
            cursor.execute(query)
            cnx.commit()

        
                
        
        #return exepction message
        except Exception as e:

            cursor.close()
            cnx.close()

            return jsonify({ "status":"error",
                    "message": str(e)
            }),500
    
        finally:
            numAffectedRows = cursor.rowcount
            cursor.close()
            cnx.close()

            if numAffectedRows> 0:
                print(f"numAffectedRows: {numAffectedRows}")
                return jsonify({"status":"success",
                        "message":"Update successful",
                        }),201
            else:
                

                return jsonify({
                    "status":"fail",
                    "message": "Update  failed",
                }),500

    
    else:
        return jsonify({"status":"Error",
                        "message": "Missing session username"})


#GET end point for retreiving a user
@app.route('/find_company_drivers/<company>', methods=['GET'])
def find_company_drivers(company):
    if (not session.get("logged_in")):
        return redirect(url_for("login"))
    
    #establish db connection
    cnx = get_db_connection()
    cursor = cnx.cursor()

    company_ = str(company.strip())
    #sql injection vulnerable string
    query = "SELECT firstname, lastname, address, phoneNumber, licenseNumber FROM USERS WHERE company = '" + str(company_).strip() + "'"
    print(query, flush=True)

    rows = None
    try:

        cursor.execute(query)
        print("INBETWEEN", flush =True)
        rows = cursor.fetchall()
        
        print(f"cursor result {rows}", flush=True)


        

    except Exception as e:
        return jsonify({
            "status":"Driver retrieval failed",
            "Error": str(e)
        }),500
    
    finally:
    
        cursor.close()
        cnx.close()

        drivers = []

        if rows: #if query resulted in retireved data return it to user
                for (first_name, last_name, address, phone_num, license_num) in  rows:
                    drivers.append({
                                "status": "User found",
                                "Name": "" if not first_name or not last_name else first_name + " " + last_name,
                                "Address": "" if not address else address ,
                                "Phone Number": "" if not phone_num else phone_num,
                                "License Number": "" if not license_num else license_num
                            })
                return jsonify({"Drivers":drivers}),200
                
               
        

        else: 
            #company not found in db
            return jsonify({
                "status":"Fail",
                "message":"Failed to find drivers"
            }),404
        
'''for  first_name, last_name, address, phone_num, license_num in rows:
            persons.append({
                "status": "User found",
                "Name": "" if not first_name or not last_name else first_name + " " + last_name,
                "Address": "" if not address else address ,
                "Phone Number": "" if not phone_num else phone_num,
                "License Number": "" if not license_num else license_num
            })
    return jsonify(persons), 200'''



@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)