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

        for pellet in getattr(world, 'food_pellets', []):
            px = int(pellet['x'] * scale_x)
            py = int(pellet['y'] * scale_y)
            radius = max(2, min(6, int(pellet['amount'] / 20)))
            pygame.draw.circle(self.screen, (0, 200, 0), (px, py), radius)

        for creature in world.creatures:
            x, y = creature.position
            screen_x = int(x * scale_x)
            screen_y = int(y * scale_y)
            num_blocks = len(creature.genome.blocks)

            # Convertir hue a RGB para colores más visibles
            import colorsys
            hue = (num_blocks * 30) % 360 / 360.0
            saturation = 1.0
            value = 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
            color = (int(r * 255), int(g * 255), int(b * 255))

            pygame.draw.circle(self.screen, color, (screen_x, screen_y), 5)  # Dibujar criatura como un círculo pequeño

        pygame.display.flip()
