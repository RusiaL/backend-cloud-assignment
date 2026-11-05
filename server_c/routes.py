from flask import Blueprint, request, current_app
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import os
import smtplib

from email.message import EmailMessage
from urllib.parse import quote

from server_c.models import User, EmailVerificationToken
from server_c.extensions import db

api = Blueprint("api", __name__)

def hash_verification_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def create_email_verification_token(user):
    token = secrets.token_urlsafe(32)

    verification_record = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_verification_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )

    db.session.add(verification_record)
    # db.session.commit()

    return token

@api.route("/", methods=["GET"])
def home():
    return {
        "server": "C",
        "status": "running"
    }, 200

@api.route("/users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True) or {}

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return {
            "error": "Username, email and password are required"
        }, 400

    existing_user = User.query.filter(
        (User.username == username) |
        (User.email == email)
    ).first()

    if existing_user:
        return {
            "error": "Username or email already exists"
        }, 409

    password_hash = generate_password_hash(password)

    user = User(
        username=username,
        email=email,
        password_hash=password_hash
    )

    db.session.add(user)

    try:
        db.session.flush()

        verification_token = create_email_verification_token(user)

        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Failed to complete user registration"
        )
        return {
            "error": "Registration could not be completed"
        }, 500

    try:
        send_verification_email(user, verification_token)
        email_status = "Verification email sent"
    except Exception:
        current_app.logger.exception(
            "Failed to send verification email"
        )
        email_status = "Registration completed, but verification email could not be sent"

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "message": email_status
    }, 201

@api.route("/users/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    if get_jwt_identity() != str(user_id):
        return {
            "error": "You can only access your own profile"
        }, 403

    user = db.session.get(User, user_id)

    if user is None:
        return {
            "error": "User not found"
        }, 404

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_verified": user.is_verified
    }, 200

@api.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {
            "error": "Username and password are required"
        }, 400

    user = User.query.filter_by(username=username).first()

    if user is None or not check_password_hash(
        user.password_hash,
        password
    ):
        return {
            "error": "Invalid username or password"
        }, 401

    if not user.is_verified:
        return {
            "error": "Email address is not verified"
        }, 403

    access_token = create_access_token(
        identity=str(user.id)
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }, 200

@api.route("/verify-email/<token>", methods=["GET"])
def verify_email(token):
    token_hash = hash_verification_token(token)

    verification_record = EmailVerificationToken.query.filter_by(
        token_hash=token_hash
    ).first()

    if verification_record is None:
        return {
            "error": "Invalid verification token"
        }, 400

    if verification_record.used_at is not None:
        return {
            "error": "Verification token has already been used"
        }, 400

    now = datetime.now(timezone.utc)

    if verification_record.expires_at <= now:
        return {
            "error": "Verification token has expired"
        }, 400

    try:
        user = verification_record.user
        user.is_verified = True
        verification_record.used_at = now

        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Failed to verify email"
        )
        return {
            "error": "Email verification could not be completed"
        }, 500

    return {
        "message": "Email successfully verified"
    }, 200

@api.route("/resend-verification", methods=["POST"])
def resend_verification():
    data = request.get_json(silent=True) or {}
    email = data.get("email")

    if not email:
        return {
            "error": "Email is required"
        }, 400

    user = User.query.filter_by(email=email).first()

    if user and not user.is_verified:
        try:
            now = datetime.now(timezone.utc)

            previous_tokens = EmailVerificationToken.query.filter_by(
                user_id=user.id,
                used_at=None
            ).all()

            for record in previous_tokens:
                record.used_at = now

            token = create_email_verification_token(user)

            db.session.commit()

        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                "Failed to prepare verification token"
            )
            return {
                "error": "Verification email could not be prepared"
            }, 500

        try:
            send_verification_email(user, token)
        except Exception:
            current_app.logger.exception(
                "Failed to resend verification email"
            )

    return {
        "message": "If the account exists and is not verified, a verification email has been sent."
    }, 200



def send_verification_email(user, token):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL")

    vercel_env = os.getenv("VERCEL_ENV")
    vercel_url = os.getenv("VERCEL_URL")
    production_url = os.getenv("VERCEL_PROJECT_PRODUCTION_URL")

    if vercel_env == "production" and production_url:
        base_url = f"https://{production_url}"
    elif vercel_url:
        base_url = f"https://{vercel_url}"
    else:
        base_url = os.getenv("APP_BASE_URL")

    required_settings = [
        smtp_host,
        smtp_username,
        smtp_password,
        smtp_from_email,
        base_url,
    ]

    if not all(required_settings):
        raise RuntimeError("SMTP settings are not fully configured.")

    verification_url = (
        f"{base_url}/verify-email/{quote(token)}"
    )

    message = EmailMessage()
    message["Subject"] = "Verify your email address"
    message["From"] = smtp_from_email
    message["To"] = user.email

    message.set_content(
        f"""
Hello {user.username},

Thank you for registering!

Please verify your email address by clicking the link below:

{verification_url}

This link expires in 24 hours.

If you did not create this account, please ignore this email.
"""
    )

    with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(message)
    
@api.route("/sync/likes", methods=["POST"])
def sync_likes():
    api_key = request.headers.get("X-API-Key")
    expected_api_key = current_app.config.get("SERVER_X_API_KEY")

    if not expected_api_key or api_key != expected_api_key:
        return {
            "error": "Unauthorized"
        }, 401

    server_y_url = current_app.config.get("SERVER_Y_URL")
    server_y_api_key = current_app.config.get("SERVER_Y_API_KEY")

    if not server_y_url or not server_y_api_key:
        current_app.logger.error(
            "Server Y configuration is incomplete"
        )
        return {
            "error": "Server Y is not configured"
        }, 503

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return {
            "error": "Invalid or missing JSON payload"
        }, 400

    try:
        response = requests.post(
            f"{server_y_url}/internal/likes",
            headers={
                "X-API-Key": server_y_api_key
            },
            json=data,
            timeout=5
        )

        try:
            response_data = response.json()
        except ValueError:
            current_app.logger.error(
                "Server Y returned a non-JSON response"
            )
            return {
                "error": "Invalid response from Server Y"
            }, 502

        return response_data, response.status_code

    except requests.RequestException:
        current_app.logger.exception(
            "Could not connect to Server Y"
        )
        return {
            "error": "Could not connect to Server Y"
        }, 502