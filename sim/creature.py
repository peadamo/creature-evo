import random

import numpy as np

class Creature:
    def __init__(self, genome):
        self.genome = genome
        self.neurons = {}
        self.connections = {}
        self.potentials = {}
        self.neuron_thresholds = {}

        # Crear neuronas de borde y libres
        for block in self.genome.blocks:
            block_type, x, y, params = block
            if block_type == 'banco_neuronal':
                num_neurons = params.get('num_neurons', 0)
                for i in range(num_neurons):
                    neuron_id = f"neuron_{block_type}_{x}_{y}_{i}"
                    # Bias interno: sin esto todas las neuronas parten en 0 y
                    # nunca hay señal, sin importar los pesos evolucionados.
                    self.neurons[neuron_id] = 0.0
                    self.potentials[neuron_id] = 0.0
                    self.neuron_thresholds[neuron_id] = params['thresholds'][i]
            else:
                for param in params.keys():
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

    def get_actuator_outputs(self):
        actuator_outputs = [value for key, value in self.neurons.items() if 'neuron_actuador' in key]
        return actuator_outputs
