class Genome:
    def __init__(self):
        self.blocks = []  # Lista de bloques (tipo, relative x,y, params)
        self.connections = []  # Lista de conexiones neuronales (origin, dest, weight, enabled)

    def add_block(self, block_type, x, y, params):
        self.blocks.append((block_type, x, y, params))

    def add_connection(self, origin, dest, weight, enabled=True):
        self.connections.append((origin, dest, weight, enabled))
