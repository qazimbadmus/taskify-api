"""
Task Management API
--------------------
A secure REST API for managing user tasks with JWT authentication.

Features:
- User registration and login
- JWT-based authentication
- User-specific task CRUD operations
- SQLite database with SQLAlchemy ORM
- Production-ready error handling
"""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
import bcrypt
import datetime
import os
from functools import wraps

# ============================================
# 1. App Configuration
# ============================================

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Security configuration
# Use environment variable in production
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# JWT expiration time
JWT_EXPIRATION_HOURS = 24

db = SQLAlchemy(app)


# ============================================
# 2. Database Models
# ============================================

class User(db.Model):
    """User model for authentication."""
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        """Convert user object to dictionary for JSON responses."""
        return {
            "id": self.id,
            "username": self.username
        }


class Task(db.Model):
    """Task model for user-specific tasks."""
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def to_dict(self):
        """Convert task object to dictionary for JSON responses."""
        return {
            "id": self.id,
            "title": self.title,
            "done": self.done
        }


# ============================================
# 3. Database Initialization
# ============================================

# Create all tables if they don't exist
with app.app_context():
    db.create_all()


# ============================================
# 4. Authentication Helpers
# ============================================

def generate_token(user_id):
    """
    Generate a JWT token for a user.
    
    Args:
        user_id (int): The user's database ID
        
    Returns:
        str: A JWT token string
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    """
    Decode and validate a JWT token.
    
    Args:
        token (str): The JWT token to decode
        
    Returns:
        int or None: The user_id if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token


def token_required(f):
    """
    Decorator to protect routes that require authentication.
    
    Usage:
        @token_required
        def protected_route(user_id):
            # user_id is extracted from the token
            pass
    
    Returns:
        function: The wrapped function with user_id parameter
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401
        
        try:
            # Extract token from "Bearer <token>"
            token = auth_header.split(" ")[1]
        except IndexError:
            return jsonify({"error": "Invalid Authorization header format. Use: Bearer <token>"}), 401
        
        user_id = decode_token(token)
        
        if user_id is None:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        return f(user_id, *args, **kwargs)
    
    return decorated


# ============================================
# 5. Public Routes
# ============================================

@app.route("/")
def home():
    """Root endpoint — welcome message."""
    return jsonify({
        "message": "Welcome to the Task API",
        "endpoints": {
            "/register": "POST - Register a new user",
            "/login": "POST - Login and get a JWT token",
            "/tasks": "GET - Get all tasks (protected)",
            "/tasks": "POST - Create a new task (protected)"
        }
    })


@app.route("/ping")
def ping():
    """Health check endpoint."""
    return jsonify({"ping": "pong"})


@app.route("/register", methods=["POST"])
def register():
    """
    Register a new user.
    
    Request body:
        {
            "username": "alice",
            "password": "secure123"
        }
    
    Returns:
        201: User created successfully
        400: Missing username or password
        400: Username already taken
    """
    data = request.get_json()
    
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Username and password are required"}), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(username=data["username"]).first()
    if existing_user:
        return jsonify({"error": "Username already taken"}), 400
    
    # Hash the password
    password_hash = bcrypt.hashpw(
        data["password"].encode("utf-8"),
        bcrypt.gensalt()
    )
    
    # Create and save the user
    new_user = User(
        username=data["username"],
        password_hash=password_hash
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User created successfully"}), 201


@app.route("/login", methods=["POST"])
def login():
    """
    Login and receive a JWT token.
    
    Request body:
        {
            "username": "alice",
            "password": "secure123"
        }
    
    Returns:
        200: {"token": "eyJ..."}
        400: Missing username or password
        401: Invalid credentials
    """
    data = request.get_json()
    
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Username and password are required"}), 400
    
    user = User.query.filter_by(username=data["username"]).first()
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Verify password
    if not bcrypt.checkpw(data["password"].encode("utf-8"), user.password_hash):
        return jsonify({"error": "Invalid credentials"}), 401
    
    token = generate_token(user.id)
    return jsonify({"token": token}), 200


# ============================================
# 6. Protected Routes
# ============================================

@app.route("/tasks", methods=["GET"])
@token_required
def get_tasks(user_id):
    """
    Get all tasks for the authenticated user.
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: List of tasks (empty if none)
    """
    tasks = Task.query.filter_by(user_id=user_id).all()
    return jsonify([task.to_dict() for task in tasks])


@app.route("/tasks", methods=["POST"])
@token_required
def create_task(user_id):
    """
    Create a new task for the authenticated user.
    
    Headers:
        Authorization: Bearer <token>
    
    Request body:
        {
            "title": "Learn Flask"
        }
    
    Returns:
        201: Task created successfully
        400: Missing title
    """
    data = request.get_json()
    
    if not data or "title" not in data:
        return jsonify({"error": "Title is required"}), 400
    
    new_task = Task(
        title=data["title"],
        user_id=user_id
    )
    db.session.add(new_task)
    db.session.commit()
    
    return jsonify(new_task.to_dict()), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
@token_required
def update_task(user_id, task_id):
    """
    Update a task (mark as done or change title).
    
    Headers:
        Authorization: Bearer <token>
    
    Request body:
        {
            "title": "Updated title",  # optional
            "done": true               # optional
        }
    
    Returns:
        200: Task updated
        404: Task not found
        403: Task belongs to another user
    """
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    
    if not task:
        return jsonify({"error": "Task not found or belongs to another user"}), 404
    
    data = request.get_json()
    
    if "title" in data:
        task.title = data["title"]
    
    if "done" in data:
        task.done = data["done"]
    
    db.session.commit()
    return jsonify(task.to_dict()), 200


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@token_required
def delete_task(user_id, task_id):
    """
    Delete a task.
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: Task deleted
        404: Task not found
        403: Task belongs to another user
    """
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    
    if not task:
        return jsonify({"error": "Task not found or belongs to another user"}), 404
    
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({"message": "Task deleted successfully"}), 200


# ============================================
# 7. Run the Application
# ============================================

if __name__ == "__main__":
    app.run(debug=True)