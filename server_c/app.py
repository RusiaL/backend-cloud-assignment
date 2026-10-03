from flask import Flask, request
import os
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

app = Flask(__name__)
load_dotenv()

database_url = os.getenv("DATABASE_URL")
connection = psycopg2.connect(database_url)
print("Successfully connected to PostgreSQL!")
connection.close()

@app.route("/")
def home():
    return {
        "server": "C",
        "status": "running"
    }

@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()

    username = data["username"]
    email = data["email"]
    password = data["password"]

    password_hash = generate_password_hash(password)

    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO users (username, email, password_hash)
        VALUES (%s, %s, %s)
        RETURNING id;
        """,
        (username, email, password_hash)
    )

    user_id = cursor.fetchone()[0]

    connection.commit()
    cursor.close()
    connection.close()

    return {
        "id": user_id,
        "username": username,
        "email": email
    }, 201


if __name__ == "__main__":
    app.run(debug=True)