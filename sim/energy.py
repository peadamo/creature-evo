class Energy:
    def __init__(self):
        self.energy_levels = {}

    def add_creature(self, creature_id, initial_energy=100):
        self.energy_levels[creature_id] = initial_energy

    def consume_energy(self, creature_id, amount):
        if self.energy_levels.get(creature_id, 0) >= amount:
            self.energy_levels[creature_id] -= amount
            return True
        else:
            return False

    def produce_energy(self, creature_id, amount):
        self.energy_levels[creature_id] += amount

    def check_death(self, creature_id):
        return self.energy_levels.get(creature_id, 0) <= 0
