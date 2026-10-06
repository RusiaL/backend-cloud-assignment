from flask import Flask, request
import os
import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)

database_url = os.getenv("DATABASE_URL")
server_c_url = os.getenv("SERVER_C_URL")
server_c_api_key = os.getenv("SERVER_C_API_KEY")

connection = psycopg2.connect(database_url)
print("Server X successfully connected to PostgreSQL!")
connection.close()

@app.route("/")
def home():
    return {
        "server": "X",
        "status": "running"
    }

@app.route("/likes", methods=["POST"])
def create_like():
    data = request.get_json()

    user_id = data["user_id"]
    post_id = data["post_id"]

    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO likes (user_id, post_id)
        VALUES (%s, %s)
        RETURNING id;
        """,
        (user_id, post_id)
    )

    like_id = cursor.fetchone()[0]

    connection.commit()
    cursor.close()
    connection.close()

    return {
        "id": like_id,
        "user_id": user_id,
        "post_id": post_id
    }, 201

@app.route("/likes/<int:user_id>", methods=["GET"])
def get_likes(user_id):
    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, user_id, post_id, created_at
        FROM likes
        WHERE user_id = %s
        ORDER BY created_at;
        """,
        (user_id,)
    )

    likes = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        "user_id": user_id,
        "likes": [
            {
                "id": like[0],
                "user_id": like[1],
                "post_id": like[2],
                "created_at": like[3].isoformat()
            }
            for like in likes
        ]
    }, 200

@app.route("/comments", methods=["POST"])
def create_comment():
    data = request.get_json()

    user_id = data["user_id"]
    post_id = data["post_id"]
    comment_text = data["comment_text"]

    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO comments (user_id, post_id, comment_text)
        VALUES (%s, %s, %s)
        RETURNING id;
        """,
        (user_id, post_id, comment_text)
    )

    comment_id = cursor.fetchone()[0]

    connection.commit()
    cursor.close()
    connection.close()

    return {
        "id": comment_id,
        "user_id": user_id,
        "post_id": post_id,
        "comment_text": comment_text
    }, 201

@app.route("/comments/<int:user_id>", methods=["GET"])
def get_comments(user_id):
    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, user_id, post_id, comment_text, created_at
        FROM comments
        WHERE user_id = %s
        ORDER BY created_at;
        """,
        (user_id,)
    )

    comments = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        "user_id": user_id,
        "comments": [
            {
                "id": comment[0],
                "user_id": comment[1],
                "post_id": comment[2],
                "comment_text": comment[3],
                "created_at": comment[4].isoformat()
            }
            for comment in comments
        ]
    }, 200

@app.route("/reactions", methods=["POST"])
def create_reaction():
    data = request.get_json()

    user_id = data["user_id"]
    post_id = data["post_id"]
    reaction_type = data["reaction_type"]

    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO reactions (user_id, post_id, reaction_type)
        VALUES (%s, %s, %s)
        RETURNING id;
        """,
        (user_id, post_id, reaction_type)
    )

    reaction_id = cursor.fetchone()[0]

    connection.commit()
    cursor.close()
    connection.close()

    return {
        "id": reaction_id,
        "user_id": user_id,
        "post_id": post_id,
        "reaction_type": reaction_type
    }, 201

@app.route("/reactions/<int:user_id>", methods=["GET"])
def get_reactions(user_id):
    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, user_id, post_id, reaction_type, created_at
        FROM reactions
        WHERE user_id = %s
        ORDER BY created_at;
        """,
        (user_id,)
    )

    reactions = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        "user_id": user_id,
        "reactions": [
            {
                "id": reaction[0],
                "user_id": reaction[1],
                "post_id": reaction[2],
                "reaction_type": reaction[3],
                "created_at": reaction[4].isoformat()
            }
            for reaction in reactions
        ]
    }, 200

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    response = requests.post(
        f"{server_c_url}/users",
        headers={
            "X-API-Key": server_c_api_key
        },
        json=data,
        timeout=5
    )

    return response.json(), response.status_code

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    response = requests.post(
        f"{server_c_url}/login",
        headers={
            "X-API-Key": server_c_api_key
        },
        json=data,
        timeout=5
    )

    return response.json(), response.status_code

@app.route("/sync/likes", methods=["POST"])
def sync_like():
    data = request.get_json()

    response = requests.post(
        f"{server_c_url}/sync/likes",
        headers={
            "X-API-Key": server_c_api_key
        },
        json=data,
        timeout=5
    )

    return response.json(), response.status_code

if __name__ == "__main__":
    app.run(port=5002, debug=True)