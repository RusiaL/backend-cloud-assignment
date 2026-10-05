from flask import Flask, request
import os
import psycopg2
import requests
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
load_dotenv()

database_url = os.getenv("DATABASE_URL")
server_y_url = os.getenv("SERVER_Y_URL")
server_y_api_key = os.getenv("SERVER_Y_API_KEY")
server_x_api_key = os.getenv("SERVER_X_API_KEY")
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

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, username, email
        FROM users
        WHERE id = %s;
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user is None:
        return {
            "error": "User not found"
        }, 404

    return {
        "id": user[0],
        "username": user[1],
        "email": user[2]
    }, 200

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data["username"]
    password = data["password"]

    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, username, email, password_hash
        FROM users
        WHERE username = %s;
        """,
        (username,)
    )

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user is None:
        return {
            "error": "Invalid username or password"
        }, 401

    password_is_correct = check_password_hash(
        user[3],
        password
    )

    if not password_is_correct:
        return {
            "error": "Invalid username or password"
        }, 401

    return {
        "message": "Login successful",
        "id": user[0],
        "username": user[1],
        "email": user[2]
    }, 200

@app.route("/sync/likes", methods=["POST"])
def sync_like():
    api_key = request.headers.get("X-API-Key")

    if api_key != server_x_api_key:
        return {
            "error": "Unauthorized"
        }, 401

    data = request.get_json()

    response = requests.post(
        f"{server_y_url}/internal/likes",
        headers={
            "X-API-Key": server_y_api_key
        },
        json=data,
        timeout=5
    )

    return response.json(), response.status_code

if __name__ == "__main__":
    app.run(debug=True)