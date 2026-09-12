import numpy as np
from sim.creature import Creature
from sim.physics import Physics
from sim.energy import Energy
from sim.reproduction import Reproduction
import random
from sim.genome import Genome
import csv

class World:
    def __init__(self, min_population=20, max_population=50):
        import random
        self.min_population = min_population
        self.max_population = max_population
        self.creatures = []
        self.physics = Physics()
        self.energy = Energy()
        self.reproduction = Reproduction()
        self.tick_count = 0
        self.food_pellets = [{'x': random.uniform(0, self.physics.grid_size[0]), 'y': random.uniform(0, self.physics.grid_size[1]), 'amount': random.uniform(10, 100)} for _ in range(30)]
        self.eggs = []
        self.creature_eggs = {}
        self.fat_levels = {}

    def spawn_creature(self, genome, position=None):
        creature = Creature(genome)
        self.creatures.append(creature)
        self.physics.add_creature(creature, position)
        self.energy.add_creature(id(creature))
        self.fat_levels[id(creature)] = 0

    def kill_creature(self, creature_id):
        self.creatures = [c for c in self.creatures if id(c) != creature_id]
        self.physics.creatures = [c for c in self.physics.creatures if id(c) != creature_id]
        del self.energy.energy_levels[creature_id]
        self.fat_levels.pop(creature_id, None)
        egg = self.creature_eggs.pop(creature_id, None)
        if egg in self.eggs:
            self.eggs.remove(egg)
        if creature_id in self.fat_levels:
            del self.fat_levels[creature_id]

    def update_sensors(self):
        for creature in self.creatures:
            nearest_distance = float('inf')
            nearest_creature = None

            for other_creature in self.creatures:
                if id(other_creature) != id(creature):
                    distance = np.linalg.norm(np.array(other_creature.position) - np.array(creature.position))
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_creature = other_creature

            if nearest_creature:
                dx = (nearest_creature.position[0] - creature.position[0]) / self.physics.grid_size[0]
                dy = (nearest_creature.position[1] - creature.position[1]) / self.physics.grid_size[1]
            else:
                dx, dy = 0.0, 0.0

            for block in creature.genome.blocks:
                if block[0] == 'sonar':
                    x, y = block[1], block[2]
                    io_id_dx = f"neuron_sonar_{x}_{y}_dx"
                    io_id_dy = f"neuron_sonar_{x}_{y}_dy"
                    io_id_activo = f"neuron_sonar_{x}_{y}_activo"
                    if creature.neurons.get(io_id_activo, 0) > 0:
                        creature.neurons[io_id_dx] = dx
                        creature.neurons[io_id_dy] = dy

    def log_summary(self, path='sim_log.csv'):
        import os
        headers = ['tick_count', 'population_count', 'avg_blocks_per_creature', 'avg_connections_per_creature', 'avg_energy_level', 'min_energy', 'max_energy']
        data = [
            self.tick_count,
            len(self.creatures),
            np.mean([len(c.genome.blocks) for c in self.creatures]) if self.creatures else 0,
            np.mean([len(c.connections) for c in self.creatures]) if self.creatures else 0,
            np.mean(list(self.energy.energy_levels.values())) if self.energy.energy_levels else 0,
            min(self.energy.energy_levels.values()) if self.energy.energy_levels else 0,
            max(self.energy.energy_levels.values()) if self.energy.energy_levels else 0
        ]

        with open(path, 'a', newline='') as file:
            writer = csv.writer(file)
            if not os.path.exists(path) or os.stat(path).st_size == 0:
                writer.writerow(headers)
            writer.writerow(data)
    def tick_incubadoras(self):
        import copy
        
        for creature in self.creatures:
            for block_type, x, y, params in creature.genome.blocks:
                if block_type == 'incubadora':
                    invertir_value = creature.neurons.get(f'neuron_incubadora_{x}_{y}_invertir', 0)
                    invertir_value = max(0.0, min(1.0, invertir_value))
                    
                    available_fat = self.fat_levels.get(id(creature), 0)
                    if invertir_value > 0 and available_fat > 0:
                        consumed_fat = min(invertir_value * 5, available_fat)
                        self.fat_levels[id(creature)] -= consumed_fat
                        
                        egg = self.creature_eggs.get(id(creature))
                        if not egg:
                            new_egg = {
                                'x': creature.position[0],
                                'y': creature.position[1],
                                'progress': 0.0,
                                'parent_genome': copy.deepcopy(creature.genome)
                            }
                            self.eggs.append(new_egg)
                            self.creature_eggs[id(creature)] = new_egg
                        else:
                            egg['progress'] += consumed_fat * 0.02
                        
                        creature.neurons[f'neuron_incubadora_{x}_{y}_desarrollo'] = min(1.0, egg['progress'])
                    else:
                        creature.neurons[f'neuron_incubadora_{x}_{y}_desarrollo'] = 0.0
        
        # Predación de huevos
        for egg in self.eggs[:]:
            num_nearby_mouths = sum(1 for creature in self.creatures if any(block_type == 'boca' for block_type, _, _, _ in creature.genome.blocks) and 
                                  ((creature.position[0] - egg['x']) ** 2 + (creature.position[1] - egg['y']) ** 2) ** 0.5 <= 2.0)
            if num_nearby_mouths > 0:
                egg['progress'] -= 0.1 * num_nearby_mouths
                if egg['progress'] <= 0:
                    self.eggs.remove(egg)
                    del self.creature_eggs[next(key for key, value in self.creature_eggs.items() if value == egg)]
                    for creature in self.creatures:
                        if any(block_type == 'boca' for block_type, _, _, _ in creature.genome.blocks) and \
                           ((creature.position[0] - egg['x']) ** 2 + (creature.position[1] - egg['y']) ** 2) ** 0.5 <= 2.0:
                            self.fat_levels[id(creature)] = self.fat_levels.get(id(creature), 0) + 20
        
        # Hachazón de huevos
        for egg in self.eggs[:]:
            if egg['progress'] >= 1.0:
                new_genome = self.reproduction.mutate_genome(egg['parent_genome'])
                self.spawn_creature(new_genome, (egg['x'], egg['y']))
                self.eggs.remove(egg)
                del self.creature_eggs[next(key for key, value in self.creature_eggs.items() if value == egg)]

    def apply_generators(self):
        for creature in self.creatures:
            available_fat = self.fat_levels.get(id(creature), 0)
            for block in creature.genome.blocks:
                if block[0] == 'generador':
                    consumed_fat = min(3, available_fat)
                    produced_amount = consumed_fat * (2/3)
                    self.energy.produce_energy(id(creature), produced_amount)
                    self.fat_levels[id(creature)] -= consumed_fat

    def absorb_food(self):
        for creature in self.creatures:
            for block in creature.genome.blocks:
                if block[0] == 'boca':
                    nearest_distance = float('inf')
                    nearest_pellet = None
                    for pellet in self.food_pellets:
                        distance = np.linalg.norm(np.array([pellet['x'], pellet['y']]) - np.array(creature.position))
                        if distance < nearest_distance and distance <= 2.0:
                            nearest_distance = distance
                            nearest_pellet = pellet

                    if nearest_pellet:
                        absorbed_amount = min(5, nearest_pellet['amount'])
                        self.fat_levels[id(creature)] = self.fat_levels.get(id(creature), 0) + absorbed_amount
                        nearest_pellet['amount'] -= absorbed_amount
                        if nearest_pellet['amount'] <= 0:
                            self.food_pellets.remove(nearest_pellet)

    def tick(self):
        self.tick_count += 1
        if len(self.creatures) < self.min_population:
            for _ in range(self.min_population - len(self.creatures)):
                genome = Genome.random_initial()
                self.spawn_creature(genome)

        # Actualizar sensores
        self.update_sensors()

        # Absorber comida
        self.absorb_food()

        # Aplicar generadores
        self.apply_generators()


        # Consumo de energía por mantenimiento según tipo de bloque
        for creature in self.creatures:
            cost = 0.0
            for block in creature.genome.blocks:
                block_type, x, y, params = block
                if block_type == 'banco_neuronal':
                    num_neurons = params.get('num_neurons', 0)
                    cost += 0.5 * num_neurons
                elif block_type == 'sonar':
                    io_id_activo = f"neuron_sonar_{x}_{y}_activo"
                    if creature.neurons.get(io_id_activo, 0) > 0:
                        cost += 0.3
                elif block_type == 'actuador':
                    dx = creature.neurons.get(f"neuron_actuador_{x}_{y}_dx", 0)
                    dy = creature.neurons.get(f"neuron_actuador_{x}_{y}_dy", 0)
                    magnitude = np.sqrt(dx**2 + dy**2)
                    cost += 2 * magnitude
                elif block_type == 'almacenamiento':
                    pass  # No tiene costo
                elif block_type == 'generador':
                    pass  # Costo gestionado en apply_generators
                elif block_type == 'boca':
                    pass  # No tiene costo

            self.energy.consume_energy(id(creature), cost)

        # Reproducción ahora sucede solo vía incubadora/huevos (tick_incubadoras)

        # Actualizar energía y consumo
        for creature in self.creatures:
            creature.evaluate()
            self.physics.update_positions()
            self.physics.handle_collisions()

        # Muerte por energía agotada
        for creature in self.creatures[:]:
            if self.energy.check_death(id(creature)):
                self.kill_creature(id(creature))

        if self.tick_count % 20 == 0:
            self.log_summary()

        if self.tick_count % 200 == 0 and len(self.food_pellets) < 10:
            for _ in range(10):
                self.food_pellets.append({'x': random.uniform(0, self.physics.grid_size[0]), 'y': random.uniform(0, self.physics.grid_size[1]), 'amount': random.uniform(10, 100)})

    def run(self, num_ticks):
        for _ in range(num_ticks):
            self.tick()
            print(f"Tick {_}: {len(self.creatures)} creatures")
