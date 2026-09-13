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

Completado: métricas de evolución en `sim_log.csv` (umbral promedio/desvío del banco, huevos eclosionados por ventana, rellenos artificiales por ventana, cantidad de huevos/comida activos).

**Resuelto (decisión propia, autorizada por el usuario a tomar estos ajustes sin consultar cada vez)**: la causa real no era solo el balance de costos — el sonar nunca sensó dirección de comida (solo criatura más cercana), así que ni con boca+generador podían aprender a buscar alimento. Ahora todo genoma inicial garantiza `boca`+`generador`+`actuador`+`sonar` de base (más 1-3 bloques random encima), y el sonar tiene 2 neuronas nuevas (`dx_comida`,`dy_comida`) además de las de criatura más cercana. De paso se encontró y arregló un crash real: `remove_block()` convertía `self.connections` de dict a lista, rompiendo `evaluate()` en cualquier criatura que hubiera perdido un bloque en combate. Verificado: la población ya no se extingue del todo entre ciclos de repoblación, tendencia de supervivencia creciente (1→10 sobrevivientes antes del relleno en una corrida de 500 ticks). Reproducción real vía huevos todavía no ocurrió en esa ventana — sigue dependiendo de que la evolución cablee la incubadora.

Completado: panel de control visual (sliders población mín/máx, velocidad, tasa de mutación en vivo, botón de subsidio de comida, contador FPS — `sim/ui.py`). Completado: bloque `casco` (50 HP, pasivo, sin neuronas). De paso se encontró y arregló un bug real: `block_hp` solo se asignaba dentro del branch de `banco_neuronal` — ningún otro bloque tenía HP propio seteado, todo el combate dependía del valor por defecto (30) de un `.get()`. Ya corregido, HP se asigna a todos los tipos de bloque en la creación de la criatura.

**Hallazgo corregido tras revisión de código más profunda**: la corrida de 5000 ticks que en un principio pareció mostrar un ecosistema autosostenido (huevos reemplazando muertes sin relleno artificial) resultó ser en parte un artefacto de un bug real: `Energy.consume_energy` no restaba nada cuando la energía disponible era menor al costo, en vez de bajarla a 0 — las criaturas quedaban "congeladas" vivas con energía casi-cero para siempre, sin morir de inanición real. Eso generaba un falso ciclo estable. Ya corregido (commit `9cdf75c`).

Con la muerte real funcionando, una corrida nueva de 5000 ticks muestra `eggs_hatched_per_20ticks = 0` durante toda la segunda mitad — la reproducción vía incubadora **no** está sosteniendo la población todavía, depende 100% del relleno artificial.

**Segundo bug encontrado en la misma revisión**: `tick_incubadoras()` estaba definida pero **nunca se llamaba** desde `World.tick()` — el comentario decía "reproducción ahora sucede vía incubadora" pero faltaba la línea que efectivamente la invocaba. Los huevos jamás se pusieron en ninguna corrida anterior. Corregido (commit `56d2d85`).

Tras el fix, `egg_count` sigue en 0 durante toda una corrida de 5000 ticks — no es un bug nuevo esta vez: `incubadora` no es un bloque garantizado al nacer (solo boca/generador/actuador/sonar lo son), y con `avg_blocks_per_creature` rondando 1.85-2.1 en esa corrida, la población no está desarrollando bloques extra más allá de los garantizados — probablemente ningún individuo llegó a tener `incubadora` en esa ventana. Es esperable dado lo poco que sobrevive cada generación; no se toca más por ahora, es cuestión de dejarlo correr más tiempo o considerar si conviene que `incubadora` también sea garantizado.

Pendiente:

1. Repasar bien todo el prototipo antes de considerar la migración a GPU (sección 5) — no tiene sentido optimizar para escala hasta que la lógica evolutiva completa esté validada en chico.

## 10. Sesión de objetivo abierto: reproducción real y análisis emergente

Contexto: se le dio a Claude el objetivo abierto de lograr reproducción sostenida multi-generación (linaje bisabuelo→nieto) y experimentar libremente con análisis de comportamiento/optimización, sin supervisión paso a paso.

### 10.1 Cadena de bugs que bloqueaban toda reproducción real (encontrados y arreglados en secuencia)

Cada uno estaba oculto por el anterior — recién se manifestaba al arreglar el previo:

1. **Sonar ciego de nacimiento**: el toggle `activo` nacía apagado y casi nunca se prendía solo (problema huevo-gallina). El sonar ahora siempre sensa.
2. **Calibración de disparo mal escalada**: la señal típica de los sensores (~0.03-0.08 normalizada) era demasiado chica frente al umbral de disparo (0.3-1.5) y la fuga (20%/tick) — casi ninguna neurona del banco disparaba nunca, en ningún lado del sistema. Fuga bajada a 5%/tick, umbrales a 0.1-0.6.
3. **Primera inversión de huevo no contaba**: `mutate_genome`/`tick_incubadoras` solo sumaba progreso en inversiones *subsiguientes*, no en la que crea el huevo. Con el disparo tan raro (~2.6%/tick), la mayoría de las criaturas solo invierte una vez en toda su vida — esa única vez no contaba.
4. **El huevo moría con el padre**: dado que casi nadie vive lo suficiente para invertir dos veces, perder el huevo al morir el padre garantizaba que ningún huevo llegara nunca a completarse. Ahora el huevo persiste huérfano.
5. **Crash consecuente**: el fix anterior (huevo huérfano) rompió el código de eclosión/depredación, que asumía que siempre había un dueño registrado en `creature_eggs`. `StopIteration` al eclosionar el primer huevo sin padre vivo. Arreglado.
6. **Tasa de progreso insuficiente**: incluso arreglado todo lo anterior, el multiplicador de progreso (0.02, luego 0.1) requería más inversiones de las que una vida realista permite. Subido a 0.5 — una sola inversión decente alcanza para completar un huevo.

Resultado: primer huevo eclosionado con éxito, y una corrida de 5000 ticks alcanzó **generación 3** (bisabuelo→abuelo→padre→nieto). Pero en corridas de 8000 ticks, la población viva vuelve a colapsar a puro generación 0 la mayoría del tiempo — la reproducción ocurre pero como evento raro, no sostenido. Pendiente de más ajuste.

### 10.2 Curiosidad destacada: la muerte cerebral es evolutivamente ventajosa (bug de balance)

Análisis de correlación bloques↔longevidad sobre 1500+ muertes registradas:

- Controlando por si el banco neuronal seguía intacto al morir, la cantidad de neuronas/conexiones **no** correlaciona con vida más corta (r≈-0.04, prácticamente nula) — descarta la hipótesis de "más cerebro = más caro, mueren antes" como efecto directo.
- Pero: **las criaturas con el banco neuronal destruido en combate viven en promedio 177 ticks, contra 44 de las que lo conservan intacto — 4x más.** Perder el cerebro elimina su costo de mantenimiento (0.5×5 neuronas = 2.5 energía/tick) y las deja "congeladas" sin gastar en moverse; si había comida cerca, sobreviven a la deriva sin hacer nada. El sistema hoy premia la ausencia de cognición. Es un desbalance real (no arreglado aún) — decidir si corregirlo (ej. penalizar la inmovilidad, o encarecer tener el cuerpo sin cerebro) o dejarlo como hallazgo filosóficamente interesante del proyecto.

### 10.3 Otra curiosidad: posible aversión a atacar parientes

Con el color ahora heredado (sección 8), medí la distancia de color RGB entre atacante y víctima en eventos de combate real, contra la distancia de color de pares aleatorios de la población (proxy de parentesco genético). Sobre una muestra chica (262 eventos): distancia promedio atacante-víctima 178 vs. 162 de pares al azar — una tendencia leve a atacar a individuos *más* distintos (menos emparentados). Señal débil, muestra insuficiente para confirmar que no es ruido; interesante para repetir con más datos.

**Repetido con muestra grande (3519 eventos de combate, 6000 pares aleatorios, misma corrida): el resultado se invirtió y se hizo mucho más fuerte** — distancia de color promedio en combate real 57.9, contra 129.3 de pares al azar de *toda* la población. Es decir, el arma ataca preferentemente a individuos de color *similar* (más emparentados), no distinto.

**Pero hay una trampa metodológica importante que hay que señalar antes de festejar esto como "las naves reconocen a su familia"**: el control de "pares aleatorios de toda la población" no es el control correcto. El arma solo puede atacar al vecino más cercano dentro de un radio de 3.0 unidades — es decir, **combate = necesariamente cercanía espacial**. Y como las crías nacen en la posición exacta de su padre (`egg['x'], egg['y']` = posición del padre al poner el huevo), los parientes cercanos genéticamente también tienden a estar cerca espacialmente al nacer. Así que "el arma ataca a los más parecidos en color" podría ser enteramente un efecto secundario de "el arma ataca a los más cercanos, y los más cercanos tienden a ser parientes por cómo nacen los huevos" — sin que haya ningún reconocimiento de parentesco real en el sistema. Para aislar el efecto genuino haría falta comparar contra pares *aleatorios pero igual de cercanos espacialmente* (mismo radio ~3.0), no contra pares de toda la población dispersa en el mapa de 100x100. Pendiente de rehacer con ese control correcto antes de sacar conclusiones fuertes — aun así, el clustering espacial de parientes en sí mismo (aunque sea "solo" un efecto de dónde nacen los huevos) es un hallazgo interesante por derecho propio.

### 10.4 Optimización de performance

Perfilado con `cProfile` (100-150 población, 200 ticks) mostró que 32 de 59 segundos se iban en `np.linalg.norm` para calcular distancias 2D simples (13M llamadas, overhead de numpy desproporcionado para un cálculo trivial). Reemplazado por `math.hypot` en las 4 ubicaciones (`update_sensors`, `absorb_food`, `apply_combat`): **47x más rápido** (59s → 1.26s mismo trabajo). Sin cambio de comportamiento, solo velocidad.

Además: el sistema escalaba O(n²) (1000 población: 242ms/tick). Se agregó `sim/spatial_grid.py`, un índice espacial en grilla para las 3 búsquedas de vecino más cercano (creatura más cercana, comida más cercana, víctima de combate más cercana), validado contra fuerza bruta (0 errores en 300 puntos random) antes de integrarlo. Resultado: 1000 población pasó de 242ms a 31ms/tick (~7.7x), escalando ahora casi lineal.

### 10.5 Selección natural real y visible (buena noticia)

Comparando gen-0 vs gen-1 en una corrida de 4000 ticks: los hijos (gen-1, n=18) viven más en promedio (61.6 ticks) que la población general (37.1), y el 100% tiene el bloque `incubadora` cableado — contra solo 23% en la población general (tasa base de aparición al azar). Es decir, **la selección está funcionando**: los que logran reproducirse tienden a tener rasgos que favorecen reproducirse de nuevo. El cuello de botella para que esto se sostenga no es que los hijos sean peores — es que el evento de reproducción exitosa en sí sigue siendo raro a nivel población (18 gen-1 sobre >2000 nacimientos totales en la corrida), por lo que el linaje tarda en compunding profundo antes de que la muestra se apague por azar.

### 10.6 Bug heredable raro: conexión colgante pasada de padre a hijo (encontrado durante el análisis de linajes)

Mientras se investigaba por qué los linajes no se sostienen, apareció un crash nuevo (`KeyError` en `Creature.evaluate()`, buscando una neurona de banco que no existía) — no reproducible con 29 semillas distintas de 3000 ticks, señal de que era genuinamente raro, no un bug determinista fácil de disparar.

Causa real: `Creature.remove_block()` (llamado cuando el combate destruye un bloque) limpiaba las conexiones del diccionario en memoria de esa instancia (`self.connections`), pero **nunca tocaba `self.genome.connections`** (la lista que efectivamente viaja al hijo vía `copy.deepcopy` cuando esa criatura pone un huevo). Si una criatura perdía un bloque en combate y **después** lograba reproducirse, el genoma heredado por su cría conservaba una conexión colgante hacia una neurona ya destruida — y la cría explotaba al construirse. Por eso era tan raro: hacían falta ambos eventos (perder un bloque Y reproducirse después) en la misma criatura, y ambos son individualmente poco frecuentes. Arreglado: `remove_block` ahora limpia ambas listas.

### 10.7 Población base más grande: no da linajes más profundos, pero sí más frecuentes

Con el crash heredable ya arreglado, comparé población mínima 20 vs. 100-150 en corridas de 15000 ticks (mismas condiciones, solo cambia el tamaño de población):

- **Población 20**: alcanzó generación 4 (máximo histórico), pero la población viva mostró algún individuo de generación >0 en solo 2 de 15 muestreos cada 1000 ticks — la mayoría del tiempo es puro gen-0.
- **Población 100-150**: alcanzó generación 3 (un poco menos en profundidad máxima, dentro de la variación esperada entre corridas), pero mostró generación >0 viva en 5 de 15 muestreos — más del doble de frecuencia.

Conclusión: más población no hace que una línea individual llegue más lejos, pero sí aumenta las chances de que *en cualquier momento dado* haya algún linaje reciente vivo, simplemente porque hay más intentos en paralelo. Tiene sentido estadístico — no es una mejora del mecanismo, es fuerza bruta de muestreo. Pendiente: correr por más tiempo con población grande para ver si eventualmente compone una cadena más profunda que con población chica.

### 10.8 Sistema de registro de linaje/árbol genealógico (implementado)

`World.lineage_log` guarda cada nacimiento por huevo como `{child_id, parent_id, generation, birth_tick}`. `World.export_lineage_csv(path)` lo vuelca a CSV para análisis offline (no se llama automáticamente, es manual). Corrida de prueba de 10000 ticks: 58 nacimientos registrados, generación máxima 3.

## 11. Backlog de hipótesis y experimentos a futuro (multi-disciplinar)

Pedido explícito del usuario: seguir generando ángulos de análisis desde biología, química, psicología y sociología, con hipótesis concretas testeables — no solo features, sino preguntas a las que el experimento podría responder.

### 11.1 Hipótesis biológicas/evolutivas
- **¿Hay especiación?** Si dejamos correr mucho tiempo con población grande, ¿emergen dos o más "linajes de color" (proxy de parentesco) que dejan de cruzarse/convivir en la misma zona del mapa? Medible con el color heredado + clustering espacial.
- **¿El costo metabólico por bloque genera un "tamaño corporal óptimo"?** Graficar `avg_blocks_per_creature` en función del tiempo — ¿converge a un valor estable, o sigue creciendo/decreciendo sin límite?
- **Selección r vs. K**: ¿emergen dos estrategias — reproducirse rápido con poca inversión (r) vs. invertir mucho en pocos huevos robustos (K)? Se podría medir agrupando por `invertir_value` promedio de cada linaje exitoso.

### 11.2 Hipótesis "químicas" (economía de energía como proxy)
- **¿Hay especies "solares" vs. "depredadoras"?** Comparar linajes que sobreviven mayormente vía `generador`+`boca` (herbívoros/autótrofos) vs. los que sobreviven mayormente por `arma` (depredadores) — ¿cuál tiene mejor tasa de reproducción a largo plazo?
- **Punto de equilibrio de la reserva de grasa (`almacenamiento`)**: ¿las criaturas con este bloque tienen ventaja real, o es puro costo sin beneficio medible dado que hoy no hay mecánica de "hambruna estacional" que lo premie?

### 11.3 Hipótesis "psicológicas" (dinámica interna de la red neuronal)
- **¿Hay "personalidades" estables?** Tomar el patrón de disparo del banco neuronal de un individuo a lo largo de su vida — ¿es consistente (mismo ritmo/umbral efectivo) o cambia según el contexto (cerca de comida vs. cerca de un depredador)?
- **Umbral evolutivo como proxy de "temperamento"**: linajes con umbrales bajos (disparan fácil, reactivos) vs. umbrales altos (disparan poco, "cautelosos") — ¿alguno de los dos predice mejor supervivencia?

### 11.4 Hipótesis sociológicas
- Ya en curso: sesgo de parentesco en combate (sección 10.3, señal débil, muestra chica — repetir con más datos).
- **¿Hay agrupamiento espacial por color/parentesco?** (clustering real, no solo en combate) — tomar snapshots de posición+color y medir si individuos de colores similares están sistemáticamente más cerca entre sí que el azar.
- **¿La violencia se correlaciona con densidad poblacional?** Tasa de eventos de combate por individuo en función de cuán cerca del máximo de población está el sistema en ese momento.

### 11.5 Funcionalidades pedidas para soportar estos análisis
1. ✅ **Guardar/cargar poblaciones** (checkpointing): implementado — `Genome.to_dict/from_dict` + `World.save_population/load_population` (JSON). Probado guardando y recargando una población real (bloques verificados byte a byte, incluso con criaturas ya dañadas por combate). Nota de diseño: al cargar, la generación se resetea a 0 (no se preserva el linaje entre sesiones, solo el genoma) — documentado en el propio código.
2. ✅ **Más gráficos**: implementado `sim/report.py` — lee `sim_log.csv`/`lineage.csv` y genera 2 imágenes (población/generación/energía/distancia a comida/reproducción real vs. relleno artificial/bloques promedio, y dispersión de nacimientos por generación en el tiempo). Uso: `python -m sim.report [sim_log.csv] [lineage.csv] [carpeta_salida]`.
3. **Entorno más rico**: ciclo día/noche (afecta producción del `generador`, tipo "solar" real — de noche no genera), temperatura (zonas del mapa con distinto costo metabólico, empuja migración), variación estacional de la cantidad de comida.
4. **Mayor capacidad de interacción**: hoy el panel de control permite ajustar población/velocidad/mutación/comida; se podría sumar poder click-clickear una criatura específica en el visual para ver su genoma/neuronas en un panel de inspección, en vez de solo agregados poblacionales.

Nada de esto implementado todavía — es la cola de ideas para las próximas sesiones, priorizada según lo que el usuario indique.

### 11.6 Experimento: ¿sembrar con población "madura" ayuda a reproducirse más? (resultado mixto)

Usando el checkpointing nuevo: guardé una población tras 8000 ticks de corrida normal (`ckpt_mature.json`, 19 individuos, 15.8% con `incubadora` — de hecho por debajo del promedio base de ~23%, pura casualidad de esa corrida) y comparé arrancar una corrida nueva sembrada con ese checkpoint vs. una corrida control desde cero, ambas por 8000 ticks más:

- **Sembrada**: alcanzó generación 2, con 19 nacimientos totales.
- **Control (desde cero)**: se quedó en generación 1, pero con 30 nacimientos totales — más eventos de reproducción, aunque menos profundos.

Sin señal clara a favor de sembrar. Motivo probable: un checkpoint tomado "a lo que sea que esté vivo en ese momento" no es lo mismo que un checkpoint de "los que mejor se reprodujeron" — es solo una muestra de supervivientes al azar, no necesariamente enriquecida en el rasgo que nos interesa (incubadora cableada + bien alimentados). Para que este experimento tenga sentido real, habría que filtrar el checkpoint a los individuos con mejor `pct_incubadora_wired`/mayor longevidad antes de guardarlo, no guardar la población entera tal cual quedó.

**Segundo intento, con checkpoint filtrado** (`World.save_successful_population()`, solo incubadora cableada + mínimo de bloques): de una corrida de 8000 ticks, apenas **2 individuos** calificaron como "exitosos" — la semilla quedó chica de entrada. Repetí la comparación (8000 ticks más cada una):

- **Sembrada (2 exitosos)**: generación 4 recién en tick 7000, con 42 nacimientos totales.
- **Control (desde cero)**: generación 4 ya en tick 5000 (más rápido), con 49 nacimientos totales en todo momento — consistentemente por delante.

**Conclusión (dos intentos, misma dirección)**: sembrar con una población reducida de "exitosos" no ayudó, y en este caso el control fue más rápido y prolífico. Hipótesis para explicarlo: una semilla de solo 2 individuos reduce la diversidad genética inicial (menos variantes de umbral/cableado para que la selección elija), mientras que arrancar 100% al azar con `min_population=20` genera 20 variantes distintas desde el tick 0 — más "tiros de dados" en paralelo desde el principio le gana a partir de pocos "buenos" candidatos. Si se quisiera reintentar esto con más rigor, convendría sembrar con una población GRANDE de exitosos (no 2), lo cual requeriría correr muchísimo más tiempo para acumular suficientes candidatos que califiquen — no se hizo por límite de tiempo de esta sesión.

### 11.7 Ciclo día/noche (implementado)

`World.is_daytime()` — 500 ticks por ciclo completo, mitad día/mitad noche. El `generador` solo produce energía (y consume grasa) de día; de noche no hace nada (no desperdicia grasa intentando y fallando). Fondo del visual cambia de gris oscuro a azul noche según la fase. Verificado el efecto real: energía neta promedio **+2.06/tick de día** vs. **-1.33/tick de noche** en una corrida de 2000 ticks — el ciclo tiene impacto de comportamiento real, no es solo cosmético.

Bug encontrado y arreglado durante la implementación (Aider): el método `is_daytime()` quedó insertado accidentalmente **en medio de `World.__init__`**, cortando la inicialización a la mitad — `fat_levels`, `generation` y el resto de los atributos posteriores nunca se creaban, crasheaba en el primer tick. Confirma el patrón ya visto en esta sesión: conviene revisar con cuidado cada entrega de Aider, incluso cuando el mensaje de commit suena razonable.

### 11.8 Revisión completa de código (madrugada, sin bugs graves nuevos)

Lectura íntegra de `world.py` (512 líneas) tras varias sesiones de agregados (día/noche, linaje, checkpointing) buscando específicamente la clase de bug de la sección 10.6 (estado en vivo desincronizado del genoma heredable) y otros descuidos. No se encontró ningún bug de esa clase en ningún otro lado — el único punto de mutación de bloques/conexiones (`Creature.remove_block`) ya está corregido. Único hallazgo: `incubadora_wired` estaba duplicado (una vez como método de `World`, otra como función anidada idéntica dentro de `log_summary`) — solo cosmético, deduplicado.

Estado general del código a esta altura: estable en corridas repetidas de 500-800 ticks, sin crashes conocidos pendientes.

### 11.9 Zonas de temperatura (implementado)

`Physics.temperature_at(x,y)` — dos focos calientes en (25,25) y (75,75) del mapa de 100x100 (temp=3.0 en el centro de cada foco, ~1.0-1.3 en zonas frías/lejanas). El costo de mantenimiento total de cada criatura se multiplica por la temperatura de su posición actual — estar cerca de un foco caliente sale más caro de sostener, en teoría empujando migración hacia zonas frías (todavía no verificado si esto se traduce en comportamiento real, dado que el movimiento intencional sigue siendo poco frecuente). Visualizado en el modo visual como un mapa de calor de fondo (grilla 10x10, azul→naranja).

**Mismo patrón de bug que el ciclo día/noche**: el commit de Aider dejó `temperature_at()` definida pero **nunca la aplicó** al costo real (a pesar de que el mensaje del commit decía "ajustar cálculo de costo considerando temperatura"), y nunca agregó la visualización pedida — encima con código muerto duplicado dentro del método por un corte/pegado mal hecho (mismo tipo de error que truncó `__init__` en el día/noche). Las tres piezas faltantes se completaron a mano. Van dos features seguidas de Aider con el mismo patrón de "el mensaje de commit describe más de lo que el código realmente hace" — vale la pena, de acá en más, verificar explícitamente que cada pieza pedida esté realmente presente en el diff, no solo que el código corra sin crashear.
