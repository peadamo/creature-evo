import math
import numpy as np

class Physics:
    def __init__(self, grid_size=(100, 100)):
        self.grid_size = grid_size
        self.creatures = []
        self.velocities = {}

    def temperature_at(self, x, y):
        """Returns the temperature at a given position (x, y) in the grid."""
        temp = 1.0 + 2.0 * math.exp(-((x-25)**2+(y-25)**2)/500) + 2.0 * math.exp(-((x-75)**2+(y-75)**2)/500)
        return temp
        self.grid_size = grid_size
        self.creatures = []
        self.velocities = {}

    def add_creature(self, creature, position=None):
        import random
        if position is None:
            x = random.uniform(0, self.grid_size[0])
            y = random.uniform(0, self.grid_size[1])
        else:
            x, y = position
        creature.position = (x, y)  # Asignar posición inicial aleatoria dentro de los límites del grid
        self.creatures.append(creature)
        self.velocities[id(creature)] = (0.0, 0.0)

    def update_positions(self):
        grid_w, grid_h = self.grid_size
        for creature in self.creatures:
            x, y = creature.position
            thrust_x, thrust_y = 0.0, 0.0

            for block_type, bx, by, params in creature.genome.blocks:
                if block_type != 'actuador':
                    continue
                impulso = creature.neurons.get(f"neuron_actuador_{bx}_{by}_impulso", 0.0)
                impulso = max(0.0, min(1.0, impulso))
                direccion = params.get('direccion', 0.0)
                thrust_x += impulso * math.cos(direccion) * 1.2
                thrust_y += impulso * math.sin(direccion) * 1.2

            vx, vy = self.velocities.get(id(creature), (0.0, 0.0))
            vx = (vx + thrust_x) * 0.85
            vy = (vy + thrust_y) * 0.85

            new_x = x + vx
            new_y = y + vy

            if new_x < 0 or new_x > grid_w:
                vx = 0.0
            if new_y < 0 or new_y > grid_h:
                vy = 0.0

            new_x = max(0, min(grid_w, new_x))
            new_y = max(0, min(grid_h, new_y))

            self.velocities[id(creature)] = (vx, vy)
            creature.position = (new_x, new_y)  # Actualizar posición de la criatura

    def handle_collisions(self):
        # Manejar colisiones en la grilla discreta
        pass

    def apply_damage(self, damage, x, y):
        # Aplicar daño local a bloques
        pass
