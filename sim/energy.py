class Energy:
    def __init__(self):
        self.energy_levels = {}

    def add_creature(self, creature_id, initial_energy=100):
        self.energy_levels[creature_id] = initial_energy

    def consume_energy(self, creature_id, amount):
        current = self.energy_levels.get(creature_id, 0)
        if current >= amount:
            self.energy_levels[creature_id] = current - amount
            return True
        else:
            # No hay suficiente: se consume lo que queda y cae a 0, en vez de
            # no restar nada. Si no, la criatura queda "congelada" con
            # energía casi-cero para siempre y nunca muere de inanición real.
            self.energy_levels[creature_id] = 0
            return False

    def produce_energy(self, creature_id, amount):
        self.energy_levels[creature_id] += amount

    def check_death(self, creature_id):
        return self.energy_levels.get(creature_id, 0) <= 0
