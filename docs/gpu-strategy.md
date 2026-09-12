# Estrategia GPU: vectorizar grafos de neuronas de tamaño variable

Estado: notas de diseño para la fase 2 (post-prototipo CPU). No bloquea el prototipo actual.

## El problema

Cada criatura tiene un grafo de neuronas distinto (depende de qué bloques tiene: cuántos sensores, cuántos bancos neuronales, etc.) y un número distinto de conexiones. La GPU rinde mejor con arrays de tamaño fijo y operaciones uniformes (SIMD/SIMT) — un grafo "de verdad" dinámico, con punteros y tamaños variables por individuo, es exactamente lo que una GPU maneja mal.

## Enfoque: tamaño máximo + máscara (padding/masking)

En vez de que cada criatura tenga un grafo de tamaño real, se define un **límite superior fijo** para la simulación completa (configurable, ej. `MAX_BLOCKS_POR_NAVE = 64`, `MAX_NEURONAS_POR_NAVE = 512`, `MAX_CONEXIONES_POR_NAVE = 2048`). Cada criatura ocupa slots de ese tamaño máximo en los arrays SoA, y una **máscara binaria** (`activo: bool[]`) indica qué slots realmente existen para esa criatura en este tick.

- Neuronas: array `[N_criaturas, MAX_NEURONAS]` de valores (fp16) + array de máscara `[N_criaturas, MAX_NEURONAS]`.
- Conexiones: arrays paralelos `origen[]`, `destino[]`, `peso[]`, `activa[]`, todos `[N_criaturas, MAX_CONEXIONES]`.
- Evaluar la red = multiplicar/propagar igual para todos, pero las neuronas/conexiones inactivas están enmascaradas (peso efectivo 0, o simplemente no se les asigna índice en el forward pass). El cómputo "de más" en slots vacíos es barato comparado con el beneficio de vectorización uniforme.

## Consecuencia de diseño

- El límite máximo por nave es también un límite de diseño para el genoma: una criatura no puede crecer bloques/neuronas/conexiones más allá del máximo elegido. Esto hay que exponerlo como parámetro de configuración de la simulación (no hardcodeado), igual que la población.
- Subir estos máximos aumenta memoria linealmente por criatura — es el mismo trade-off de "fuerza bruta > precisión" ya elegido: se prioriza población y complejidad, así que estos máximos deberían ser generosos por defecto y el usuario los ajusta si la VRAM no alcanza.
- El orden de evaluación de la red (qué neurona depende de cuál) también tiene que resolverse de forma vectorizable: la opción simple es evaluar por "capas" topológicas (BFS desde las neuronas de entrada) en varias pasadas fijas, en vez de un grafo con orden de evaluación arbitrario por individuo. Se define un número fijo de pasadas de propagación por tick (ej. 4-8), suficiente para que la señal llegue de sensores a actuadores incluso en grafos profundos, sin resolver dependencias exactas por individuo.

## Por qué no resolverlo ahora

El prototipo CPU (numpy, población chica) puede usar grafos realmente dinámicos por individuo sin este problema — sirve para validar que la lógica evolutiva (mutación, crossover, reproducción, daño) funciona antes de pagar el costo de diseñar el layout fijo. Cuando migremos a Taichi/Warp, este documento es el punto de partida.
