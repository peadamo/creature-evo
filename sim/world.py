import numpy as np
from sim.creature import Creature
from sim.physics import Physics
from sim.energy import Energy
from sim.reproduction import Reproduction
import random
from sim.genome import Genome

class World:
    def __init__(self, min_population=20, max_population=50):
        self.min_population = min_population
        self.max_population = max_population
        self.creatures = []
        self.physics = Physics()
        self.energy = Energy()
        self.reproduction = Reproduction()
        self.tick_count = 0

    def spawn_creature(self, genome):
        creature = Creature(genome)
        self.creatures.append(creature)
        self.physics.add_creature(creature)
        self.energy.add_creature(id(creature))

    def kill_creature(self, creature_id):
        self.creatures = [c for c in self.creatures if id(c) != creature_id]
        self.physics.creatures = [c for c in self.physics.creatures if id(c) != creature_id]
        del self.energy.energy_levels[creature_id]

    def tick(self):
        self.tick_count += 1
        if len(self.creatures) < self.min_population:
            for _ in range(self.min_population - len(self.creatures)):
                genome = Genome.random_initial()
                self.spawn_creature(genome)

        # Reproducción
        for creature in self.creatures[:]:
            new_genome = self.reproduction.reproduce(creature.genome, self.energy.energy_levels[id(creature)], 100)
            if new_genome:
                self.spawn_creature(new_genome)
                self.energy.consume_energy(id(creature), 5)  # Costo de reproducción

        # Actualizar energía y consumo
        for creature in self.creatures:
            creature.evaluate()
            self.physics.update_positions()
            self.physics.handle_collisions()

        # Muerte por energía agotada
        for creature in self.creatures[:]:
            if self.energy.check_death(id(creature)):
                self.kill_creature(id(creature))

    def run(self, num_ticks):
        for _ in range(num_ticks):
            self.tick()
            print(f"Tick {_}: {len(self.creatures)} creatures")
