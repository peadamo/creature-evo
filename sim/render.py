import pygame
import pygame.font

class Renderer:
    def __init__(self, width=800, height=600):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Creature-Evo Simulation")
        self.font = pygame.font.SysFont(None, 20)

    def draw(self, world, ui_panel=None, fps=0):
        self.screen.fill((0, 0, 0))  # Limpiar la pantalla con negro

        grid_w, grid_h = world.physics.grid_size
        scale_x = self.width / grid_w
        scale_y = self.height / grid_h

        for pellet in getattr(world, 'food_pellets', []):
            px = int(pellet['x'] * scale_x)
            py = int(pellet['y'] * scale_y)
            radius = max(2, min(6, int(pellet['amount'] / 20)))
            pygame.draw.circle(self.screen, (0, 200, 0), (px, py), radius)

        for egg in getattr(world, 'eggs', []):
            ex = int(egg['x'] * scale_x)
            ey = int(egg['y'] * scale_y)
            radius = 3 + int(egg['progress'] * 4)
            pygame.draw.circle(self.screen, (220, 220, 0), (ex, ey), radius)

        for marker in getattr(world, 'death_markers', []):
            mx = int(marker['x'] * scale_x)
            my = int(marker['y'] * scale_y)
            size = 6
            pygame.draw.line(self.screen, (255, 0, 0), (mx - size, my - size), (mx + size, my + size), 2)
            pygame.draw.line(self.screen, (255, 0, 0), (mx - size, my + size), (mx + size, my - size), 2)

        for creature in world.creatures:
            x, y = creature.position
            screen_x = int(x * scale_x)
            screen_y = int(y * scale_y)
            num_blocks = len(creature.genome.blocks)

            # Convertir hue a RGB para colores más visibles
            import colorsys
            # 137.5 (ángulo áureo) evita que conteos de bloques comunes
            # colisionen en el mismo color, a diferencia de un paso fijo
            # como 30 (12 bloques exactos volvía a dar rojo, igual que 0).
            hue = (num_blocks * 137.5) % 360 / 360.0
            saturation = 1.0
            value = 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
            color = (int(r * 255), int(g * 255), int(b * 255))

            pygame.draw.circle(self.screen, color, (screen_x, screen_y), 5)  # Dibujar criatura como un círculo pequeño

        if ui_panel:
            ui_panel.draw(self.screen, self.font, fps)

        stats_lines = [
            f"Tick: {world.tick_count}",
            f"Vida max: {world.max_lifespan_ever}",
            f"Vida promedio (500t): {round(sum(l for _, l in world.lifespan_history) / len(world.lifespan_history), 1) if world.lifespan_history else 0}",
        ]
        for i, line in enumerate(stats_lines):
            surface = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(surface, (self.width - 220, 30 + i * 20))

        pygame.display.flip()
