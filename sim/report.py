"""Genera gráficos a partir de sim_log.csv y lineage.csv.

Uso: python -m sim.report [sim_log.csv] [lineage.csv] [carpeta_salida]
No se llama automáticamente desde ningún otro lado - es una herramienta
manual de análisis offline.
"""
import sys
import csv

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def load_csv(path):
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def to_float_series(rows, key):
    return [float(r[key]) for r in rows]


def plot_sim_log(rows, out_dir):
    ticks = to_float_series(rows, 'tick_count')

    fig, axes = plt.subplots(3, 2, figsize=(12, 10))

    axes[0, 0].plot(ticks, to_float_series(rows, 'population_count'))
    axes[0, 0].set_title('Población')

    axes[0, 1].plot(ticks, to_float_series(rows, 'max_generation_ever'))
    axes[0, 1].set_title('Generación máxima alcanzada')

    axes[1, 0].plot(ticks, to_float_series(rows, 'avg_energy_level'), label='promedio')
    axes[1, 0].plot(ticks, to_float_series(rows, 'min_energy'), label='mínima')
    axes[1, 0].set_title('Energía')
    axes[1, 0].legend()

    axes[1, 1].plot(ticks, to_float_series(rows, 'avg_distance_to_nearest_food'))
    axes[1, 1].set_title('Distancia promedio a comida más cercana')

    axes[2, 0].plot(ticks, to_float_series(rows, 'eggs_hatched_per_20ticks'), label='huevos eclosionados')
    axes[2, 0].plot(ticks, to_float_series(rows, 'artificial_refills_per_20ticks'), label='rellenos artificiales')
    axes[2, 0].set_title('Reproducción real vs. relleno artificial')
    axes[2, 0].legend()

    axes[2, 1].plot(ticks, to_float_series(rows, 'avg_blocks_per_creature'))
    axes[2, 1].set_title('Bloques promedio por criatura')

    fig.tight_layout()
    out_path = f"{out_dir}/sim_log_report.png"
    fig.savefig(out_path)
    print(f"Guardado: {out_path}")


def plot_lineage(rows, out_dir):
    if not rows:
        print("lineage.csv vacío, sin nacimientos registrados todavía.")
        return
    gens = [int(r['generation']) for r in rows]
    ticks = [int(r['birth_tick']) for r in rows]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(ticks, gens, alpha=0.6)
    ax.set_xlabel('Tick de nacimiento')
    ax.set_ylabel('Generación')
    ax.set_title('Nacimientos por huevo a lo largo del tiempo')
    out_path = f"{out_dir}/lineage_report.png"
    fig.savefig(out_path)
    print(f"Guardado: {out_path}")


if __name__ == '__main__':
    sim_log_path = sys.argv[1] if len(sys.argv) > 1 else 'sim_log.csv'
    lineage_path = sys.argv[2] if len(sys.argv) > 2 else 'lineage.csv'
    out_dir = sys.argv[3] if len(sys.argv) > 3 else '.'

    try:
        rows = load_csv(sim_log_path)
        plot_sim_log(rows, out_dir)
    except FileNotFoundError:
        print(f"No se encontró {sim_log_path}")

    try:
        rows = load_csv(lineage_path)
        plot_lineage(rows, out_dir)
    except FileNotFoundError:
        print(f"No se encontró {lineage_path}")
