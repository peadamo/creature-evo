# Diseño técnico — creature-evo

Estado: diseño inicial, sin implementación. Este documento es la fuente de verdad para Aider/el agente local antes de escribir código. Cualquier cambio de diseño se edita acá primero.

## 1. Objetivo filosófico

Simular un ecosistema de naves-criatura con cuerpo y cerebro coevolutivos, lo suficientemente completo como para satisfacer los criterios biológicos clásicos de "vida" (metabolismo, homeostasis, reproducción, respuesta al entorno, adaptación por selección) sin ser biología. El sistema es la evidencia; no hace falta ganarle la discusión filosófica a nadie, solo que corra y se sostenga solo.

## 2. Cuerpo: naves modulares en grilla (inspirado en Cosmoteer)

- Cada criatura es un conjunto de **bloques** colocados en una grilla 2D discreta, relativa a un bloque núcleo (core).
- Tipos de bloque base: `core` (obligatorio, 1 por nave), `casco` (estructura/HP), `motor` (empuje), `arma` (daño a distancia/contacto), `sensor` (visión/proximidad/contacto), `generador` (produce energía), `banco_neuronal` (ver sección 3).
- Cada bloque tiene: posición relativa (x,y), orientación, HP propio, costo de energía en reposo, y parámetros específicos de su tipo.
- **El daño es local**: un impacto destruye el bloque que recibe el golpe, no un "HP total" abstracto de la nave. Perder el motor te deja a la deriva; perder el arma te deja indefensa. Esto genera presión selectiva real hacia redundancia y blindaje distribuido, no solo "más HP".
- La física de colisión y masa es simple: masa/inercia = suma de bloques, colisión en grilla discreta (no soft-body continuo). Prioriza throughput sobre precisión (ver sección 5).

## 3. Cerebro: neuronas ancladas a bloques físicos

Concepto central del usuario, no negociable: **el cerebro no es una red separada del cuerpo — está distribuido dentro de él.**

- **Cada parámetro relevante de un bloque es una neurona** (una terminación nerviosa): lectura de sensor, HP actual del bloque, nivel de energía disponible, ángulo de un motor, gatillo de un arma, etc. Estas son las neuronas de entrada/salida "de borde", ancladas físicamente a la parte del cuerpo que las genera o consume.
- **Bloques de tipo `banco_neuronal`**: no representan ninguna función física externa, solo aportan N neuronas internas "libres" (ej. 16 por bloque) al grafo de la criatura. Sirven para computación interna — capas ocultas, memoria, procesamiento — no ligada 1:1 a un sensor o actuador. Más bloques de este tipo = cerebro más profundo, a costa de espacio en la grilla y energía.
- **El grafo de neuronas de una criatura es la unión de**: neuronas de borde (una por parámetro de cada bloque presente) + neuronas libres (de cada banco neuronal presente). El tamaño y forma de este grafo depende directamente de qué bloques tiene la nave — cuerpo y cerebro son la misma estructura genética, no dos sistemas evolucionando en paralelo por separado.
- **Conexiones (sinapsis) entre neuronas**: pesos con topología variable, estilo NEAT — no hay una arquitectura fija de capas. Cada conexión es un gen `(neurona_origen, neurona_destino, peso, activa/inactiva)`.
- **Herencia**: tanto la lista de bloques (cuerpo) como la lista de conexiones (pesos + topología) son parte del genoma y se heredan/mutan juntas. Mutaciones posibles:
  - Estructurales de cuerpo: agregar/quitar/mover un bloque (esto automáticamente agrega/quita las neuronas de borde asociadas)
  - Estructurales de cerebro: agregar/quitar una conexión, agregar un banco neuronal
  - Paramétricas: ajustar un peso existente
  - Al usar identificadores estables de gen (innovation numbers estilo NEAT) para las conexiones, el crossover entre dos genomas puede alinear conexiones homólogas en vez de mezclar a ciegas.

Esto significa que perder un sensor en batalla no solo te deja "ciega" — literalmente elimina esas neuronas del grafo (y las conexiones que dependían de ellas) en el individuo actual; no afecta el genoma que ya se heredó a las crías previas.

## 4. Economía de energía y reproducción (ecosistema asíncrono)

- No hay generaciones discretas. Población continua tipo ecosistema real.
- Cada bloque activo consume energía por tick; `generador` la produce (ej. de una fuente ambiental tipo "sol"/campo de energía del mapa).
- Matar a otra nave y/o recolectar recursos del entorno otorga energía.
- Al acumular energía suficiente, una criatura se reproduce (asexual con mutación, o sexual si hay otra criatura cerca — a definir en iteración 2). La cría nace con un costo de energía para el progenitor.
- Sin energía suficiente, los bloques dejan de funcionar (no reciben corriente) y eventualmente la nave muere — esto es el "metabolismo".
- **Control de población**: parámetro configurable de población objetivo mínima/máxima. UI expone un slider de rango razonable (0–1000) pero el valor real es un entero sin tope hardcodeado — si el usuario escribe 1,000,000 el sistema lo intenta (y se cae con la GPU que tenga, no por límite artificial de software).

## 5. Estrategia de cómputo GPU: fuerza bruta > precisión

Decisión de arquitectura explícita: priorizar cantidad de individuos y complejidad física por individuo, sacrificando precisión numérica.

- **fp16 (media precisión)** para pesos de red neuronal y estados físicos, en vez de fp32. En una RTX 4080 Super esto casi duplica cuántas naves/neuronas entran en memoria y el throughput de cómputo (tensor cores rinden mucho mejor en fp16).
- **Structure-of-Arrays (SoA)**, no un objeto por criatura: arrays contiguos como "posición X de todas las naves", "HP de todos los bloques", etc. Es el layout que permite que la GPU procese miles/millones de entidades en paralelo sin overhead de indirección.
- Física de colisión discreta en grilla, no continua de alta precisión.
- Consecuencia aceptada: inestabilidad numérica y "ruido" genético mayor que con fp32 — es intencional, no un bug a corregir después.
- Motor candidato: Python + Taichi o NVIDIA Warp (compilan a kernels CUDA), evaluar cuál maneja mejor grafos de topología variable (el cerebro NEAT-like es la parte más incómoda de vectorizar, porque cada criatura puede tener un grafo de neuronas de forma distinta — a resolver: probablemente rellenar hasta un tamaño máximo de grafo por "generación de bloques posibles" y enmascarar neuronas/conexiones inactivas, en vez de grafos de tamaño realmente dinámico en GPU).

## 6. Preguntas abiertas para iteración 2 (no bloquean el arranque)

- Reproducción sexual vs. asexual (o ambas, según proximidad/especie)
- Cómo se relaciona el sensor "visión" con el resto de naves (raycasting discreto en grilla vs. campo de proximidad)
- Si hay especiación (nichos que no cruzan) o población única
- Formato exacto de serialización del genoma (para guardar/cargar/inspeccionar individuos)

## 7. Próximo paso técnico

Prototipo mínimo (no GPU todavía) para validar el ciclo completo con población chica (ej. 20-50 naves) en CPU/numpy:
sensar → red de neuronas (grafo NEAT-like) → actuar (motores/armas) → daño por bloque → energía → muerte/reproducción asíncrona.

Una vez que ese ciclo funciona y se ve comportamiento evolutivo mínimo, se migra el núcleo de cómputo (evaluación de redes + física) a Taichi/Warp en fp16/SoA para escalar.
