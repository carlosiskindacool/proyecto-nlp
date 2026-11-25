"""
Ejecuta en este computador (con su GPU) un notebook de Colab del proyecto, sin cambiar su código.

python src/ejecutar_notebook_local.py models/mt5/mt5.ipynb [--drive D:/mt5_local_drive]
    [--set EPOCAS=1 --set LOTE=4 ...]

Se ejecutan tal cual las celdas de código del notebook (mismo modelo, mismos hiperparámetros y mismo código de
entrenamiento y evaluación que en Colab). Lo único que cambia es el entorno:
  - Google Drive se reemplaza por una carpeta local (--drive): ahí quedan los pesos, las predicciones y el resumen.
  - se omiten las celdas `!pip` (las dependencias ya están instaladas) y la que clona el repo de GitHub: se usa
    esta misma carpeta del repo, sin `git pull`.
  - --set NOMBRE=valor reemplaza una constante de la celda de configuración (por ejemplo ENTRENAMIENTO o PARES).
Al terminar copia las predicciones a data/processed/ y el resumen a resultados/comparacion_mt5.csv.
"""
import argparse
import json
import os
import re
import shutil
import sys
import types


def drive_falso(raiz):
    """Un módulo google.colab.drive que solo crea carpetas locales."""
    colab = types.ModuleType("google.colab")
    drive = types.ModuleType("google.colab.drive")
    drive.mount = lambda ruta, **kw: os.makedirs(os.path.join(raiz, "MyDrive"), exist_ok=True)
    drive.flush_and_unmount = lambda: None
    colab.drive = drive
    import google  # el paquete real (protobuf también vive en `google`): solo se le agrega `colab`
    google.colab = colab
    sys.modules.update({"google.colab": colab, "google.colab.drive": drive})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("notebook")
    ap.add_argument("--drive", default="D:/mt5_local_drive")
    ap.add_argument("--set", action="append", default=[], metavar="NOMBRE=VALOR", help="valor en sintaxis de Python")
    args = ap.parse_args()

    repo = os.getcwd()
    raiz_drive = os.path.abspath(args.drive).replace("\\", "/")
    ajustes = {"RAIZ_DRIVE": repr(raiz_drive), "REPO": repr(repo.replace("\\", "/"))}
    for s in args.set:
        nombre, valor = s.split("=", 1)
        ajustes[nombre] = valor
    os.makedirs(os.path.join(raiz_drive, "MyDrive"), exist_ok=True)

    celdas = [''.join(c["source"]) for c in json.load(open(args.notebook, encoding="utf-8"))["cells"]
              if c["cell_type"] == "code"]
    ns = {"__name__": "__main__"}
    for n, codigo in enumerate(celdas, 1):
        if codigo.lstrip().startswith("!"):
            continue                       # !pip install ...
        if 'subprocess.run(["git"' in codigo:
            # en Colab clona el repo; aquí se usa esta carpeta tal cual
            codigo = ("import os, sys\nos.chdir(REPO)\nsys.path.insert(0, f'{REPO}/src/chilenismos')\n")
        if re.search(r"^NOMBRE = ", codigo, re.M):
            for nombre, valor in ajustes.items():
                codigo, k = re.subn(rf"^{nombre} = .*$", lambda m: f"{nombre} = {valor}", codigo, flags=re.M)
                if not k:
                    raise SystemExit(f"La celda de configuración no tiene {nombre}")
            # los pesos temporales van junto al drive local, no en /content
            codigo = re.sub(r'^DIR_LOCAL = .*$', lambda m: f'DIR_LOCAL = f"{raiz_drive}/_mejor_{{NOMBRE}}"', codigo, flags=re.M)
        print(f"\n>>> celda {n}/{len(celdas)}", flush=True)
        usa_drive = "google.colab" in codigo
        if usa_drive:
            drive_falso(raiz_drive)        # solo mientras corre la celda que lo importa (otras librerías miran sys.modules)
        try:
            exec(compile(codigo, f"{os.path.basename(args.notebook)}[{n}]", "exec"), ns)
        finally:
            if usa_drive:
                sys.modules.pop("google.colab.drive", None)
                sys.modules.pop("google.colab", None)

    base = f"{ns['CARPETA_DRIVE']}"
    pred = ns["RUTA_PREDICCIONES"]
    os.makedirs("data/processed", exist_ok=True)
    shutil.copy(pred, os.path.join("data/processed", os.path.basename(pred)))
    os.makedirs("resultados", exist_ok=True)
    if os.path.exists(ns["RUTA_RESUMEN"]):
        shutil.copy(ns["RUTA_RESUMEN"], "resultados/comparacion_mt5.csv")
    print(f"\nPredicciones copiadas a data/processed/{os.path.basename(pred)}; pesos en {ns['DIR_PESOS']}")


if __name__ == "__main__":
    main()
