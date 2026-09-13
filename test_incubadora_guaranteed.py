#!/usr/bin/env python3
"""Test: verifica que TODAS las criaturas tengan incubadora"""

from sim.world import World

w = World()

# Forzar 1 tick para que se llene min_population
w.tick()

print(f"Poblacion: {len(w.creatures)}")
for i, c in enumerate(w.creatures):
    bloques = [b[0] for b in c.genome.blocks]
    tiene_incubadora = 'incubadora' in bloques
    print(f"  Criatura {i}: {bloques} -> incubadora={tiene_incubadora}")

total = len(w.creatures)
con_incubadora = sum(1 for c in w.creatures if any(b[0] == 'incubadora' for b in c.genome.blocks))
print(f"\nResumen: {con_incubadora}/{total} tienen incubadora ({100*con_incubadora/total:.1f}%)")
