import random

import numpy as np

class Creature:
    def __init__(self, genome):
        self.genome = genome
        self.neurons = {}
        self.connections = {}

        # Crear neuronas de borde y libres
        for block in self.genome.blocks:
            block_type, x, y, params = block
            if block_type == 'banco_neuronal':
                num_neurons = params.get('num_neurons', 0)
                for i in range(num_neurons):
                    neuron_id = f"neuron_{block_type}_{x}_{y}_{i}"
                    # Bias interno: sin esto todas las neuronas parten en 0 y
                    # nunca hay señal, sin importar los pesos evolucionados.
                    self.neurons[neuron_id] = random.uniform(-1.0, 1.0)
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
        # Evaluar el grafo neuronal (simplificado)
        for (origin, dest), weight in self.connections.items():
            self.neurons[dest] += self.neurons[origin] * weight
            self.neurons[dest] = np.tanh(self.neurons[dest])

    def get_actuator_outputs(self):
        actuator_outputs = [value for key, value in self.neurons.items() if 'neuron_actuador' in key]
        return actuator_outputs
