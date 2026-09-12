import random

class Genome:
    def __init__(self):
        self.blocks = []  # Lista de bloques (tipo, relative x,y, params)
        self.connections = []  # Lista de conexiones neuronales (origin, dest, weight, enabled)

    @classmethod
    def random_initial(cls):
        genome = cls()
        genome.add_block('banco_neuronal', 0, 0, {'num_neurons': 5})
        for _ in range(random.randint(1, 3)):
            block_type = random.choice(['sensor', 'actuador'])
            x, y = random.randint(0, 10), random.randint(0, 10)
            params = {}
            genome.add_block(block_type, x, y, params)
        return genome

    def add_block(self, block_type, x, y, params):
        self.blocks.append((block_type, x, y, params))

    def add_connection(self, origin, dest, weight, enabled=True):
        self.connections.append((origin, dest, weight, enabled))
