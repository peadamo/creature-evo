# Diseño técnico — creature-evo

Estado: prototipo CPU funcional en `sim/` (numpy + pygame), implementando un subconjunto de este diseño. Este documento es la fuente de verdad conceptual — cuando el diseño avanza en las charlas, se vuelca acá antes (o en paralelo) de mandarlo a implementar. La sección 8 lleva el inventario de qué está implementado vs. pendiente.

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

- Reproducción sexual vs. asexual (o ambas, según proximidad/especie) — **actualizado en sección 8.6**: reproducción va a dejar de ser automática y pasar por bloque `incubadora`
- Si hay especiación (nichos que no cruzan) o población única
- Formato exacto de serialización del genoma (para guardar/cargar/inspeccionar individuos)

## 7. Próximo paso técnico

Prototipo mínimo (no GPU todavía) para validar el ciclo completo con población chica (ej. 20-50 naves) en CPU/numpy:
sensar → red de neuronas (grafo NEAT-like) → actuar (motores/armas) → daño por bloque → energía → muerte/reproducción asíncrona.

Una vez que ese ciclo funciona y se ve comportamiento evolutivo mínimo, se migra el núcleo de cómputo (evaluación de redes + física) a Taichi/Warp en fp16/SoA para escalar.

## 8. Estado real del prototipo (actualizado en vivo)

Nota de arquitectura clave descubierta durante la implementación, que reemplaza lo dicho en la sección 2 sobre geometría de bloques: **no hay geometría espacial por bloque, ni rotación, ni colisión física real** (a diferencia de lo planteado inicialmente con Cosmoteer). Los bloques son puramente lógicos — como en el juego de programar creeps en JS (Screeps): un bloque "es" lo que su código hace, no una forma dibujada en el espacio. Cada criatura tiene una única posición global (un punto); el arma, la boca, el sonar, etc. actúan por distancia lógica a ese punto, y el arma elige a qué *tipo* de bloque de la víctima atacar (no a qué posición). Esto simplifica todo el sistema de física y es una decisión de diseño definitiva, no un parche temporal.

### 8.1 Bloques implementados

| Bloque | Neuronas | Costo energético/tick | Función |
|---|---|---|---|
| `banco_neuronal` | N internas (integrate-and-fire, ver 8.3) | `0.5 × num_neuronas` | Cómputo interno, "pensamiento" |
| `sonar` | `dx`, `dy` (input), `activo` (output) | `0.3` si `activo > 0`, si no `0` | Detecta dx/dy normalizado al vecino más cercano, solo si está encendido |
| `actuador` | `dx`, `dy` (output) | `2 × magnitud_movimiento` | Mueve la nave (physics.py promedia todos los actuadores) |
| `generador` | `output` (input al banco) | `0` propio | Consume grasa (`almacenamiento`) a razón de 3/tick, produce energía a razón 2:3 (con pérdida) |
| `boca` | ninguna | `0` | Absorbe hasta 5/tick de un pellet de comida en rango 2.0, lo suma a la reserva de grasa de la criatura |
| `almacenamiento` | ninguna | `0` | Reserva de "grasa" que consume el generador — hoy es un contador global por criatura (`World.fat_levels`), no todavía HP/capacidad por bloque individual |

Pendientes de implementar: `casco`/escudo (HP pasivo sin función activa), `arma` (ver 8.2), `incubadora` (ver 8.6).

### 8.2 Arma (diseñada, no implementada aún)

Ataque de contacto lógico (sin proyectil, sin geometría): cada tick, si la distancia entre dos criaturas es menor a un umbral, la que tiene bloque `arma` puede dañar a la otra. El arma tiene un **output que elige qué tipo de bloque atacar** en la víctima (discretiza su valor continuo en categorías de tipo de bloque — ej. "atacar banco_neuronal" para intentar matar el cerebro directo, en vez de daño genérico). Si la víctima no tiene un bloque de ese tipo, el daño cae en uno al azar. HP por bloque (mencionado en sección 2) sigue pendiente de tabla de valores concreta — la idea es que bloques "sensibles" (banco neuronal) tengan poco HP y futuros bloques de blindaje tengan mucho.

Al destruirse un bloque, deja un pellet de comida en esa posición equivalente a su valor energético (conecta el combate con el sistema de comida/boca ya implementado).

### 8.3 Cerebro: integrate-and-fire con umbral evolutivo (reemplaza la propagación simple original)

Cambio de arquitectura respecto a la sección 3 original: las neuronas del `banco_neuronal` ya no evalúan con un simple `tanh` instantáneo. Ahora:

- Cada neurona del banco tiene un **potencial acumulado que persiste entre ticks**, y un **umbral propio evolutivo** (gen heredable, mutable — no fijo).
- Cada tick: `potencial = potencial_anterior × 0.8 (fuga) + suma_de_entradas_ponderadas`.
- Si `potencial > umbral`: la neurona dispara (emite 1 ese tick, resetea potencial a 0). Si no, emite 0 y el potencial sigue acumulando/decayendo.
- Consecuencia deliberada: una señal que viaja sensor → banco → actuador tarda **como mínimo 2 ticks** en llegar de punta a punta (una pasada de evaluación por tick sobre todas las conexiones, sin reordenar por capas) — hay un "tiempo de reacción" natural según cuántos saltos tenga el camino.
- Las neuronas de **borde** (sensor, actuador) deliberadamente NO tienen esta dinámica — son interfaz directa con el mundo físico (pasan el valor de este tick sin memoria propia), para no distorsionar lecturas de sensores ni retrasar la salida motora con una inercia aparte de la decisión de la red.

### 8.4 Selección natural: ya activa

A diferencia de versiones tempranas del prototipo, hoy **sí hay muerte real por falta de energía** (metabolismo por tipo de bloque + generador que depende de grasa acumulada, no energía gratis). Población fluctúa en vez de crecer sin freno.

### 8.5 Logging de diagnóstico

`World.log_summary()` escribe cada 20 ticks una fila a `sim_log.csv` (gitignored, no versionado) con: tick, población, bloques/conexiones promedio, energía avg/min/max. Solo agregados, nunca detalle por criatura — para inspección liviana sin inflar contexto.

### 8.6 Ciclo de vida — reproducción vía incubadora (implementado)

Reemplazó por completo el modelo viejo (reproducción automática al llegar a un umbral fijo de energía — ese código fue eliminado). Bloque `incubadora`:

- **Input** `desarrollo`: progreso del huevo actual (0 si no hay huevo en curso).
- **Output** `invertir`: cuánta grasa (`fat_levels`) invertir en el huevo este tick — la criatura decide activamente cuánto reservar para reproducirse vs. quedarse con ella.
- **El huevo es una entidad separada en el mapa** (`World.eggs`), con su propia posición (la del padre al momento de ponerlo) — no vive "dentro" del bloque. Es vulnerable: cualquier criatura con `boca` cerca lo puede depredar (reduce su progreso, y si llega a 0 el huevo se destruye y el depredador gana grasa).
- Al llegar a `progress >= 1.0`, eclosiona: nace una cría (genoma del padre + mutación) en la posición del huevo.
- Como `incubadora` no se cablea automáticamente al banco neuronal al nacer (igual que boca/almacenamiento), una criatura recién generada nunca invierte nada hasta que una mutación posterior conecte esa neurona — la reproducción efectiva es rara al principio y depende de que la evolución "descubra" el cableado. Es esperado, no un bug.

### 8.7 Ideas registradas para más adelante (no priorizadas)

- Selección de parentesco: sonar que distinga pariente cercano de extraño (kin selection)
- Costo de conexión proporcional a la distancia entre bloques en la grilla del genoma (penaliza cerebros "desparramados")
- Bloque de comunicación/señalización entre naves (feromonas, posible mentira/señales falsas)
- Envejecimiento: costo metabólico creciente con el tiempo de vida

## 9. Cola de trabajo pendiente (priorizada)

Completado: motores independientes por dirección + física de impulso/inercia real (velocidad persistente, fricción, `Physics.velocities`) — reemplazó el vector de movimiento promediado de la sección 8. Cableado de `incubadora → banco` corregido de paso (no era un simple "olvido", el cableado de `actuador` tampoco había sido migrado del esquema viejo dx/dy al nuevo impulso — quedó todo prolijo en el mismo commit).

Completado: arma con daño de contacto lógico (radio 3.0), selección discretizada de tipo de bloque objetivo, HP por bloque (banco neuronal frágil = 10hp, resto = 30hp), destrucción de bloque al llegar a 0 (limpia neuronas/conexiones/HP asociados) y deja pellet de comida (15) en su lugar. Probado estable 2000 ticks sin crash.

En curso ahora: panel de control visual (punto 1).

1. **Panel de control visual** (pedido explícito): sliders de población mín/máx en vivo, velocidad de simulación, contador de FPS, slider de tasa de mutación, botón/slider de "subsidio" de comida extra.
2. **Métricas de evolución real** en `sim_log.csv` (hoy solo agregados básicos): distribución de umbrales del banco (¿se aleja de uniforme random?), tasa de huevos puestos por tick a lo largo del tiempo, población sostenida por encima del mínimo sin relleno artificial.
3. **Casco/escudo**: bloque pasivo, sin neuronas, solo aporta HP extra a la nave.
4. Repasar bien todo el prototipo antes de considerar la migración a GPU (sección 5) — no tiene sentido optimizar para escala hasta que la lógica evolutiva completa esté validada en chico.
