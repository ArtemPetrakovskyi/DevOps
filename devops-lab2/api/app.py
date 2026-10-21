"""API-сервіс: CRUD для задач (tasks). Зберігає дані в PostgreSQL (у Docker)
або в локальному SQLite (коли запускається напряму з PyCharm)."""

import os

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, nullable=False, default=False)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "done": self.done}


def create_app(database_url=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        database_url or os.getenv("DATABASE_URL") or "sqlite:///tasks.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/api/tasks")
    def list_tasks():
        tasks = Task.query.order_by(Task.id).all()
        return jsonify([t.to_dict() for t in tasks])

    @app.post("/api/tasks")
    def create_task():
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify(error="title is required"), 400
        task = Task(title=title)
        db.session.add(task)
        db.session.commit()
        return jsonify(task.to_dict()), 201

    @app.patch("/api/tasks/<int:task_id>")
    def toggle_task(task_id):
        task = db.session.get(Task, task_id)
        if task is None:
            return jsonify(error="not found"), 404
        data = request.get_json(silent=True) or {}
        task.done = bool(data.get("done", not task.done))
        db.session.commit()
        return jsonify(task.to_dict())

    @app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id):
        task = db.session.get(Task, task_id)
        if task is None:
            return jsonify(error="not found"), 404
        db.session.delete(task)
        db.session.commit()
        return "", 204

    return app


if __name__ == "__main__":
    # Запуск з PyCharm: http://localhost:5001
    create_app().run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
