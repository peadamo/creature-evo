import pygame
import pygame.font

class Renderer:
    def __init__(self, width=1200, height=900):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Creature-Evo Simulation")
        self.font = pygame.font.SysFont(None, 20)
        self.block_count_font = pygame.font.SysFont(None, 16, bold=True)

    def draw(self, world, ui_panel=None, fps=0):
        if world.is_daytime():
            self.screen.fill((20, 20, 20))  # Día: fondo ligeramente más claro
        else:
            self.screen.fill((10, 10, 40))  # Noche: fondo azul oscuro

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
            color = creature.genome.color  # rasgo hereditario, permite rastrear linajes a simple vista

            radius = 11
            pygame.draw.circle(self.screen, color, (screen_x, screen_y), radius)
            brightness = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
            text_color = (0, 0, 0) if brightness > 140 else (255, 255, 255)
            label = self.block_count_font.render(str(num_blocks), True, text_color)
            label_rect = label.get_rect(center=(screen_x, screen_y))
            self.screen.blit(label, label_rect)

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
