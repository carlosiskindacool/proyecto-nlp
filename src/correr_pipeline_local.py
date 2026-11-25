"""
Corre en cadena, en este computador, los pasos del pipeline final que dependen del diccionario y de los pares nuevos.

python src/correr_pipeline_local.py [--esperar-borradores] [--lote 4]

Pasos (cada uno escribe su log en logs/cadena_<paso>.log y si uno falla se detiene la cadena):
  1. (opcional) espera a que termine `idea_flo.borrador[.]py`, que escribe los borradores de entrenamiento nuevos.
  2. deja `data/interim/borrador_entrenamiento_nuevo.csv` como `borrador_entrenamiento.csv` (el anterior queda como
     `borrador_entrenamiento_v1.csv`).
  3. mT5 denso (models/mt5/mt5.ipynb) y 4. mT5 con MoE (models/mt5_moe/mt5_moe.ipynb), con
     `src/ejecutar_notebook_local.py`: el mismo código de los notebooks, con GPU local y lote 4 (la T4 de Colab
     usa lote 8; la RTX 3050 de 4 GB no lo aguanta en fp32). Si el MoE se queda sin memoria, reintenta con lote 2.
  5. métricas intrínsecas, 6. traducciones al inglés (evaluación extrínseca) y 7. resumen de la extrínseca.
Mantiene el equipo despierto mientras corre (Windows).
"""
import argparse
import ctypes
import os
import shutil
import subprocess
import sys
import time

PY = sys.executable
CONJUNTOS = ["annotation/lote1.csv", "annotation/lote_1_noticias.csv", "annotation/lote_1_tuits.csv",
             "annotation/lote_1_2_noticias.csv", "annotation/lote_1_2_tuits.csv"]


def registrar(msg):
    linea = f"{time.strftime('%H:%M:%S')} {msg}"
    print(linea, flush=True)
    with open("logs/cadena.log", "a", encoding="utf-8") as f:
        f.write(linea + "\n")


def correr(nombre, cmd, requerido=True):
    registrar(f"INICIO {nombre}")
    t0 = time.time()
    with open(f"logs/cadena_{nombre}.log", "w", encoding="utf-8") as log:
        r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    registrar(f"{'OK' if r.returncode == 0 else 'ERROR ' + str(r.returncode)} {nombre} ({(time.time() - t0) / 60:.1f} min)")
    if r.returncode and requerido:
        raise SystemExit(f"falló {nombre}; ver logs/cadena_{nombre}.log")
    return r.returncode


def notebook(nombre, ruta, lote, drive):
    return correr(nombre, [PY, "src/ejecutar_notebook_local.py", ruta, "--drive", drive,
                           "--set", f"LOTE={lote}", "--set", f"PARES={CONJUNTOS!r}"], requerido=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--esperar-borradores", action="store_true")
    ap.add_argument("--lote", type=int, default=4)
    ap.add_argument("--drive", default="D:/mt5_local_drive")
    args = ap.parse_args()
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)   # no dormir
    os.makedirs("logs", exist_ok=True)

    if args.esperar_borradores:
        registrar("espero a que terminen los borradores de entrenamiento")
        while subprocess.run(["powershell", "-NoProfile", "-Command",
                              "if (Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'idea_flo.borrador[.]py' }) { exit 1 }"]).returncode:
            time.sleep(30)
    nuevo, actual, v1 = ("data/interim/borrador_entrenamiento_nuevo.csv", "data/interim/borrador_entrenamiento.csv",
                         "data/interim/borrador_entrenamiento_v1.csv")
    if not os.path.exists(v1):
        shutil.copy(actual, v1)
    shutil.copy(nuevo, actual)
    registrar(f"entrenamiento: {sum(1 for _ in open(actual, encoding='utf-8')) - 1} filas (antes {sum(1 for _ in open(v1, encoding='utf-8')) - 1})")

    if notebook("mt5_denso", "models/mt5/mt5.ipynb", args.lote, args.drive):
        raise SystemExit("falló el mT5 denso; ver logs/cadena_mt5_denso.log")
    if notebook("mt5_moe", "models/mt5_moe/mt5_moe.ipynb", args.lote, args.drive):
        registrar("el MoE falló con lote %d; reintento con lote 2" % args.lote)
        if notebook("mt5_moe_lote2", "models/mt5_moe/mt5_moe.ipynb", 2, args.drive):
            raise SystemExit("falló el mT5 con MoE")
    correr("metricas", [PY, "src/chilenismos/metricas_normalizador.py"])
    correr("extrinseca", [PY, "src/eval_extrinseca.py"])
    correr("extrinseca_resumen", [PY, "src/eval_extrinseca_resumen.py"])
    registrar("FIN")


if __name__ == "__main__":
    main()
