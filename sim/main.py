import argparse
from sim.world import World

def main(num_ticks):
    world = World()
    # Crear algunos genomas iniciales y spawnear criaturas
    world.run(num_ticks)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the creature-evo simulation.")
    parser.add_argument("num_ticks", type=int, help="Number of ticks to run the simulation")
    args = parser.parse_args()
    main(args.num_ticks)
