# Task Management API

A secure REST API for managing user tasks with JWT authentication.

## Features
- User registration and login
- JWT-based authentication
- Create, view, update, delete tasks
- SQLite database with SQLAlchemy ORM

## Live Demo
[https://taskify-api-bph3.onrender.com](https://taskify-api-bph3.onrender.com)

## Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /register | Create a new user | No |
| POST | /login | Get JWT token | No |
| GET | /tasks | Get all tasks | Yes |
| POST | /tasks | Create a task | Yes |
| PUT | /tasks/{id} | Update a task | Yes |
| DELETE | /tasks/{id} | Delete a task | Yes |

## Local Setup

```bash
pip install -r requirements.txt
python app.py
```

**API Testing**

You can test the API using Postman.  
Import this collection: [Task_API.postman_collection.json](./Task_API.postman_collection.json)
