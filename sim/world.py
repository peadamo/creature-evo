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

    def update_sensors(self):
        for creature in self.creatures:
            nearest_distance = float('inf')
            nearest_creature = None

            for other_creature in self.creatures:
                if id(other_creature) != id(creature):
                    distance = np.linalg.norm(np.array([other_creature.x, other_creature.y]) - np.array([creature.x, creature.y]))
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_creature = other_creature

            if nearest_creature:
                dx = (nearest_creature.x - creature.x) / self.physics.grid_size[0]
                dy = (nearest_creature.y - creature.y) / self.physics.grid_size[1]
            else:
                dx, dy = 0.0, 0.0

            for block in creature.genome.blocks:
                if block[0] == 'sonar':
                    x, y = block[1], block[2]
                    io_id_dx = f"neuron_sonar_{x}_{y}_dx"
                    io_id_dy = f"neuron_sonar_{x}_{y}_dy"
                    creature.neurons[io_id_dx] = dx
                    creature.neurons[io_id_dy] = dy

    def tick(self):
        self.tick_count += 1
        if len(self.creatures) < self.min_population:
            for _ in range(self.min_population - len(self.creatures)):
                genome = Genome.random_initial()
                self.spawn_creature(genome)

        # Actualizar sensores
        self.update_sensors()

        # Reproducción
        for creature in self.creatures[:]:
            if len(self.creatures) >= self.max_population:
                break
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
