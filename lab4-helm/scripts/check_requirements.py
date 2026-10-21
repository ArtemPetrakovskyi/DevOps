# DVO-L4-3C8B52
"""Самоперевірка вимог лабораторної: додаток А та вимоги до здачі (потрібен лише helm)."""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHART = ROOT / "chart" / "task-manager"
CODE = "# DVO-L4-3C8B52"
ok = True


def check(cond, msg):
    global ok
    print(("[ OK ] " if cond else "[FAIL] ") + msg)
    ok = ok and cond


# А.1, А.2 — кодування, LF, перший рядок
files = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix in
         {".yaml", ".yml", ".tpl", ".txt", ".py", ".md", ".sh", ".ps1"} or p.name == ".helmignore"]
files = [p for p in files if "dist" not in p.parts and ".git" not in p.parts and "docs" not in p.parts]
bad = []
for p in files:
    raw = p.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        bad.append(f"{p.name}: не UTF-8")
        continue
    if b"\r\n" in raw:
        bad.append(f"{p.name}: CRLF")
    if text.split("\n", 1)[0].strip() != CODE:
        bad.append(f"{p.name}: немає шифру у першому рядку")
check(not bad, f"А.1/А.2: {len(files)} файлів — UTF-8, LF, шифр у першому рядку {bad or ''}")

# А.4
readme = (ROOT / "README.md").read_text(encoding="utf-8").rstrip()
check("## Подяки" in readme.splitlines()[-3:][0] or readme.splitlines()[-2].startswith("## Подяки"),
      "А.4: README завершується розділом «Подяки»")

helm = shutil.which("helm")
if not helm:
    sys.exit("helm не знайдено — рендер-перевірки пропущено")
out = subprocess.run([helm, "template", "chk", str(CHART), "--set", "ingress.enabled=true"],
                     text=True, encoding="utf-8", stdout=subprocess.PIPE, check=True).stdout
docs = [d for d in out.split("\n---\n") if "kind:" in d]
check(len(docs) >= 11, f"Рендер: {len(docs)} об'єктів (Secret, ConfigMap, PVC, 3 Deployment, 3 Service, Ingress, Job-хук, Pod-тест)")
check(all("mascot: \"harbuz\"" in d and "devops-lab/mascot-approved: \"true\"" in d for d in docs),
      "А.3: усі об'єкти мають мітку mascot та анотацію devops-lab/mascot-approved")
src = "\n".join(p.read_text(encoding="utf-8") for p in (CHART / "templates").rglob("*.yaml"))
check(not re.search(r"\b(replicas|replicaCount):\s*\d", src), "У шаблонах немає жорстко прописаних реплік")
check(not re.search(r"image:\s*\"?[a-z]+[:/][^{\"\s]*\d", src), "У шаблонах немає жорстко прописаних образів/тегів")
check("lab-only-password" not in (CHART / "values.yaml").read_text(encoding="utf-8"),
      "У values немає реальних паролів")
sys.exit(0 if ok else 1)
