import random

import pygame


class ControlPanel:
    def __init__(self, world, screen_width=800):
        self.world = world
        self.screen_width = screen_width
        self.ticks_per_frame = 1
        self.mutation_multiplier = 1.0
        self.sliders = [
            {'label': 'Min pop', 'attr': 'min_population', 'min': 0, 'max': 1000, 'obj': world},
            {'label': 'Max pop', 'attr': 'max_population', 'min': 0, 'max': 1000, 'obj': world},
            {'label': 'Speed (ticks/frame)', 'attr': 'ticks_per_frame', 'min': 1, 'max': 20, 'obj': self},
            {'label': 'Mutation rate x', 'attr': 'mutation_multiplier', 'min': 0.1, 'max': 5.0, 'obj': self}
        ]
        self.dragging = None
        self.food_subsidy_button_rect = pygame.Rect(10, self.BAR_Y_OFFSET + len(self.sliders) * self.ROW_HEIGHT + 10, 200, 30)

    ROW_HEIGHT = 50
    BAR_Y_OFFSET = 20  # deja lugar arriba para el label

    def _bar_pos(self, index):
        return 10, self.BAR_Y_OFFSET + index * self.ROW_HEIGHT

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, slider in enumerate(self.sliders):
                bar_x, bar_y = self._bar_pos(i)
                handle_x = int(bar_x + (slider['obj'].__dict__[slider['attr']] - slider['min']) / (slider['max'] - slider['min']) * 200)
                handle_rect = pygame.Rect(handle_x - 12, bar_y - 5, 24, 30)
                if handle_rect.collidepoint(event.pos):
                    self.dragging = slider
            if self.food_subsidy_button_rect.collidepoint(event.pos):
                # Antes tiraba pellets chicos en posiciones 100% al azar del
                # mapa - el efecto era invisible, se perdía entre la comida
                # ya existente. Ahora: más cantidad, más grandes, y cerca de
                # criaturas vivas para que el efecto se note al toque.
                grid_w, grid_h = self.world.physics.grid_size
                for _ in range(30):
                    if self.world.creatures:
                        base = random.choice(self.world.creatures).position
                        x = max(0, min(grid_w, base[0] + random.uniform(-10, 10)))
                        y = max(0, min(grid_h, base[1] + random.uniform(-10, 10)))
                    else:
                        x = random.uniform(0, grid_w)
                        y = random.uniform(0, grid_h)
                    amount = random.randint(80, 150)
                    self.world.food_pellets.append({'x': x, 'y': y, 'amount': amount})
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            bar_x, bar_y = self._bar_pos(self.sliders.index(self.dragging))
            handle_x = max(0, min(event.pos[0] - bar_x, 200))
            new_value = self.dragging['min'] + (handle_x / 200) * (self.dragging['max'] - self.dragging['min'])
            is_int_slider = self.dragging['attr'] in ('min_population', 'max_population', 'ticks_per_frame')
            setattr(self.dragging['obj'], self.dragging['attr'], int(new_value) if is_int_slider else new_value)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = None

    def draw(self, screen, font, fps):
        for i, slider in enumerate(self.sliders):
            bar_x, bar_y = self._bar_pos(i)
            bar_rect = pygame.Rect(bar_x, bar_y, 200, 20)
            handle_x = int(bar_x + (slider['obj'].__dict__[slider['attr']] - slider['min']) / (slider['max'] - slider['min']) * 200)

            # Fondo del riel + relleno tenue hasta el valor actual (para que
            # se note el rango recorrido sin que tape el pomo del handle).
            pygame.draw.rect(screen, (60, 60, 60), bar_rect)
            pygame.draw.rect(screen, (90, 90, 140), (bar_x, bar_y, handle_x, 20))
            pygame.draw.rect(screen, (255, 255, 255), bar_rect, 2)

            # Pomo del slider: círculo bien visible con borde, claramente
            # distinto del relleno - antes era el mismo rojo que el relleno
            # y no se distinguía dónde agarrar para arrastrar.
            knob_center = (bar_x + handle_x, bar_y + 10)
            pygame.draw.circle(screen, (255, 60, 60), knob_center, 10)
            pygame.draw.circle(screen, (255, 255, 255), knob_center, 10, 2)

            raw_value = slider['obj'].__dict__[slider['attr']]
            is_population_slider = slider['attr'] in ('min_population', 'max_population')
            label = f"{slider['label']}: {int(raw_value) if is_population_slider else round(raw_value, 2)}"
            text_surface = font.render(label, True, (255, 255, 255))
            screen.blit(text_surface, (bar_x, bar_y - 18))

        pygame.draw.rect(screen, (0, 128, 0), self.food_subsidy_button_rect)
        subsidy_label = "Food subsidy"
        text_surface = font.render(subsidy_label, True, (255, 255, 255))
        screen.blit(text_surface, (self.food_subsidy_button_rect.x + 10, self.food_subsidy_button_rect.y + 5))

        fps_text = f"FPS: {fps:.2f}"
        fps_surface = font.render(fps_text, True, (255, 255, 255))
        screen.blit(fps_surface, (self.screen_width - 100, 10))
