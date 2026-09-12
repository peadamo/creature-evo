import argparse
from sim.world import World
from sim.render import Renderer
import pygame

def main(num_ticks, visual=False):
    world = World()

    if visual:
        renderer = Renderer()
        clock = pygame.time.Clock()
        running = True

        while running and world.tick_count < num_ticks:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            world.tick()
            renderer.draw(world)
            pygame.display.flip()
            clock.tick(30)  # Limitar a 30 FPS
    else:
        world.run(num_ticks)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the creature-evo simulation.")
    parser.add_argument("num_ticks", type=int, help="Number of ticks to run the simulation")
    parser.add_argument("--visual", action="store_true", help="Enable visual rendering with pygame")
    args = parser.parse_args()
    main(args.num_ticks, args.visual)
