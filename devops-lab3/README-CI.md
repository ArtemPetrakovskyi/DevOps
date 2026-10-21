# Лабораторна №2 — Continuous Integration (GitHub Actions)

Проєкт той самий, що в лабораторній №1 (`api` + `web` + PostgreSQL). Додано:

| Файл | Призначення |
|---|---|
| `.github/workflows/ci.yml` | пайплайн CI |
| `api/ruff.toml`, `web/ruff.toml` | конфігурація лінтера Ruff |
| `*/requirements-dev.txt` | додано `ruff` |
| `docker-compose.ghcr.yml` | запуск проєкту з образів, опублікованих у GHCR |
| `scripts/protect-main.sh` | (необов'язково) налаштування Branch Protection через `gh` |

## Що робить пайплайн

```
push / pull_request
        │
        ▼
 ┌───────────────────────────┐    matrix: api, web (паралельно, fail-fast: false)
 │ Build & Test (api | web)  │    Lint (ruff) → Build (compileall, pip check) → Test (pytest)
 └─────────────┬─────────────┘    кеш pip через actions/setup-python
               │ needs (обидва мають бути зелені)
               ▼
 ┌───────────────────────────────┐    matrix: api, web
 │ Docker build & scan (api|web) │    build (без push) → Trivy (CRITICAL/HIGH блокують)
 └─────────────┬─────────────────┘    → якщо це push: login у ghcr.io → push
               ▼
        ghcr.io/<owner>/<repo>-api  та  -web
        теги: sha-<commit>, <гілка>, latest (тільки main)
```

Для Pull Request публікація пропускається (`if: github.event_name == 'push'`).
Автентифікація в реєстрі — через вбудований секрет `GITHUB_TOKEN`, у репозиторії паролів немає.

Назви перевірок (їх треба зробити обов'язковими): 
`Build & Test (api)`, `Build & Test (web)`, `Docker build & scan (api)`, `Docker build & scan (web)`.

---

## Покрокова інструкція

### 0. Вимоги
- Той самий репозиторій на GitHub, що й у лабораторній №1.
- Репозиторій **публічний** (на безкоштовному плані Branch Protection працює лише для публічних репозиторіїв).
- Встановлені `git` і (для кроків 5–7 за бажанням) GitHub CLI `gh`.

### 1. Додати файли в репозиторій і запустити пайплайн
Розпакуйте архів `devops-lab2.zip` і скопіюйте його вміст **поверх** папки вашого проєкту (замінити файли, якщо питає). Далі у терміналі PyCharm:

```bash
git checkout main
git pull
git add .
git commit -m "Lab 2: CI pipeline (GitHub Actions)"
git push origin main
```

Відкрийте репозиторій на GitHub → вкладка **Actions** → запуск **CI**. Має бути 2 завдання *Build & Test* і 2 завдання *Docker build & scan*. Це перший push у `main`, тому образи одразу опублікуються з тегом `latest`.

> Якщо крок *Push image* падає з `denied: permission_denied: write_package`:
> **Settings → Actions → General → Workflow permissions → Read and write permissions → Save**, потім **Re-run all jobs**.

> Якщо Trivy зупиняє збірку через вразливість базового образу — це правильна поведінка блокуючого кроку. Оновіть тег базового образу у Dockerfile (наприклад `python:3.12-slim` → свіжіший patch) і запушіть знову.

### 2. Продемонструвати кешування
Вкладка **Actions** → відкрийте запуск → **Re-run all jobs**. У другому запуску в кроці *Set up Python* буде рядок `Cache restored from key: setup-python-...`, а встановлення залежностей пройде швидше.

### 3. Pull Request зі статусами
```bash
git checkout -b feature/ci-demo
# внесіть будь-яку невелику зміну, наприклад додайте рядок у README.md
git add .
git commit -m "Docs: small change to demo CI"
git push -u origin feature/ci-demo
gh pr create --fill        # або натисніть "Compare & pull request" на GitHub
```
У PR внизу сторінки буде блок **Checks** з усіма завданнями пайплайну (статуси ✓/✗). Результати лінтера відображаються як анотації у вкладці **Files changed**. Публікація образів у PR не виконується — крок *Push image* буде *skipped*.

### 4. Реєстр образів
На сторінці репозиторію праворуч — розділ **Packages** (або github.com → ваш профіль → **Packages**). Мають бути два пакети: `<repo>-api` та `<repo>-web` з тегами `latest`, `sha-...`, `main`.

Щоб `docker pull` працював без логіну, зробіть пакети публічними: відкрийте пакет → **Package settings** → **Change visibility** → **Public**. (Робиться для кожного з двох пакетів.) 
Якщо залишаєте приватними — залогіньтесь: створіть Personal access token (classic) з правом `read:packages` і виконайте
```bash
echo <TOKEN> | docker login ghcr.io -u <ваш-github-логін> --password-stdin
```

### 5. docker pull і запуск образів із реєстру
`<owner>/<repo>` — малими літерами (наприклад `ivan-petrenko/devops-lab1`).

```bash
docker pull ghcr.io/<owner>/<repo>-api:latest
docker pull ghcr.io/<owner>/<repo>-web:latest

# Linux / macOS / Git Bash
GHCR_REPO=<owner>/<repo> docker compose -f docker-compose.ghcr.yml up -d
# Windows PowerShell
$env:GHCR_REPO="<owner>/<repo>"; docker compose -f docker-compose.ghcr.yml up -d

docker compose -f docker-compose.ghcr.yml ps
curl http://localhost:5001/health
# браузер: http://localhost:5000

# зупинка
docker compose -f docker-compose.ghcr.yml down
```
Перед цим зупиніть стек із лабораторної №1 (`docker compose down`), бо порти 5000/5001 однакові.

### 6. Branch protection для main
**Варіант A — через інтерфейс GitHub:**
1. **Settings → Branches → Add branch protection rule** (на новому інтерфейсі: **Settings → Rules → Rulesets → New branch ruleset**).
2. Branch name pattern: `main`.
3. Увімкніть **Require a pull request before merging** (кількість схвалень можна лишити 0, щоб зливати власні PR).
4. Увімкніть **Require status checks to pass before merging** та **Require branches to be up to date before merging**. У полі пошуку додайте 4 перевірки:
   `Build & Test (api)`, `Build & Test (web)`, `Docker build & scan (api)`, `Docker build & scan (web)`.
   (Вони з'являються у списку лише після того, як хоча б раз відпрацювали — тому кроки 1 і 3 треба зробити раніше.)
5. Увімкніть **Do not allow bypassing the above settings** / **Include administrators**.
6. **Create / Save changes**.

**Варіант B — одна команда (потрібен `gh`, Git Bash на Windows):**
```bash
gh auth login
./scripts/protect-main.sh <owner>/<repo>
```

Перевірка: спроба `git push origin main` напряму має завершитись помилкою `protected branch hook declined` (зробіть невеликий коміт у `main` локально й запушіть — для скріншота).

### 7. Демонстрація заблокованого PR
**Сценарій 1 — ламаємо тест:**
```bash
git checkout main && git pull
git checkout -b demo/broken-test
```
У `api/app.py` у функції `create_task` змініть код відповіді з `201` на `200`:
`return jsonify(task.to_dict()), 201` → `return jsonify(task.to_dict()), 200`
```bash
git commit -am "Demo: break test"
git push -u origin demo/broken-test
gh pr create --fill
```
Результат: `Build & Test (api)` — червоний, `Docker build & scan (...)` — skipped, кнопка **Merge pull request** недоступна з написом *Merging is blocked / Required statuses must pass*.

**Сценарій 2 — ламаємо лінтер:**
```bash
git checkout main
git checkout -b demo/broken-lint
```
Додайте на початок `web/app.py` непотрібний імпорт: `import sys`
```bash
git commit -am "Demo: break lint"
git push -u origin demo/broken-lint
gh pr create --fill
```
Результат: крок *Lint (ruff)* падає (помилка `F401 'sys' imported but unused`), анотація видна у **Files changed**, злиття заблоковане.

Після демонстрації закрийте PR без злиття (**Close pull request**) і видаліть гілки.

---

## Локальна перевірка перед push (те саме, що робить CI)

```bash
cd api            # потім те саме для web
python -m venv .venv
.venv\Scripts\activate           # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check .
ruff format --check .            # щоб виправити форматування: ruff format .
python -m pytest -v
```

У PyCharm для цього можна використати вбудований термінал або налаштувати Ruff через **Settings → Tools → External Tools** / плагін Ruff.
