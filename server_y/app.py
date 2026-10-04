from flask import Flask
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)

database_url = os.getenv("DATABASE_URL")

connection = psycopg2.connect(database_url)
print("Server Y successfully connected to PostgreSQL!")
connection.close()


@app.route("/")
def home():
    return {
        "server": "Y",
        "status": "running"
    }


if __name__ == "__main__":
    app.run(port=5001, debug=True)