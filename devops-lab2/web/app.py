"""Web-сервіс: HTML-інтерфейс, який спілкується з API по HTTP."""

import os

import requests
from flask import Flask, redirect, render_template, request, url_for


def create_app(api_url=None):
    app = Flask(__name__)
    app.config["API_URL"] = (api_url or os.getenv("API_URL") or "http://localhost:5001").rstrip("/")

    def api(path):
        return f"{app.config['API_URL']}{path}"

    @app.get("/")
    def index():
        error = None
        tasks = []
        try:
            resp = requests.get(api("/api/tasks"), timeout=5)
            resp.raise_for_status()
            tasks = resp.json()
        except requests.RequestException:
            error = "API недоступний"
        return render_template("index.html", tasks=tasks, error=error)

    @app.post("/add")
    def add():
        title = request.form.get("title", "").strip()
        if title:
            try:
                requests.post(api("/api/tasks"), json={"title": title}, timeout=5)
            except requests.RequestException:
                pass
        return redirect(url_for("index"))

    @app.post("/toggle/<int:task_id>")
    def toggle(task_id):
        try:
            requests.patch(api(f"/api/tasks/{task_id}"), json={}, timeout=5)
        except requests.RequestException:
            pass
        return redirect(url_for("index"))

    @app.post("/delete/<int:task_id>")
    def delete(task_id):
        try:
            requests.delete(api(f"/api/tasks/{task_id}"), timeout=5)
        except requests.RequestException:
            pass
        return redirect(url_for("index"))

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    # Запуск з PyCharm: http://localhost:5000
    create_app().run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
