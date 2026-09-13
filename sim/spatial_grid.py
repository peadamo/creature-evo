import math


class SpatialGrid:
    """Grilla uniforme para búsquedas de vecino más cercano sin comparar
    contra toda la población (evita el O(n^2) de recorrer todas las
    criaturas/pellets por cada una). Se reconstruye una vez por tick."""

    def __init__(self, cell_size=10.0):
        self.cell_size = cell_size
        self.buckets = {}

    def _key(self, x, y):
        return (int(x // self.cell_size), int(y // self.cell_size))

    def build(self, items):
        """items: iterable de (x, y, obj)"""
        self.buckets = {}
        for x, y, obj in items:
            key = self._key(x, y)
            self.buckets.setdefault(key, []).append((x, y, obj))

    def nearest(self, x, y, exclude_obj=None, max_radius=None):
        """Devuelve (obj, distancia) del más cercano a (x,y), o (None, None).
        Expande anillos de celdas hacia afuera hasta encontrar candidatos,
        y una celda extra de margen para no perderse un vecino más cerca
        que cayó en una celda diagonal."""
        cx, cy = self._key(x, y)
        best_obj, best_dist = None, float('inf')
        max_ring = 30  # tope de seguridad (mapas típicos de esta sim son 100x100)

        ring = 0
        extra_margin = 0
        while ring <= max_ring:
            any_bucket = False
            for dx in range(-ring, ring + 1):
                for dy in range(-ring, ring + 1):
                    if max(abs(dx), abs(dy)) != ring:
                        continue
                    bucket = self.buckets.get((cx + dx, cy + dy))
                    if not bucket:
                        continue
                    any_bucket = True
                    for ox, oy, obj in bucket:
                        if obj is exclude_obj:
                            continue
                        d = math.hypot(ox - x, oy - y)
                        if d < best_dist:
                            best_dist = d
                            best_obj = obj

            if best_obj is not None:
                extra_margin += 1
                if extra_margin > 1:
                    break
            if any_bucket or best_obj is not None:
                pass
            ring += 1

        if best_obj is None:
            return None, None
        if max_radius is not None and best_dist > max_radius:
            return None, None
        return best_obj, best_dist
