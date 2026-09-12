import random

class Genome:
    def __init__(self):
        self.blocks = []  # Lista de bloques (tipo, relative x,y, params)
        self.connections = []  # Lista de conexiones neuronales (origin, dest, weight, enabled)

    @classmethod
    def random_initial(cls):
        genome = cls()
        bank_x, bank_y = 0, 0
        num_bank_neurons = 5
        thresholds = [random.uniform(0.3, 1.5) for _ in range(num_bank_neurons)]
        genome.add_block('banco_neuronal', bank_x, bank_y, {'num_neurons': num_bank_neurons, 'thresholds': thresholds})

        io_blocks = []
        for _ in range(random.randint(1, 3)):
            block_type = random.choice(['sonar', 'actuador', 'generador', 'boca', 'almacenamiento', 'incubadora'])
            x, y = random.randint(0, 10), random.randint(0, 10)
            params = {}
            if block_type == 'sonar':
                params = {'dx': 0.0, 'dy': 0.0, 'activo': 0.0}
            elif block_type == 'actuador':
                params = {'direccion': random.uniform(0, 6.283), 'impulso': 0.0}
            elif block_type in ['boca', 'almacenamiento']:
                params = {}
            elif block_type == 'incubadora':
                params = {'desarrollo': 0.0, 'invertir': 0.0}
            elif block_type == 'generador':
                params = {'output': 0.0}
            genome.add_block(block_type, x, y, params)
            io_blocks.append((block_type, x, y))

        # Conectar cada bloque sensor/actuador/generador con una neurona aleatoria del banco,
        # para que haya señal fluyendo desde el arranque.
        for block_type, x, y in io_blocks:
            if block_type in ('boca', 'almacenamiento', 'incubadora'):
                continue  # sin neuronas propias, nada que conectar
            if block_type == 'generador':
                io_id = f"neuron_generador_{x}_{y}_output"
                bank_neuron_id = f"neuron_banco_neuronal_{bank_x}_{bank_y}_{random.randint(0, num_bank_neurons - 1)}"
                weight = random.uniform(-1.0, 1.0)
                genome.add_connection(io_id, bank_neuron_id, weight)
            else:
                io_id_dx = f"neuron_{block_type}_{x}_{y}_dx"
                io_id_dy = f"neuron_{block_type}_{x}_{y}_dy"
                bank_neuron_id = f"neuron_banco_neuronal_{bank_x}_{bank_y}_{random.randint(0, num_bank_neurons - 1)}"
                weight = random.uniform(-1.0, 1.0)
                if block_type == 'sonar':
                    genome.add_connection(io_id_dx, bank_neuron_id, weight)
                    genome.add_connection(io_id_dy, bank_neuron_id, weight)
                    io_id_activo = f"neuron_sonar_{x}_{y}_activo"
                    genome.add_connection(bank_neuron_id, io_id_activo, weight)
                else:
                    genome.add_connection(bank_neuron_id, io_id_dx, weight)
                    genome.add_connection(bank_neuron_id, io_id_dy, weight)

        return genome

    def add_block(self, block_type, x, y, params):
        self.blocks.append((block_type, x, y, params))

    def add_connection(self, origin, dest, weight, enabled=True):
        self.connections.append((origin, dest, weight, enabled))
