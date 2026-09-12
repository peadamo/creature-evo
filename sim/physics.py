import numpy as np

class Physics:
    def __init__(self, grid_size=(100, 100)):
        self.grid_size = grid_size
        self.creatures = []

    def add_creature(self, creature):
        import random
        x = random.uniform(0, self.grid_size[0])
        y = random.uniform(0, self.grid_size[1])
        creature.position = (x, y)  # Asignar posición inicial aleatoria dentro de los límites del grid
        self.creatures.append(creature)

    def update_positions(self):
        for creature in self.creatures:
            x, y = creature.position
            actuator_outputs = creature.get_actuator_outputs()

            if len(actuator_outputs) == 0:
                dx, dy = 0, 0
            elif len(actuator_outputs) == 1:
                dx = actuator_outputs[0] * 0.5
                dy = actuator_outputs[0] * 0.5
            else:
                avg_output = sum(actuator_outputs) / len(actuator_outputs)
                dx = avg_output * 0.5
                dy = avg_output * 0.5

            new_x = max(0, min(self.grid_size[0], x + dx))  # Asegurar que la nueva posición esté dentro de los límites del grid
            new_y = max(0, min(self.grid_size[1], y + dy))

            creature.position = (new_x, new_y)  # Actualizar posición de la criatura

    def handle_collisions(self):
        # Manejar colisiones en la grilla discreta
        pass

    def apply_damage(self, damage, x, y):
        # Aplicar daño local a bloques
        pass
