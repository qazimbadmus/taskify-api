from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean ,default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "done": self.done
        }

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return {"message": "Welcome to the Task API"}

@app.route("/ping")
def ping():
    return {"ping":"pong"}

@app.route("/tasks", methods=["GET"])
def tasks():
    tasks = Task.query.all()
    return jsonify([task.to_dict() for task in tasks])


@app.route("/tasks", methods=["POST"])
def create_task():

    data = request.get_json()
    if not data or "title" not in data:
        return {"Title is required"}, 400
    
    new_task = Task(title=data["title"])
    db.session.add(new_task)
    db.session.commit()

    return jsonify(new_task.to_dict()), 201


app.run(debug=True)
    