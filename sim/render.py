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

        # Mapa de calor de temperatura: grilla gruesa de 10x10 celdas, azul
        # (frío, temp~1.0) a naranja (caliente, temp~5.0 cerca de los focos).
        cells = 10
        cell_w = grid_w / cells
        cell_h = grid_h / cells
        for cx in range(cells):
            for cy in range(cells):
                center_x = (cx + 0.5) * cell_w
                center_y = (cy + 0.5) * cell_h
                temp = world.physics.temperature_at(center_x, center_y)
                t = max(0.0, min(1.0, (temp - 1.0) / 4.0))
                color = (
                    int(0 + t * 150),
                    int(0 + t * 30),
                    int(100 - t * 100),
                )
                rect = pygame.Rect(cx * cell_w * scale_x, cy * cell_h * scale_y, cell_w * scale_x, cell_h * scale_y)
                pygame.draw.rect(self.screen, color, rect)

        for pellet in getattr(world, 'food_pellets', []):
            px = int(pellet['x'] * scale_x)
            py = int(pellet['y'] * scale_y)
            radius = max(2, min(6, int(pellet['amount'] / 20)))
            pygame.draw.circle(self.screen, (0, 200, 0), (px, py), radius)

        for egg in getattr(world, 'eggs', []):
            ex = int(egg['x'] * scale_x)
            ey = int(egg['y'] * scale_y)

            # Tamaño del huevo = progreso visual
            progress_pct = min(1.0, egg['progress'] / egg['capacity'])
            radius = 3 + int(progress_pct * 6)

            # Color según fase
            color = (220, 180, 0) if egg['phase'] == 'interno' else (220, 220, 0)
            pygame.draw.circle(self.screen, color, (ex, ey), radius)

            # Barra de progreso arriba del huevo
            bar_width = 12
            bar_height = 2
            bar_x = ex - bar_width // 2
            bar_y = ey - radius - 6
            pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))  # fondo
            pygame.draw.rect(self.screen, (0, 200, 0), (bar_x, bar_y, int(bar_width * progress_pct), bar_height))  # progreso

        for marker in getattr(world, 'death_markers', []):
            mx = int(marker['x'] * scale_x)
            my = int(marker['y'] * scale_y)
            size = 6
            pygame.draw.line(self.screen, (255, 0, 0), (mx - size, my - size), (mx + size, my + size), 2)
            pygame.draw.line(self.screen, (255, 0, 0), (mx - size, my + size), (mx + size, my - size), 2)

        # Línea de ataque: destello entre atacante y víctima, dura pocos ticks.
        for marker in getattr(world, 'attack_markers', []):
            x1 = int(marker['x1'] * scale_x)
            y1 = int(marker['y1'] * scale_y)
            x2 = int(marker['x2'] * scale_x)
            y2 = int(marker['y2'] * scale_y)
            pygame.draw.line(self.screen, (255, 140, 0), (x1, y1), (x2, y2), 2)

        # Explosión/resto al perder un bloque en combate (no la muerte final).
        for marker in getattr(world, 'block_destroy_markers', []):
            mx = int(marker['x'] * scale_x)
            my = int(marker['y'] * scale_y)
            progress = marker['ticks_left'] / 12.0
            radius = int(4 + (1 - progress) * 14)
            alpha_color = (200, 80, 0)
            pygame.draw.circle(self.screen, alpha_color, (mx, my), radius, 2)

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

            # Barrita de energía arriba de la nave: verde=llena, roja=vacía.
            energy = world.energy.energy_levels.get(id(creature), 0)
            frac = max(0.0, min(1.0, energy / 100.0))
            bar_w, bar_h = 24, 3
            bar_x = screen_x - bar_w // 2
            bar_y = screen_y - radius - 8
            pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
            bar_color = (int(255 * (1 - frac)), int(255 * frac), 0)
            pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, int(bar_w * frac), bar_h))

        if ui_panel:
            ui_panel.draw(self.screen, self.font, fps)

        population = len(world.creatures)
        max_generation = getattr(world, 'max_generation_ever', 0)
        stats_lines = [
            f"Tick: {world.tick_count}",
            f"Población: {population} / {world.max_creatures}",
            f"Gen máx: {max_generation}",
            f"Vida max: {world.max_lifespan_ever}",
            f"Vida promedio (500t): {round(sum(l for _, l in world.lifespan_history) / len(world.lifespan_history), 1) if world.lifespan_history else 0}",
        ]
        for i, line in enumerate(stats_lines):
            surface = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(surface, (self.width - 220, 30 + i * 20))

        pygame.display.flip()
