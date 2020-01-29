from src.db.UserTable import UserTable
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import sys

# Sign in/up functions
def signin(db, data):
    if data["email"] or data["password"]:       # Server side check for user email and password entry
        try:
            query = UserTable.query.filter_by(email=data['email']).filter_by(password=data['password']).first()
            # Query the database with the entered email and password combination

            if not query:                   # If no results are returned, the email/password are incorrect, return forbidden code
                return {
                    "result": 400
                }

            query.lastlogin = datetime.now()        # If it is found, update the lastlogin field
            db.session.commit()

            return {
                "result": 200,
                "userid": str(query.userid)
            }
        except Exception as e:
            print(e)
            sys.stdout.flush()
            return {
                "result": 500
            }


def signup(db, data):
    userdata = UserTable({  # Define an instance of the UserTable class with the entered data
        "username": data["username"],
        "email": data["email"],
        "password": data["password"],  # Replace with hashed password eventually
        "lastlogin": datetime.now()
    })

    try:
        db.session.add(userdata)  # Add the newly instantiated object to the DB
        db.session.commit()  # Ensure the database transaction properly completes
    except IntegrityError as e:  # Thrown if the user attempts to use an email that already exists in the table
        return {
            "result": 400,
        }
    except Exception as e:
        print("Failed Signup for user... " + data["email"])
        print(e)
        sys.stdout.flush()  # Output to Heroku log if an error occurs

        return {
            "result": 500
        }  # Return a 500 error code

    return {
        "result": 200
    }  # If successful, return a 200 code

