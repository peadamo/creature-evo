import copy
import random

from sim.genome import Genome

class Reproduction:
    def __init__(self):
        self.innovation_id = 0

    def get_innovation_id(self):
        self.innovation_id += 1
        return self.innovation_id

    def mutate_genome(self, genome):
        new_genome = copy.deepcopy(genome)
        
        # Probabilidades de mutación
        mutation_probabilities = {
            'add_block': 0.2,
            'remove_block': 0.1,
            'mutate_connection': 0.3,
            'add_connection': 0.4
        }
        
        if random.random() < mutation_probabilities['add_block']:
            block_type = random.choice(['banco_neuronal', 'sensor', 'actuador'])
            x, y = random.randint(0, 10), random.randint(0, 10)
            params = {'num_neurons': random.randint(1, 5)}
            new_genome.add_block(block_type, x, y, params)
        
        if random.random() < mutation_probabilities['remove_block']:
            non_core_blocks = [block for block in new_genome.blocks if block[0] != 'banco_neuronal']
            if non_core_blocks:
                block_to_remove = random.choice(non_core_blocks)
                new_genome.blocks.remove(block_to_remove)

                valid_ids = set()
                for block_type, x, y, params in new_genome.blocks:
                    if block_type == 'banco_neuronal':
                        for i in range(params.get('num_neurons', 0)):
                            valid_ids.add(f"neuron_{block_type}_{x}_{y}_{i}")
                    else:
                        for param_key in params.keys():
                            valid_ids.add(f"neuron_{block_type}_{x}_{y}_{param_key}")
                new_genome.connections = [
                    c for c in new_genome.connections if c[0] in valid_ids and c[1] in valid_ids
                ]

        if random.random() < mutation_probabilities['mutate_connection']:
            if new_genome.connections:
                connection_to_mutate = random.choice(new_genome.connections)
                origin, dest, weight, enabled = connection_to_mutate
                new_weight = weight + random.uniform(-0.1, 0.1)
                index = new_genome.connections.index(connection_to_mutate)
                new_genome.connections[index] = (origin, dest, new_weight, enabled)
        
        if random.random() < mutation_probabilities['add_connection'] and len(new_genome.blocks) >= 2:
            origin_block, dest_block = random.sample(new_genome.blocks, 2)
            
            # Construir IDs de neuronas para los bloques seleccionados
            origin_id = None
            dest_id = None
            
            for block in new_genome.blocks:
                block_type, x, y, params = block
                if block == origin_block:
                    if block_type == 'banco_neuronal':
                        num_neurons = params.get('num_neurons', 0)
                        i = random.randint(0, num_neurons - 1)
                        origin_id = f"neuron_{block_type}_{x}_{y}_{i}"
                    else:
                        param_key = random.choice(list(params.keys()))
                        origin_id = f"neuron_{block_type}_{x}_{y}_{param_key}"
                if block == dest_block:
                    if block_type == 'banco_neuronal':
                        num_neurons = params.get('num_neurons', 0)
                        i = random.randint(0, num_neurons - 1)
                        dest_id = f"neuron_{block_type}_{x}_{y}_{i}"
                    else:
                        param_key = random.choice(list(params.keys()))
                        dest_id = f"neuron_{block_type}_{x}_{y}_{param_key}"
            
            if origin_id and dest_id:
                weight = random.uniform(-1.0, 1.0)
                new_genome.add_connection(origin_id, dest_id, weight)
        
        return new_genome

    def crossover(self, parent1, parent2):
        new_genome = Genome()
        
        # Combinar conexiones con matching innovation ids
        connections_dict = {}
        for connection in parent1.connections:
            innovation_id = (connection[0], connection[1])
            connections_dict[innovation_id] = [connection]
        for connection in parent2.connections:
            innovation_id = (connection[0], connection[1])
            if innovation_id in connections_dict:
                connections_dict[innovation_id].append(connection)
        
        for innovation_id, connections in connections_dict.items():
            if len(connections) == 2:
                chosen_connection = random.choice(connections)
            else:
                chosen_connection = connections[0]
            new_genome.add_connection(*chosen_connection)
        
        # Combinar bloques (puedes ajustar esto según tus necesidades)
        all_blocks = parent1.blocks + parent2.blocks
        unique_blocks_dict = {}
        for block in all_blocks:
            block_type, x, y, _ = block
            key = (block_type, x, y)
            if key not in unique_blocks_dict:
                unique_blocks_dict[key] = block
        
        unique_blocks = list(unique_blocks_dict.values())
        for block in unique_blocks:
            new_genome.add_block(*block)
        
        return new_genome

    def reproduce(self, parent_genome, current_energy, energy_threshold):
        if current_energy < energy_threshold:
            return None
        mutated_child_genome = self.mutate_genome(parent_genome)
        return mutated_child_genome
