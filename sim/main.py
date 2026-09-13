import argparse
from sim.world import World
from sim.ui import ControlPanel
from sim.render import Renderer
import pygame

def main(num_ticks, visual=False):
    world = World()

    if visual:
        renderer = Renderer()
        panel = ControlPanel(world, screen_width=renderer.width, screen_height=renderer.height)
        clock = pygame.time.Clock()
        running = True

        while running and (num_ticks is None or world.tick_count < num_ticks):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                panel.handle_event(event)

            for _ in range(panel.ticks_per_frame):
                world.tick(ui_panel=panel)
            renderer.draw(world, ui_panel=panel, fps=clock.get_fps())
            pygame.display.flip()
            clock.tick(30)  # Limitar a 30 FPS
    else:
        if num_ticks is None:
            raise SystemExit("num_ticks is required in headless mode (only --visual can run indefinitely)")
        world.run(num_ticks)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the creature-evo simulation.")
    parser.add_argument("num_ticks", type=int, nargs="?", default=None,
                         help="Number of ticks to run (omit for --visual to run until the window is closed)")
    parser.add_argument("--visual", action="store_true", help="Enable visual rendering with pygame")
    args = parser.parse_args()
    main(args.num_ticks, args.visual)
