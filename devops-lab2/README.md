# Лабораторна №1 — Віртуалізація та контейнеризація (DevOps)

Проєкт «Менеджер задач» з трьох частин:

| Частина | Технології | Порт (хост) | Опис |
|---|---|---|---|
| `db`  | PostgreSQL 16 | — (лише всередині мережі Docker) | база даних |
| `api` | Python 3.12, Flask, SQLAlchemy, gunicorn | 5001 | REST API задач |
| `web` | Python 3.12, Flask, requests, gunicorn | 5000 | HTML-інтерфейс, ходить в `api` |

```
devops-lab1/
├── api/   (app.py, tests/, Dockerfile, requirements*.txt)
├── web/   (app.py, templates/, tests/, Dockerfile, requirements*.txt)
├── docker-compose.yml
└── README.md
```

---

## Варіант A. Запуск через Docker (основний, те, що вимагає лабораторна)

Потрібно: встановлений **Docker Desktop** (Windows/macOS) або Docker Engine + Compose plugin (Linux). Перевірка:

```bash
docker --version
docker compose version
```

Команди виконуйте з кореня проєкту (папка, де лежить `docker-compose.yml`).
У PyCharm: **View → Tool Windows → Terminal** (відкриється у корені проєкту).

```bash
# 1. Зібрати образи та запустити все у фоні
docker compose up --build -d

# 2. Подивитись статус контейнерів (мають бути Up, db — healthy)
docker compose ps

# 3. Подивитись логи (Ctrl+C — вийти з логів)
docker compose logs -f

# 4. Перевірка роботи
#    Браузер:  http://localhost:5000   (інтерфейс)
#    API:      http://localhost:5001/api/tasks
#    Health:   http://localhost:5001/health
curl http://localhost:5001/health
curl -X POST http://localhost:5001/api/tasks -H "Content-Type: application/json" -d "{\"title\": \"Тестова задача\"}"
curl http://localhost:5001/api/tasks

# 5. Перевірити, що дані справді лежать у PostgreSQL
docker compose exec db psql -U tasks -d tasks -c "SELECT * FROM task;"

# 6. Перелік образів
docker images

# 7. Зупинити (дані БД зберігаються у volume)
docker compose down

# 8. Зупинити і видалити дані БД
docker compose down -v
```

> У Windows PowerShell рядок з `curl -X POST ...` зручніше замінити на:
> `curl.exe -X POST http://localhost:5001/api/tasks -H "Content-Type: application/json" -d '{\"title\":\"Тест\"}'`
> або просто додати задачу через браузер.

### Запуск тестів у контейнері (необов'язково)

```bash
docker compose run --rm --no-deps -v ./api/tests:/app/tests api sh -c "pip install -q pytest && python -m pytest -q /app/tests -p no:cacheprovider --rootdir=/app"
```

Простіше запускати тести локально (див. нижче).

---

## Варіант B. Запуск у PyCharm без Docker (для розробки й тестів)

У цьому режимі `api` використовує локальний SQLite (файл `tasks.db`), PostgreSQL не потрібен.

### 1. Відкрити проєкт
**File → Open** → оберіть папку `devops-lab1`.

### 2. Створити віртуальні середовища (по одному на сервіс)
Відкрийте Terminal у PyCharm.

**Windows (PowerShell):**
```powershell
cd api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
deactivate
cd ..\web
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
deactivate
cd ..
```

**macOS / Linux:**
```bash
cd api && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt && deactivate && cd ..
cd web && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt && deactivate && cd ..
```

### 3. Налаштувати інтерпретатор і Run-конфігурації
Для кожного сервісу: **Run → Edit Configurations → + → Python**

- **API**: Script path = `api/app.py`, Working directory = `api`, Python interpreter = `api/.venv` (Add Interpreter → Existing → вкажіть `api/.venv/Scripts/python.exe` або `api/.venv/bin/python`).
- **WEB**: Script path = `web/app.py`, Working directory = `web`, interpreter = `web/.venv`. Environment variables: `API_URL=http://localhost:5001`.

Запустіть спочатку **API**, потім **WEB**. Відкрийте http://localhost:5000.

### 4. Запуск тестів у PyCharm
**Run → Edit Configurations → + → Python tests → pytest**:
- для API: Target = Custom, `api/tests`, Working directory = `api`, interpreter `api/.venv`;
- для WEB: `web/tests`, Working directory = `web`, interpreter `web/.venv`.

Або з терміналу:
```bash
cd api && python -m pytest -v       # (з активованим api/.venv)
cd web && python -m pytest -v       # (з активованим web/.venv)
```

---

## Git / GitHub

```bash
git init
git add .
git commit -m "Lab 1: Docker + docker-compose"
git branch -M main
# створіть порожній репозиторій на github.com (без README), потім:
git remote add origin https://github.com/<ваш-логін>/devops-lab1.git
git push -u origin main
```

## Часті проблеми

- **`port is already allocated`** — порт 5000/5001 зайнятий. macOS: вимкніть AirPlay Receiver (Settings → General → AirDrop & Handoff) або змініть порт ліворуч у `docker-compose.yml` (наприклад `"8080:5000"`).
- **`Cannot connect to the Docker daemon`** — запустіть Docker Desktop і зачекайте, поки він стартує.
- **Сторінка показує «API недоступний»** — `api` ще стартує або не запущений; перевірте `docker compose logs api`.
