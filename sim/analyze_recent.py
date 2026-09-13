#!/usr/bin/env python3
"""Analisis rapido de reproduccion y evolucion del ultimo sim_log.csv"""

import csv
import sys

def analyze():
    try:
        with open('sim_log.csv', 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        print("No sim_log.csv found. Run simulation first.")
        return

    if not rows:
        print("sim_log.csv is empty")
        return

    # Stats
    total_eggs = sum(float(r.get('eggs_hatched_per_20ticks', 0)) for r in rows)
    total_ticks = int(rows[-1]['tick_count'])

    incubadora_100pct = all(float(r['pct_with_incubadora']) == 1.0 for r in rows)

    avg_wired = sum(float(r['pct_incubadora_wired']) for r in rows) / len(rows)
    max_gen = max(int(float(r['max_generation_ever'])) for r in rows)

    print(f"[STATS] Analisis de {total_ticks} ticks:")
    print(f"  * Huevos eclosionados: {int(total_eggs)} (~{total_eggs/total_ticks:.3f} por tick)")
    print(f"  * Incubadora garantizada: {'SI (100%)' if incubadora_100pct else 'NO'}")
    print(f"  * Incubadora cableada (promedio): {avg_wired*100:.1f}%")
    print(f"  * Generacion maxima alcanzada: {max_gen}")
    print(f"  * Poblacion final: {rows[-1]['population_count']} criaturas")

    # Tendencia de reproduccion ultimos 500 ticks
    if len(rows) > 10:
        recent = rows[-10:]
        recent_eggs = sum(float(r.get('eggs_hatched_per_20ticks', 0)) for r in recent)
        print(f"\n  Ultimos ~500 ticks:")
        print(f"    * Huevos: {int(recent_eggs)} (~{recent_eggs/500:.3f} por tick)")
        print(f"    * Generacion maxima: {int(float(recent[-1]['max_generation_ever']))}")

    print("\n  -> Ver sim/report.py para graficos detallados")

if __name__ == '__main__':
    analyze()
