# Backlog de features pendientes

## Nuevas neuronas comunes a TODOS los bloques (propuesta del usuario)

A implementar en iteraciones futuras. Estas neuronas darían a la red neuronal más control y observabilidad sobre el estado de cada bloque.

### 1. Input neuronal: `hp_level`
- **Ubicación**: cada bloque
- **Función**: lectura del nivel de vida actual (0.0 = destruido, 1.0 = HP máximo)
- **Rango**: 0.0 a 1.0 normalizado
- **Aplicación**: permite que la red "sepa" cuándo un bloque está cerca de morir y pueda adaptar comportamiento

### 2. Output neuronal: `suicidio`
- **Ubicación**: cada bloque
- **Función**: si la neurona supera un threshold (ej. > 0.5), destruye ese bloque específico
- **Aplicación evolutiva**: permite que la criatura sacrifique un bloque dañado deliberadamente (ej. soltar un bloque que está consumiendo mucha energía por daño)

### 3. Output neuronal: `dormir`
- **Ubicación**: cada bloque
- **Función**: si la neurona supera un threshold, desactiva todas las funciones del bloque (no genera, no consume, no emite neuronas)
- **Consumo**: se vuelve 0 mientras está en "dormición"
- **Aplicación evolutiva**: permite hibernación estratégica o desactivación de bloques costosos en momentos de hambruna

## Notas de implementación

- Cada bloque necesitaría una neurona `hp_level` de entrada nueva (lectura, no cableada al banco por defecto, pero disponible)
- Los outputs `suicidio` y `dormir` necesitarían ser cableados opcionalmente por la evolución (no garantizados al nacer)
- `dormir` requiere agregar un campo `dormido` booleano a cada bloque en Creature
- Impacto en `Energy.consume_energy`: necesitaría chequear si un bloque está dormido antes de cobrar costo

### 4. Neurona sensorial: `huevo_propio_cercano` (propuesta usuario)
- **Ubicación**: solo `incubadora` 
- **Función**: input que detecta si hay un huevo PROPIO en radio ~5.0
- **Rango**: 0.0 si no hay, 1.0 si hay huevo propio cercano
- **Aplicación evolutiva**: permite que la madre defienda/cuide activamente su huevo (seguirlo, protegerlo de depredadores)

## Estado

- [x] Implementar `hp_level` en todos los bloques (completado)
- [x] Implementar `radar_parentesco` sensor (completado - calcula similitud genética)
- [x] Implementar `suicidio` en todos los bloques (completado - auto-amputacion)
- [x] Implementar `dormir` en todos los bloques (completado - hibernacion 50% energía)
- [ ] Testear largas simulaciones para ver si evolución descubre nuevos comportamientos

## CRÍTICO CORREGIDO (post-sesión)

- **Generador**: Consumía 3 grasa, producía 2 energía = DEFICIT NETO (-1)
  - Imposible acumular para reproducción (15 energía/huevo)
  - Reproducción colapsaba post-500 ticks
  - **FIX**: Cambiar a 10 energía (coeficiente 2/3 → 10/3) = +7 neto
  - **Resultado**: Población sostenible (~20 criaturas sin hambruna)

## Próximos pasos

- Simular 10k+ ticks con balance energético arreglado
- Rastrear evolución de comportamientos (suicidio/dormir usage)
- Investigar por qué reproducción aún baja post-500 (aging? evolution drift?)

## Notas recientes

- **Reproducción funciona**: 10 huevos/50 ticks (fix: pesos positivos para invertir/liberar)
- **radar_parentesco**: ~22% de probabilidad, similia genética Hamming distance
- **suicidio**: auto-amputacion selectiva, bloques garantizados protegidos
- **dormir**: hibernacion que reduce energía a 50% + detiene funciones del bloque

