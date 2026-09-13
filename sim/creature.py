import random

import numpy as np

class Creature:
    def __init__(self, genome):
        self.genome = genome
        self.neurons = {}
        self.connections = {}
        self.potentials = {}
        self.neuron_thresholds = {}
        self.block_hp = {}  # Agregar diccionario para HP de bloques

        # Crear neuronas de borde y libres
        for block in self.genome.blocks:
            block_type, x, y, params = block

            if block_type == 'banco_neuronal':
                self.block_hp[(block_type, x, y)] = 10
            elif block_type == 'casco':
                self.block_hp[(block_type, x, y)] = 50
            else:
                self.block_hp[(block_type, x, y)] = 30

            if block_type == 'banco_neuronal':
                num_neurons = params.get('num_neurons', 0)
                for i in range(num_neurons):
                    neuron_id = f"neuron_{block_type}_{x}_{y}_{i}"
                    self.neurons[neuron_id] = 0.0
                    # Potencial inicial aleatorio: si todas arrancan en 0.0 exacto,
                    # todas las criaturas quedan en fase y disparan sincronizadas
                    # (falso patrón, no algo que emergió de la evolución).
                    threshold = params['thresholds'][i]
                    self.potentials[neuron_id] = random.uniform(0.0, threshold)
                    self.neuron_thresholds[neuron_id] = threshold
            # Neurona hp_level para todos los bloques (input: lectura del nivel de vida)
            hp_neuron_id = f"neuron_{block_type}_{x}_{y}_hp_level"
            self.neurons[hp_neuron_id] = 0.0

            if block_type != 'banco_neuronal':
                for param in params.keys():
                    neuron_id = f"neuron_{block_type}_{x}_{y}_{param}"
                    self.neurons[neuron_id] = 0.0

                # Neurona de dirección para actuadores (output, controla ángulo)
                if block_type == 'actuador':
                    direccion_neuron = f"neuron_{block_type}_{x}_{y}_direccion"
                    self.neurons[direccion_neuron] = 0.0

                # Sonar: sensores de comida y huevos
                if block_type == 'sonar':
                    self.neurons[f"neuron_sonar_{x}_{y}_dx"] = 0.0
                    self.neurons[f"neuron_sonar_{x}_{y}_dy"] = 0.0
                    self.neurons[f"neuron_sonar_{x}_{y}_dx_comida"] = 0.0
                    self.neurons[f"neuron_sonar_{x}_{y}_dy_comida"] = 0.0
                    self.neurons[f"neuron_sonar_{x}_{y}_dx_huevo"] = 0.0
                    self.neurons[f"neuron_sonar_{x}_{y}_dy_huevo"] = 0.0
                    self.neurons[f"neuron_sonar_{x}_{y}_activo"] = 0.0

                # Radar de parentesco: sensores de huevos
                if block_type == 'radar_parentesco':
                    self.neurons[f"neuron_radar_parentesco_{x}_{y}_dx"] = 0.0
                    self.neurons[f"neuron_radar_parentesco_{x}_{y}_dy"] = 0.0
                    self.neurons[f"neuron_radar_parentesco_{x}_{y}_parentesco"] = 0.0
                    self.neurons[f"neuron_radar_parentesco_{x}_{y}_activo"] = 0.0

                # Neurona dormir: output que desactiva el bloque si > 0.5
                dormir_neuron_id = f"neuron_{block_type}_{x}_{y}_dormir"
                self.neurons[dormir_neuron_id] = 0.0

        # Crear conexiones
        for connection in self.genome.connections:
            origin, dest, weight, enabled = connection
            if enabled:
                self.connections[(origin, dest)] = weight

    def evaluate(self):
        # Pass A - Accumulate
        edge_inputs = {}
        for (origin, dest), weight in self.connections.items():
            if dest in self.potentials:
                self.potentials[dest] += self.neurons[origin] * weight
            else:
                edge_inputs[dest] = edge_inputs.get(dest, 0.0) + self.neurons[origin] * weight
        for dest, value in edge_inputs.items():
            self.neurons[dest] = value

        # Pass B - Fire and Leak
        for neuron_id, threshold in self.neuron_thresholds.items():
            # Fuga baja (retiene 95%): con 0.8 el potencial estacionario ante
            # un estímulo típico (distancias normalizadas ~0.05) queda en
            # ~0.125, por debajo de casi todo el rango de umbrales - las
            # neuronas del banco casi nunca disparaban en ningún lado del
            # sistema. Con 0.95 el estacionario sube a ~0.46, dentro del
            # rango bajo de umbrales.
            self.potentials[neuron_id] *= 0.95
            if self.potentials[neuron_id] > threshold:
                self.neurons[neuron_id] = 1.0
                self.potentials[neuron_id] = 0.0
            else:
                self.neurons[neuron_id] = 0.0

        # Pass C - Apply connections to edge outputs (incubadora, sonar control, etc)
        # Las neuronas de salida como invertir necesitan ser propagadas DESPUES de que el banco dispara
        edge_outputs = {}
        for (origin, dest), weight in self.connections.items():
            if dest not in self.potentials:  # Es una neurona de borde/salida
                edge_outputs[dest] = edge_outputs.get(dest, 0.0) + self.neurons[origin] * weight
        for dest, value in edge_outputs.items():
            if dest in self.neurons:
                self.neurons[dest] = value

        # Pass D - Update sensory inputs (hp_level para cada bloque)
        for block_type, x, y in self.block_hp.keys():
            hp_neuron_id = f"neuron_{block_type}_{x}_{y}_hp_level"
            max_hp = self.block_hp[(block_type, x, y)]
            current_hp = self.block_hp.get((block_type, x, y), max_hp)
            if hp_neuron_id in self.neurons:
                self.neurons[hp_neuron_id] = min(1.0, current_hp / max_hp) if max_hp > 0 else 0.0

    def remove_block(self, block_type, x, y):
        # Eliminar el bloque del genoma
        self.genome.blocks = [block for block in self.genome.blocks if not (block[0] == block_type and block[1] == x and block[2] == y)]
        
        # Eliminar HP del bloque
        self.block_hp.pop((block_type, x, y), None)
        
        # Eliminar neuronas asociadas al bloque
        prefix = f'neuron_{block_type}_{x}_{y}_'
        matching_neurons = [key for key in self.neurons if key.startswith(prefix)]
        for neuron_id in matching_neurons:
            del self.neurons[neuron_id]
            self.potentials.pop(neuron_id, None)
            self.neuron_thresholds.pop(neuron_id, None)
        
        # Eliminar conexiones asociadas al bloque - tanto del diccionario en
        # vivo (self.connections, usado por evaluate() de ESTA instancia)
        # como de la lista genética (self.genome.connections). Si solo se
        # limpia self.connections, un hijo nacido de este genoma más
        # adelante (self.genome.connections viaja en el huevo vía
        # copy.deepcopy) hereda una conexión colgante hacia una neurona que
        # ya no existe, y crashea al construirse.
        self.connections = {
            (origin, dest): weight
            for (origin, dest), weight in self.connections.items()
            if not (origin.startswith(prefix) or dest.startswith(prefix))
        }
        self.genome.connections = [
            (origin, dest, weight, enabled)
            for (origin, dest, weight, enabled) in self.genome.connections
            if not (origin.startswith(prefix) or dest.startswith(prefix))
        ]

    def get_actuator_outputs(self):
        actuator_outputs = [value for key, value in self.neurons.items() if 'neuron_actuador' in key]
        return actuator_outputs

    def mutate_somatic(self, tick_count, mutation_rate=0.05, mutation_field=None, world_position=(0, 0)):
        """Aplicar mutaciones somáticas lentas durante la vida del individuo"""
        # Si está en campo de mutación, duplicar tasa
        if mutation_field and world_position:
            dist = ((mutation_field['x'] - world_position[0])**2 + (mutation_field['y'] - world_position[1])**2)**0.5
            if dist < mutation_field['radius']:
                mutation_rate *= 2.0

        # Cada tick: pequeña mutación de pesos
        for connection in self.genome.connections:
            if random.random() < mutation_rate:
                origin, dest, weight, enabled = connection
                # Cambiar peso ±5%
                delta = random.uniform(-0.05, 0.05)
                new_weight = max(-1.0, min(1.0, weight + delta))
                idx = self.genome.connections.index(connection)
                self.genome.connections[idx] = (origin, dest, new_weight, enabled)
                # Actualizar en self.connections si existe
                if (origin, dest) in self.connections:
                    self.connections[(origin, dest)] = new_weight

        # Cada 100 ticks: agregar/borrar conexión
        if tick_count % 100 == 0 and len(self.genome.connections) > 5:
            if random.random() < 0.5 and len(self.genome.connections) > 2:
                # Borrar conexión
                idx = random.randint(0, len(self.genome.connections) - 1)
                removed = self.genome.connections.pop(idx)
                self.connections.pop((removed[0], removed[1]), None)
            else:
                # Agregar conexión aleatoria
                if len(self.genome.blocks) > 0:
                    pass  # Más complejo, saltamos por ahora

        # Cada 500 ticks: agregar bloque (muy raro)
        if tick_count % 500 == 0 and random.random() < 0.1:
            pass  # Implementar después si es necesario
