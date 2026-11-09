"""
Arma la tabla de resultados con una columna por conjunto de pares.

python src/chilenismos/tabla.py [--resumen resultados/comparacion_baselines.csv]
    [--out resultados/tabla_por_conjunto.csv] [--md resultados/tabla_por_conjunto.md]

Lee el CSV largo que escriben baselines.py y baselines_llm.py (una fila por sistema y conjunto)
y escribe una tabla ancha: una fila por sistema y, por cada conjunto, BLEU y chrF.
"""
import argparse
import csv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumen", default="resultados/comparacion_baselines.csv")
    ap.add_argument("--out", default="resultados/tabla_por_conjunto.csv")
    ap.add_argument("--md", default="resultados/tabla_por_conjunto.md")
    args = ap.parse_args()

    with open(args.resumen, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    conjuntos = list(dict.fromkeys(r["pares"] for r in filas))
    sistemas = list(dict.fromkeys(r["sistema"] for r in filas))
    celda = {(r["sistema"], r["pares"]): r for r in filas}
    n = {c: next(r["n_pares"] for r in filas if r["pares"] == c) for c in conjuntos}

    cab = ["sistema"] + [f"{c} BLEU" for c in conjuntos] + [f"{c} chrF" for c in conjuntos]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cab)
        for s in sistemas:
            w.writerow([s] + [celda.get((s, c), {}).get("bleu", "") for c in conjuntos]
                       + [celda.get((s, c), {}).get("chrf", "") for c in conjuntos])

    with open(args.md, "w", encoding="utf-8") as f:
        f.write("| Sistema | " + " | ".join(f"{c.split("/")[-1]} ({n[c]} pares) BLEU / chrF" for c in conjuntos) + " |\n")
        f.write("|---|" + "---|" * len(conjuntos) + "\n")
        for s in sistemas:
            partes = []
            for c in conjuntos:
                r = celda.get((s, c))
                partes.append(f"{r['bleu'].replace('.', ',')} / {r['chrf'].replace('.', ',')}" if r else "–")
            f.write(f"| {s} | " + " | ".join(partes) + " |\n")
    print(f"{len(sistemas)} sistemas x {len(conjuntos)} conjuntos -> {args.out}, {args.md}")


if __name__ == "__main__":
    main()
