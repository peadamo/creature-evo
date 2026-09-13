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
            else:
                for param in params.keys():
                    if block_type == 'actuador' and param == 'direccion':
                        continue  # geometría fija del bloque, no es una señal
                    neuron_id = f"neuron_{block_type}_{x}_{y}_{param}"
                    self.neurons[neuron_id] = 0.0

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
            self.potentials[neuron_id] *= 0.8
            if self.potentials[neuron_id] > threshold:
                self.neurons[neuron_id] = 1.0
                self.potentials[neuron_id] = 0.0
            else:
                self.neurons[neuron_id] = 0.0

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
        
        # Eliminar conexiones asociadas al bloque
        self.connections = [conn for conn in self.connections if not (conn[0].startswith(prefix) or conn[1].startswith(prefix))]

    def get_actuator_outputs(self):
        actuator_outputs = [value for key, value in self.neurons.items() if 'neuron_actuador' in key]
        return actuator_outputs
