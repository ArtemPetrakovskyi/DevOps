# DVO-L4-3C8B52
"""Допоміжний запуск лабораторної роботи №4 (Helm) з PyCharm.

Кожна підкоманда виконує реальні команди helm/kubectl/minikube/docker і друкує їх
(рядки, що починаються з «$»), тож вивід можна одразу використати для скріншотів.

Приклади:
    python scripts/lab4.py prepare
    python scripts/lab4.py all            # весь сценарій пунктів 6-9 підряд
    python scripts/lab4.py install-dev --dry-run   # лише показати команди

Потрібні лише Python 3.8+ та встановлені helm 3, kubectl, minikube (+docker).
"""
import argparse
import difflib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHART = ROOT / "chart" / "task-manager"
RELEASE = os.environ.get("LAB4_RELEASE", "tm")
NAMESPACE = os.environ.get("LAB4_NAMESPACE", "task-manager-lab4")
DRY = False


def run(cmd, check=True, capture=False):
    """Виконує команду без shell, друкуючи її як «$ ...»."""
    shown = " ".join(str(c) for c in cmd)
    print(f"\n$ {shown}", flush=True)
    if DRY:
        return ""
    exe = shutil.which(str(cmd[0]))
    if exe is None:
        sys.exit(f"Не знайдено програму «{cmd[0]}» у PATH. Див. README.md, розділ 1.")
    cmd = [exe] + [str(c) for c in cmd[1:]]
    res = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8",
                         stdout=subprocess.PIPE if capture else None,
                         stderr=subprocess.STDOUT if capture else None)
    if capture:
        print(res.stdout)
    if check and res.returncode != 0:
        sys.exit(f"Команда завершилась з кодом {res.returncode}")
    return res.stdout if capture else ""


def helm(*args, **kw):
    return run(["helm", *args], **kw)


def kubectl(*args, **kw):
    return run(["kubectl", *args], **kw)


def chart_path():
    return str(CHART.relative_to(ROOT))


def values(env):
    return str((CHART / f"values-{env}.yaml").relative_to(ROOT))


def pw_args():
    """Пароль БД беремо зі змінної оточення DB_PASSWORD (у файли значень не пишемо)."""
    pw = os.environ.get("DB_PASSWORD")
    return ["--set", f"secret.postgresPassword={pw}"] if pw else []


# ----------------------------------------------------------------- п. 1
def cmd_prepare(a):
    helm("version")
    run(["minikube", "start", "--driver=docker"])
    kubectl("get", "nodes")
    kubectl("get", "pods", "-n", "kube-system")
    print("\nВидалення об'єктів лабораторної №3 (namespace task-manager), щоб уникнути конфлікту імен:")
    kubectl("delete", "namespace", "task-manager", "--ignore-not-found")


def cmd_images(a):
    """Збирає та завантажує в minikube образи 1.0.0 та 1.1.0 з проєкту лабораторної №3."""
    src = Path(a.src).resolve()
    for ver in ("1.0.0", "1.1.0"):
        for comp in ("api", "web"):
            run(["docker", "build", "--build-arg", f"APP_VERSION={ver}",
                 "-t", f"tasks-{comp}:{ver}", str(src / comp)])
            run(["minikube", "image", "load", f"tasks-{comp}:{ver}"])
    run(["minikube", "image", "ls"])


# ----------------------------------------------------------------- п. 6
def cmd_diff_env(a):
    """Різниця між середовищами без встановлення в кластер (helm template + diff)."""
    outs = {}
    for env in ("dev", "prod"):
        print(f"\n$ helm template {RELEASE} {chart_path()} -f {values(env)} "
              f"--set secret.postgresPassword=demo > {env}.yaml")
        if DRY:
            continue
        out = subprocess.run(
            [shutil.which("helm"), "template", RELEASE, chart_path(), "-n", NAMESPACE,
             "-f", values(env), "--set", "secret.postgresPassword=demo"],
            cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, check=True).stdout
        outs[env] = out.splitlines()
    if DRY:
        return
    print("\n$ diff dev.yaml prod.yaml")
    for line in difflib.unified_diff(outs["dev"], outs["prod"], "dev.yaml", "prod.yaml", n=1, lineterm=""):
        print(line)
    print("\nПріоритет значень (від найнижчого до найвищого): values.yaml -> -f файл(и) "
          "(у порядку слідування) -> --set / --set-string.")
    print("Демонстрація: replicaCount для web у різних комбінаціях")
    for label, extra in [("values.yaml", []),
                         ("+ -f values-prod.yaml", ["-f", values("prod")]),
                         ("+ -f values-prod.yaml --set web.replicaCount=7",
                          ["-f", values("prod"), "--set", "web.replicaCount=7"])]:
        res = subprocess.run([shutil.which("helm"), "template", RELEASE, chart_path(),
                              "-s", "templates/deployment-web.yaml", *extra],
                             cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE).stdout
        reps = [l.strip() for l in res.splitlines() if l.strip().startswith("replicas:")]
        print(f"  {label:<48} -> {reps[0] if reps else '?'}")


# ----------------------------------------------------------------- п. 7
def cmd_lint(a):
    helm("lint", chart_path())
    helm("lint", chart_path(), "-f", values("dev"))
    helm("lint", chart_path(), "-f", values("prod"))


def cmd_template(a):
    helm("template", RELEASE, chart_path(), "-n", NAMESPACE, *pw_args())


def cmd_install_dev(a):
    helm("install", RELEASE, chart_path(), "-n", NAMESPACE, "--create-namespace",
         "-f", values("dev"), *pw_args(), "--wait", "--timeout", "3m")
    helm("list", "-n", NAMESPACE)
    helm("status", RELEASE, "-n", NAMESPACE)
    helm("get", "values", RELEASE, "-n", NAMESPACE)
    helm("get", "values", RELEASE, "-n", NAMESPACE, "--all")
    kubectl("get", "all,pvc,configmap,secret", "-n", NAMESPACE)
    print("\nДе Helm зберігає стан релізу: Secret типу helm.sh/release.v1 у namespace релізу")
    kubectl("get", "secret", "-n", NAMESPACE, "-l", "owner=helm")


# ----------------------------------------------------------------- п. 8
def cmd_upgrade_tag(a):
    helm("upgrade", RELEASE, chart_path(), "-n", NAMESPACE, "--reuse-values",
         "--set", "api.image.tag=1.1.0", "--set", "web.image.tag=1.1.0", "--wait", "--timeout", "3m")
    helm("get", "values", RELEASE, "-n", NAMESPACE)


def cmd_upgrade_prod(a):
    helm("upgrade", RELEASE, chart_path(), "-n", NAMESPACE, "-f", values("prod"),
         *pw_args(), "--wait", "--timeout", "5m")
    kubectl("get", "pods,ingress", "-n", NAMESPACE)


def cmd_history(a):
    helm("history", RELEASE, "-n", NAMESPACE)


def cmd_rollback(a):
    helm("rollback", RELEASE, str(a.revision), "-n", NAMESPACE, "--wait")
    helm("history", RELEASE, "-n", NAMESPACE)


def cmd_uninstall(a):
    helm("uninstall", RELEASE, "-n", NAMESPACE)
    kubectl("get", "all,pvc,configmap,secret,ingress", "-n", NAMESPACE)


# ----------------------------------------------------------------- п. 9б
def cmd_test(a):
    helm("test", RELEASE, "-n", NAMESPACE, "--logs")


def cmd_package(a):
    helm("package", chart_path(), "-d", "dist")


def cmd_all(a):
    """Весь сценарій п. 6-9: dev -> upgrade tag -> upgrade prod -> history -> rollback -> test -> uninstall."""
    cmd_diff_env(a)
    cmd_lint(a)
    cmd_install_dev(a)
    cmd_test(a)
    cmd_upgrade_tag(a)
    cmd_upgrade_prod(a)
    cmd_history(a)
    a.revision = 2
    cmd_rollback(a)
    cmd_uninstall(a)


def main():
    global DRY
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="лише показати команди, нічого не виконувати")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in [("prepare", cmd_prepare), ("diff-env", cmd_diff_env), ("lint", cmd_lint),
                     ("template", cmd_template), ("install-dev", cmd_install_dev),
                     ("upgrade-tag", cmd_upgrade_tag), ("upgrade-prod", cmd_upgrade_prod),
                     ("history", cmd_history), ("uninstall", cmd_uninstall), ("test", cmd_test),
                     ("package", cmd_package), ("all", cmd_all)]:
        sub.add_parser(name).set_defaults(fn=fn)
    s = sub.add_parser("rollback")
    s.add_argument("revision", type=int, nargs="?", default=2)
    s.set_defaults(fn=cmd_rollback)
    s = sub.add_parser("images")
    s.add_argument("--src", required=True, help="шлях до проєкту лабораторної №3 (де каталоги api/ та web/)")
    s.set_defaults(fn=cmd_images)
    a = p.parse_args()
    DRY = a.dry_run
    a.fn(a)


if __name__ == "__main__":
    main()
