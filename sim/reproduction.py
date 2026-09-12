import random

class Reproduction:
    def __init__(self):
        self.innovation_id = 0

    def get_innovation_id(self):
        self.innovation_id += 1
        return self.innovation_id

    def mutate_genome(self, genome):
        # Mutaciones posibles: agregar/quitar/mover un bloque, agregar/quitar/mutar una conexión
        pass

    def crossover(self, parent1, parent2):
        # Cruce por innovation id
        pass

    def reproduce(self, parent, energy_threshold):
        if parent.energy >= energy_threshold:
            child_genome = self.mutate_genome(parent.genome)
            return Creature(child_genome)
        else:
            return None
