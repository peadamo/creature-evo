class ControlPanel:
    def __init__(self, world):
        self.world = world
        self.ticks_per_frame = 1
        self.mutation_multiplier = 1.0
        self.sliders = [
            {'label': 'Min pop', 'attr': 'min_population', 'min': 0, 'max': 1000, 'obj': world},
            {'label': 'Max pop', 'attr': 'max_population', 'min': 0, 'max': 1000, 'obj': world},
            {'label': 'Speed (ticks/frame)', 'attr': 'ticks_per_frame', 'min': 1, 'max': 20, 'obj': self},
            {'label': 'Mutation rate x', 'attr': 'mutation_multiplier', 'min': 0.1, 'max': 5.0, 'obj': self}
        ]
        self.dragging = None
        self.food_subsidy_button_rect = pygame.Rect(10, 130, 200, 30)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for slider in self.sliders:
                bar_x, bar_y = 10, 10 + (self.sliders.index(slider) * 30)
                bar_rect = pygame.Rect(bar_x, bar_y, 200, 20)
                handle_x = int(bar_x + (slider['obj'].__dict__[slider['attr']] - slider['min']) / (slider['max'] - slider['min']) * 200)
                handle_rect = pygame.Rect(handle_x - 5, bar_y - 5, 10, 30)
                if handle_rect.collidepoint(event.pos):
                    self.dragging = slider
            if self.food_subsidy_button_rect.collidepoint(event.pos):
                import random
                for _ in range(20):
                    x = random.uniform(0, self.world.physics.grid_size[0])
                    y = random.uniform(0, self.world.physics.grid_size[1])
                    amount = random.randint(5, 30)
                    self.world.food_pellets.append({'x': x, 'y': y, 'amount': amount})
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            bar_x, bar_y = 10, 10 + (self.sliders.index(self.dragging) * 30)
            handle_x = max(0, min(event.pos[0] - bar_x, 200))
            new_value = self.dragging['min'] + (handle_x / 200) * (self.dragging['max'] - self.dragging['min'])
            if isinstance(self.dragging['obj'], World):
                setattr(self.dragging['obj'], self.dragging['attr'], int(new_value))
            else:
                setattr(self.dragging['obj'], self.dragging['attr'], new_value)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = None

    def draw(self, screen, font, fps):
        for slider in self.sliders:
            bar_x, bar_y = 10, 10 + (self.sliders.index(slider) * 30)
            bar_rect = pygame.Rect(bar_x, bar_y, 200, 20)
            handle_x = int(bar_x + (slider['obj'].__dict__[slider['attr']] - slider['min']) / (slider['max'] - slider['min']) * 200)
            handle_rect = pygame.Rect(handle_x - 5, bar_y - 5, 10, 30)
            pygame.draw.rect(screen, (255, 255, 255), bar_rect, 2)
            pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, handle_x, 20))
            label = f"{slider['label']}: {int(slider['obj'].__dict__[slider['attr']]) if isinstance(slider['obj'], World) else slider['obj'].__dict__[slider['attr']]}"
            text_surface = font.render(label, True, (255, 255, 255))
            screen.blit(text_surface, (bar_x, bar_y - 20))

        pygame.draw.rect(screen, (0, 128, 0), self.food_subsidy_button_rect)
        subsidy_label = "Food subsidy"
        text_surface = font.render(subsidy_label, True, (255, 255, 255))
        screen.blit(text_surface, (self.food_subsidy_button_rect.x + 10, self.food_subsidy_button_rect.y + 5))

        fps_text = f"FPS: {fps:.2f}"
        fps_surface = font.render(fps_text, True, (255, 255, 255))
        screen.blit(fps_surface, (self.width - 100, 10))
