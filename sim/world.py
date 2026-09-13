import math

import numpy as np
from sim.creature import Creature
from sim.physics import Physics
from sim.energy import Energy
from sim.reproduction import Reproduction
import random
from sim.genome import Genome
from sim.spatial_grid import SpatialGrid
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
        self.lineage_log = []
        self.food_pellets = [{'x': random.uniform(0, self.physics.grid_size[0]), 'y': random.uniform(0, self.physics.grid_size[1]), 'amount': random.uniform(10, 100)} for _ in range(60)]
        self.eggs = []
        self.creature_eggs = {}
        self.fat_levels = {}
        self.eggs_hatched_since_log = 0
        self.artificial_refills_since_log = 0
        self.birth_tick = {}
        self.lifespan_history = []  # lista de (death_tick, lifespan_en_ticks)
        self.max_lifespan_ever = 0
        self.death_markers = []  # [{'x','y','ticks_left'}] para el indicador visual de muerte
        self.death_causes_since_log = {}
        self.generation = {}
        self.max_generation_ever = 0
        self.food_absorbed_since_log = 0.0
        self.food_distance_sum_since_log = 0.0
        self.food_distance_samples_since_log = 0

    def spawn_creature(self, genome, position=None, generation=0, parent_id=None):
        creature = Creature(genome)
        self.creatures.append(creature)
        self.physics.add_creature(creature, position)
        self.energy.add_creature(id(creature))
        self.fat_levels[id(creature)] = 0
        self.birth_tick[id(creature)] = self.tick_count
        self.generation[id(creature)] = generation
        self.max_generation_ever = max(self.max_generation_ever, generation)
        if parent_id is not None:
            self.lineage_log.append({
                'child_id': id(creature),
                'parent_id': parent_id,
                'generation': generation,
                'birth_tick': self.tick_count
            })
        return creature

    def kill_creature(self, creature_id):
        dying = next((c for c in self.creatures if id(c) == creature_id), None)
        if dying is not None:
            lifespan = self.tick_count - self.birth_tick.get(creature_id, self.tick_count)
            self.lifespan_history.append((self.tick_count, lifespan))
            self.max_lifespan_ever = max(self.max_lifespan_ever, lifespan)
            self.death_markers.append({'x': dying.position[0], 'y': dying.position[1], 'ticks_left': 15})

            had_brain = any(bt == 'banco_neuronal' for bt, _, _, _ in dying.genome.blocks)
            cause = 'starvation' if had_brain else 'starvation_brain_dead'
            self.death_causes_since_log[cause] = self.death_causes_since_log.get(cause, 0) + 1

            # El cadáver se descompone en comida, igual que un bloque destruido en combate.
            body_food = max(15, len(dying.genome.blocks) * 8)
            self.food_pellets.append({'x': dying.position[0], 'y': dying.position[1], 'amount': body_food})

        self.creatures = [c for c in self.creatures if id(c) != creature_id]
        self.physics.creatures = [c for c in self.physics.creatures if id(c) != creature_id]
        del self.energy.energy_levels[creature_id]
        self.fat_levels.pop(creature_id, None)
        # El huevo ya en curso sobrevive al padre: el recurso ya fue
        # invertido y perderlo cada vez que el padre muere (algo frecuente,
        # dada la esperanza de vida corta) hacía que casi ningún huevo
        # llegara a completarse jamás.
        self.creature_eggs.pop(creature_id, None)
        if creature_id in self.fat_levels:
            del self.fat_levels[creature_id]
        self.physics.velocities.pop(creature_id, None)
        self.birth_tick.pop(creature_id, None)
        self.generation.pop(creature_id, None)

    def update_sensors(self):
        for creature in self.creatures:
            nearest_creature, _ = self.creature_grid.nearest(
                creature.position[0], creature.position[1], exclude_obj=creature
            )

            if nearest_creature:
                dx = (nearest_creature.position[0] - creature.position[0]) / self.physics.grid_size[0]
                dy = (nearest_creature.position[1] - creature.position[1]) / self.physics.grid_size[1]
            else:
                dx, dy = 0.0, 0.0

            nearest_food, nearest_food_distance = self.food_grid.nearest(
                creature.position[0], creature.position[1]
            )

            if nearest_food:
                dx_comida = (nearest_food['x'] - creature.position[0]) / self.physics.grid_size[0]
                dy_comida = (nearest_food['y'] - creature.position[1]) / self.physics.grid_size[1]
                self.food_distance_sum_since_log += nearest_food_distance
                self.food_distance_samples_since_log += 1
            else:
                dx_comida, dy_comida = 0.0, 0.0

            for block in creature.genome.blocks:
                if block[0] == 'sonar':
                    x, y = block[1], block[2]
                    # El toggle 'activo' generaba un problema de huevo-y-gallina:
                    # nace apagado, y solo se enciende en el instante exacto en
                    # que la neurona del banco conectada dispara CON peso
                    # positivo (~50% de las veces ni eso) - el sensor quedaba
                    # ciego la enorme mayoría del tiempo desde el nacimiento,
                    # sin poder aprender nada. El sonar ahora siempre sensa;
                    # 'activo' queda como neurona de salida disponible para que
                    # la evolución la use en el futuro (ver costo fijo abajo).
                    creature.neurons[f"neuron_sonar_{x}_{y}_dx"] = dx
                    creature.neurons[f"neuron_sonar_{x}_{y}_dy"] = dy
                    creature.neurons[f"neuron_sonar_{x}_{y}_dx_comida"] = dx_comida
                    creature.neurons[f"neuron_sonar_{x}_{y}_dy_comida"] = dy_comida

    def log_summary(self, path='sim_log.csv'):
        import os
        headers = [
            'tick_count', 'population_count', 'avg_blocks_per_creature', 'avg_connections_per_creature',
            'avg_energy_level', 'min_energy', 'max_energy',
            'avg_bank_threshold', 'std_bank_threshold',
            'eggs_hatched_per_20ticks', 'artificial_refills_per_20ticks',
            'egg_count', 'food_pellet_count',
            'max_lifespan_ever', 'avg_lifespan_last_500',
            'deaths_starvation', 'deaths_starvation_brain_dead',
            'max_generation_ever', 'food_absorbed_per_20ticks', 'avg_distance_to_nearest_food',
            'pct_with_incubadora', 'pct_incubadora_wired', 'avg_sonar_activo',
        ]

        all_thresholds = []
        for c in self.creatures:
            for block_type, x, y, params in c.genome.blocks:
                if block_type == 'banco_neuronal':
                    all_thresholds.extend(params.get('thresholds', []))

        has_incubadora = [any(bt == 'incubadora' for bt, _, _, _ in c.genome.blocks) for c in self.creatures]

        def incubadora_wired(c):
            for bt, x, y, _ in c.genome.blocks:
                if bt == 'incubadora':
                    dest = f"neuron_incubadora_{x}_{y}_invertir"
                    if any(d == dest for (_, d) in c.connections.keys()):
                        return True
            return False

        incubadora_wired_flags = [incubadora_wired(c) for c in self.creatures if any(bt == 'incubadora' for bt, _, _, _ in c.genome.blocks)]

        sonar_activo_values = []
        for c in self.creatures:
            for bt, x, y, _ in c.genome.blocks:
                if bt == 'sonar':
                    sonar_activo_values.append(c.neurons.get(f"neuron_sonar_{x}_{y}_activo", 0))

        data = [
            self.tick_count,
            len(self.creatures),
            np.mean([len(c.genome.blocks) for c in self.creatures]) if self.creatures else 0,
            np.mean([len(c.connections) for c in self.creatures]) if self.creatures else 0,
            np.mean(list(self.energy.energy_levels.values())) if self.energy.energy_levels else 0,
            min(self.energy.energy_levels.values()) if self.energy.energy_levels else 0,
            max(self.energy.energy_levels.values()) if self.energy.energy_levels else 0,
            np.mean(all_thresholds) if all_thresholds else 0,
            np.std(all_thresholds) if all_thresholds else 0,
            self.eggs_hatched_since_log,
            self.artificial_refills_since_log,
            len(self.eggs),
            len(self.food_pellets),
            self.max_lifespan_ever,
            np.mean([l for (_, l) in self.lifespan_history]) if self.lifespan_history else 0,
            self.death_causes_since_log.get('starvation', 0),
            self.death_causes_since_log.get('starvation_brain_dead', 0),
            self.max_generation_ever,
            self.food_absorbed_since_log,
            (self.food_distance_sum_since_log / self.food_distance_samples_since_log) if self.food_distance_samples_since_log else -1,
            (sum(has_incubadora) / len(has_incubadora)) if has_incubadora else 0,
            (sum(incubadora_wired_flags) / len(incubadora_wired_flags)) if incubadora_wired_flags else 0,
            np.mean(sonar_activo_values) if sonar_activo_values else 0,
        ]

        with open(path, 'a', newline='') as file:
            writer = csv.writer(file)
            if not os.path.exists(path) or os.stat(path).st_size == 0:
                writer.writerow(headers)
            writer.writerow(data)

        self.eggs_hatched_since_log = 0
        self.artificial_refills_since_log = 0
        self.death_causes_since_log = {}
        self.food_absorbed_since_log = 0.0
        self.food_distance_sum_since_log = 0.0
        self.food_distance_samples_since_log = 0

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
                            egg = {
                                'x': creature.position[0],
                                'y': creature.position[1],
                                'progress': 0.0,
                                'parent_genome': copy.deepcopy(creature.genome),
                                'parent_generation': self.generation.get(id(creature), 0),
                                'parent_id': id(creature),
                            }
                            self.eggs.append(egg)
                            self.creature_eggs[id(creature)] = egg
                        # 0.5: medido que con la tasa de disparo real del banco,
                        # una criatura logra invertir en promedio ~1 vez en toda
                        # su vida. Pedir múltiples inversiones para completar un
                        # huevo (como exigía 0.02, y hasta 0.1) significaba que
                        # básicamente ningún huevo llegaba nunca a progress=1.0.
                        egg['progress'] += consumed_fat * 0.5
                        
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
                    owner_key = next((key for key, value in self.creature_eggs.items() if value == egg), None)
                    if owner_key is not None:
                        del self.creature_eggs[owner_key]
                    for creature in self.creatures:
                        if any(block_type == 'boca' for block_type, _, _, _ in creature.genome.blocks) and \
                           ((creature.position[0] - egg['x']) ** 2 + (creature.position[1] - egg['y']) ** 2) ** 0.5 <= 2.0:
                            self.fat_levels[id(creature)] = self.fat_levels.get(id(creature), 0) + 20
        
        # Hachazón de huevos
        for egg in self.eggs[:]:
            if egg['progress'] >= 1.0:
                new_genome = self.reproduction.mutate_genome(egg['parent_genome'])
                self.spawn_creature(new_genome, (egg['x'], egg['y']), generation=egg.get('parent_generation', 0) + 1, parent_id=egg.get('parent_id'))
                self.eggs.remove(egg)
                owner_key = next((key for key, value in self.creature_eggs.items() if value == egg), None)
                if owner_key is not None:
                    del self.creature_eggs[owner_key]
                self.eggs_hatched_since_log += 1

    def apply_combat(self):
        target_types = ['banco_neuronal', 'sonar', 'actuador', 'generador', 'boca', 'almacenamiento', 'incubadora', 'arma', 'casco']
        live_ids = {id(c) for c in self.creatures}

        for attacker in self.creatures:
            if id(attacker) not in live_ids:
                continue  # ya murió antes en este mismo tick (víctima de otro atacante)
            for block_type, ax, ay, _ in attacker.genome.blocks:
                if block_type == 'arma':
                    nearest_victim, _ = self.creature_grid.nearest(
                        attacker.position[0], attacker.position[1], exclude_obj=attacker, max_radius=3.0
                    )
                    if nearest_victim is not None and id(nearest_victim) not in live_ids:
                        nearest_victim = None  # murió en este mismo tick, dato de la grilla desactualizado

                    if nearest_victim:
                        objetivo_value = attacker.neurons.get(f'neuron_arma_{ax}_{ay}_objetivo', 0)
                        index = int(abs(objetivo_value) * 100) % len(target_types)
                        preferred_type = target_types[index]
                        
                        matching_blocks = [block for block in nearest_victim.genome.blocks if block[0] == preferred_type]
                        if not matching_blocks:
                            matching_blocks = nearest_victim.genome.blocks
                        
                        if matching_blocks:
                            block_to_attack = random.choice(matching_blocks)
                            bt, bx, by, _ = block_to_attack
                            
                            nearest_victim.block_hp[(bt, bx, by)] = nearest_victim.block_hp.get((bt, bx, by), 30) - 10
                            
                            if nearest_victim.block_hp[(bt, bx, by)] <= 0:
                                nearest_victim.remove_block(bt, bx, by)
                                self.food_pellets.append({'x': nearest_victim.position[0], 'y': nearest_victim.position[1], 'amount': 15})
                                # Sin bloques no hay cuerpo: quedaría como un
                                # "fantasma" sin costo de mantenimiento que
                                # nunca muere de inanición. Si el combate se
                                # llevó todo, la criatura muere ahí mismo.
                                if not nearest_victim.genome.blocks:
                                    self.kill_creature(id(nearest_victim))
                                    live_ids.discard(id(nearest_victim))
        
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
        live_pellet_ids = {id(p) for p in self.food_pellets}
        for creature in self.creatures:
            for block in creature.genome.blocks:
                if block[0] == 'boca':
                    nearest_pellet, _ = self.food_grid.nearest(
                        creature.position[0], creature.position[1], max_radius=2.0
                    )

                    # La grilla es una foto fija de este tick: otra criatura
                    # puede haber vaciado (o ya removido de food_pellets)
                    # este mismo pellet unos pasos antes en este mismo tick.
                    if nearest_pellet and nearest_pellet['amount'] > 0 and id(nearest_pellet) in live_pellet_ids:
                        absorbed_amount = min(5, nearest_pellet['amount'])
                        self.fat_levels[id(creature)] = self.fat_levels.get(id(creature), 0) + absorbed_amount
                        nearest_pellet['amount'] -= absorbed_amount
                        self.food_absorbed_since_log += absorbed_amount
                        if nearest_pellet['amount'] <= 0:
                            self.food_pellets.remove(nearest_pellet)
                            live_pellet_ids.discard(id(nearest_pellet))

    def tick(self):
        self.tick_count += 1
        if len(self.creatures) < self.min_population:
            for _ in range(self.min_population - len(self.creatures)):
                genome = Genome.random_initial()
                self.spawn_creature(genome)
                self.artificial_refills_since_log += 1

        # Reconstruir índices espaciales una vez por tick, reusados por
        # update_sensors/absorb_food/apply_combat en vez de que cada uno
        # recorra todas las criaturas/pellets por separado (O(n^2)).
        self.creature_grid = SpatialGrid(cell_size=10.0)
        self.creature_grid.build((c.position[0], c.position[1], c) for c in self.creatures)
        self.food_grid = SpatialGrid(cell_size=10.0)
        self.food_grid.build((p['x'], p['y'], p) for p in self.food_pellets)

        # Actualizar sensores
        self.update_sensors()

        # Aplicar combate
        self.apply_combat()

        # Absorber comida
        self.absorb_food()

        # Aplicar generadores
        self.apply_generators()


        # Consumo de energía por mantenimiento según tipo de bloque
        for creature in self.creatures:
            cost = 0.0
            for block in creature.genome.blocks:
                block_type, x, y, params = block
                # Mantenimiento tisular mínimo: sin esto, tener el cuerpo sin
                # cerebro (banco_neuronal destruido) salía gratis, y de hecho
                # las criaturas "cerebro-muertas" vivían 4x más en promedio
                # que las que conservan su cerebro - el sistema premiaba la
                # ausencia de cognición. Todo bloque cuesta algo por existir.
                cost += 0.1
                if block_type == 'banco_neuronal':
                    num_neurons = params.get('num_neurons', 0)
                    cost += 0.5 * num_neurons
                elif block_type == 'sonar':
                    cost += 0.15  # fijo ahora que el sonar siempre está encendido
                elif block_type == 'actuador':
                    impulso = creature.neurons.get(f"neuron_actuador_{x}_{y}_impulso", 0)
                    cost += 2 * max(0.0, min(1.0, impulso))
                elif block_type == 'almacenamiento':
                    pass  # No tiene costo
                elif block_type == 'generador':
                    pass  # Costo gestionado en apply_generators
                elif block_type == 'boca':
                    pass  # No tiene costo

            self.energy.consume_energy(id(creature), cost)

        # Reproducción ahora sucede solo vía incubadora/huevos
        self.tick_incubadoras()

        # Actualizar energía y consumo
        for creature in self.creatures:
            creature.evaluate()
        self.physics.update_positions()
        self.physics.handle_collisions()

        # Muerte por energía agotada
        for creature in self.creatures[:]:
            if self.energy.check_death(id(creature)):
                self.kill_creature(id(creature))

        # Decaimiento de los marcadores visuales de muerte
        for marker in self.death_markers[:]:
            marker['ticks_left'] -= 1
            if marker['ticks_left'] <= 0:
                self.death_markers.remove(marker)

        # Recorte del historial de vidas: solo nos interesa la ventana reciente
        cutoff = self.tick_count - 500
        self.lifespan_history = [(t, l) for (t, l) in self.lifespan_history if t >= cutoff]

        if self.tick_count % 20 == 0:
            self.log_summary()

        if self.tick_count % 50 == 0 and len(self.food_pellets) < 40:
            for _ in range(15):
                self.food_pellets.append({'x': random.uniform(0, self.physics.grid_size[0]), 'y': random.uniform(0, self.physics.grid_size[1]), 'amount': random.uniform(10, 100)})

    def export_lineage_csv(self, path='lineage.csv'):
        import csv

        headers = ['child_id', 'parent_id', 'generation', 'birth_tick']
        with open(path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            for entry in self.lineage_log:
                writer.writerow([entry['child_id'], entry['parent_id'], entry['generation'], entry['birth_tick']])

    def run(self, num_ticks):
        for _ in range(num_ticks):
            self.tick()
            print(f"Tick {_}: {len(self.creatures)} creatures")
