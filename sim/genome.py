import random

class Genome:
    def __init__(self):
        self.blocks = []  # Lista de bloques (tipo, relative x,y, params)
        self.connections = []  # Lista de conexiones neuronales (origin, dest, weight, enabled)
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    @classmethod
    def random_initial(cls):
        genome = cls()
        bank_x, bank_y = 0, 0
        num_bank_neurons = 5
        thresholds = [random.uniform(0.1, 0.6) for _ in range(num_bank_neurons)]
        genome.add_block('banco_neuronal', bank_x, bank_y, {'num_neurons': num_bank_neurons, 'thresholds': thresholds})

        def make_params(block_type):
            if block_type == 'sonar':
                return {'dx': 0.0, 'dy': 0.0, 'dx_comida': 0.0, 'dy_comida': 0.0, 'activo': 0.0}
            elif block_type == 'actuador':
                return {'direccion': random.uniform(0, 6.283), 'impulso': 0.0}
            elif block_type in ('boca', 'almacenamiento', 'casco'):
                return {}
            elif block_type == 'incubadora':
                return {'desarrollo': 0.0, 'invertir': 0.0}
            elif block_type == 'arma':
                return {'objetivo': 0.0}
            elif block_type == 'generador':
                return {'output': 0.0}
            return {}

        io_blocks = []

        # Sustento garantizado: sin esto la mayoría de las criaturas nace sin
        # forma de conseguir energía ni de percibir dónde está la comida, y
        # muere de inanición antes de que la evolución tenga chance de actuar.
        for guaranteed_type in ('boca', 'generador', 'actuador', 'sonar'):
            x, y = random.randint(0, 10), random.randint(0, 10)
            genome.add_block(guaranteed_type, x, y, make_params(guaranteed_type))
            io_blocks.append((guaranteed_type, x, y))

        for _ in range(random.randint(1, 3)):
            block_type = random.choice(['sonar', 'actuador', 'generador', 'boca', 'almacenamiento', 'incubadora', 'arma', 'casco'])
            x, y = random.randint(0, 10), random.randint(0, 10)
            genome.add_block(block_type, x, y, make_params(block_type))
            io_blocks.append((block_type, x, y))

        # Conectar cada bloque sensor/actuador/generador con una neurona aleatoria del banco,
        # para que haya señal fluyendo desde el arranque.
        for block_type, x, y in io_blocks:
            if block_type in ('boca', 'casco'):
                continue  # sin neuronas propias, nada que conectar
            elif block_type == 'almacenamiento':
                genome.add_connection(f'neuron_almacenamiento_{x}_{y}_reserva', bank_neuron(), random.uniform(-1.0, 1.0))

            def bank_neuron():
                return f"neuron_banco_neuronal_{bank_x}_{bank_y}_{random.randint(0, num_bank_neurons - 1)}"

            if block_type == 'generador':
                genome.add_connection(f"neuron_generador_{x}_{y}_output", bank_neuron(), random.uniform(-1.0, 1.0))
            elif block_type == 'sonar':
                genome.add_connection(f"neuron_sonar_{x}_{y}_dx", bank_neuron(), random.uniform(-1.0, 1.0))
                genome.add_connection(f"neuron_sonar_{x}_{y}_dy", bank_neuron(), random.uniform(-1.0, 1.0))
                genome.add_connection(f"neuron_sonar_{x}_{y}_dx_comida", bank_neuron(), random.uniform(-1.0, 1.0))
                genome.add_connection(f"neuron_sonar_{x}_{y}_dy_comida", bank_neuron(), random.uniform(-1.0, 1.0))
                genome.add_connection(bank_neuron(), f"neuron_sonar_{x}_{y}_activo", random.uniform(-1.0, 1.0))
            elif block_type == 'actuador':
                genome.add_connection(bank_neuron(), f"neuron_actuador_{x}_{y}_impulso", random.uniform(-1.0, 1.0))
            elif block_type == 'incubadora':
                genome.add_connection(bank_neuron(), f"neuron_incubadora_{x}_{y}_invertir", random.uniform(-1.0, 1.0))
            elif block_type == 'arma':
                genome.add_connection(bank_neuron(), f'neuron_arma_{x}_{y}_objetivo', random.uniform(-1.0, 1.0))

        return genome

    def add_block(self, block_type, x, y, params):
        self.blocks.append((block_type, x, y, params))

    def add_connection(self, origin, dest, weight, enabled=True):
        self.connections.append((origin, dest, weight, enabled))

    def to_dict(self):
        return {
            'blocks': [[block_type, x, y, params] for block_type, x, y, params in self.blocks],
            'connections': [[origin, dest, weight, enabled] for origin, dest, weight, enabled in self.connections],
            'color': list(self.color)
        }

    @classmethod
    def from_dict(cls, d):
        genome = cls()
        genome.blocks = [(block_type, x, y, params) for block_type, x, y, params in d['blocks']]
        genome.connections = [(origin, dest, weight, enabled) for origin, dest, weight, enabled in d['connections']]
        genome.color = tuple(d['color'])
        return genome
