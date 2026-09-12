import pygame

class Renderer:
    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Creature-Evo Simulation")

    def draw(self, world):
        self.screen.fill((0, 0, 0))  # Limpiar la pantalla con negro

        grid_w, grid_h = world.physics.grid_size
        scale_x = self.width / grid_w
        scale_y = self.height / grid_h

        for creature in world.creatures:
            x, y = creature.position
            screen_x = int(x * scale_x)
            screen_y = int(y * scale_y)
            num_blocks = len(creature.genome.blocks)
            color_intensity = min(255, int(num_blocks * 10))  # Ajustar intensidad del color basado en el número de bloques
            color = (color_intensity, color_intensity, color_intensity)  # Color gris más brillante con más bloques

            pygame.draw.circle(self.screen, color, (screen_x, screen_y), 5)  # Dibujar criatura como un círculo pequeño

        pygame.display.flip()
