# Handoff — leer esto primero en una sesión nueva

Este documento es el punto de entrada rápido. El historial completo, detallado, de todo lo que se probó/rompió/aprendió está en [`docs/design.md`](design.md) — este archivo es solo un resumen de orientación para no tener que leer todo de una.

## Qué es este proyecto

Simulación de vida artificial en 2D: criaturas hechas de bloques modulares (cuerpo) con un cerebro distribuido (red neuronal cuyas neuronas están ancladas a cada bloque físico), que evolucionan por selección natural — sin diseño manual del comportamiento. Objetivo filosófico del usuario: que el sistema termine cumpliendo criterios biológicos de "vida" (metabolismo, reproducción, adaptación) sin ser biología, como argumento contra la idea de que esas propiedades requieren biología real.

## Setup del entorno (ya hecho, no repetir)

- Repo: `C:\Users\peada\Documents\creature-evo`, remoto en `https://github.com/peadamo/creature-evo.git`, rama `main`.
- Motor local de programación: **Aider + Ollama**, modelo `qwen2.5-coder:32b` (el de 14b se probó y es inútil para esto — no aplica ediciones, solo repite el archivo).
- Comando típico para delegar una tarea a Aider (siempre desde la raíz del repo):
  ```
  OLLAMA_API_BASE=http://127.0.0.1:11434 aider --model ollama/qwen2.5-coder:32b --yes-always --message "..."
  ```
- Correr la simulación: `python -m sim.main <ticks>` (headless) o `python -m sim.main --visual` (ventana, sin límite de ticks si se omite el número).
- `pip install -r requirements.txt` si hace falta (numpy, pygame, matplotlib).

## Flujo de trabajo establecido (pedido explícito del usuario)

1. **Priorizar tokens de Claude al máximo.** Delegar el trabajo de código real a Aider en vez de editar archivos directamente — reservar ediciones directas de Claude para fixes triviales (1-3 líneas) o cuando Aider ya falló una vez en lo mismo.
2. **Aider deja cosas a medias con frecuencia** — patrón repetido varias veces en esta sesión: el mensaje de commit describe más de lo que el código realmente hace, o inserta código en el lugar equivocado (ej. un método pegado en medio de `__init__`, cortándolo). **Siempre revisar el diff completo y correr `python -m sim.main 500` al menos 3 veces (con tracebacks completos, no resúmenes) antes de dar por buena una entrega de Aider.**
3. No correr Aider y consultas a modelos locales en simultáneo — compiten por la VRAM (16GB, 4080 Super) y se ralentizan mutuamente.
4. Para preguntas cortas de análisis/opinión, NO vale la pena usar el navegador para consultar Gemini/ChatGPT — el overhead de tool calls (screenshots, clicks) sale más caro en tokens de Claude que simplemente responder directo. El navegador solo se justificó una vez, como demostración, y se concluyó que no conviene para preguntas cortas.
5. El usuario quiere reportes de "curiosidades" — bugs raros, patrones de comportamiento emergente interesantes — no solo el resultado técnico.
6. Respuestas de chat: tono terso, directo, sin relleno.
7. No agregar nueva dificultad ambiental (temperatura, clima, etc.) hasta que el ciclo básico de supervivencia/reproducción funcione bien — evitar que quede como "sopa primordial" que nunca progresa. La penalización de temperatura ya implementada está **desactivada a propósito** (código queda, efecto comentado).

## Estado funcional actual (ver design.md sección 8-12 para el detalle completo)

Implementado y funcionando: bloques modulares con neuronas propias, red integrate-and-fire con umbral/fuga evolutivos, motores de impulso con física de inercia real, sonar (criaturas + comida), combate por contacto con selección de bloque objetivo y HP por bloque, sistema de energía/grasa con capacidad limitada por bloque `almacenamiento`, reproducción vía huevos (incubadora) con bonus de energía al poner huevo, ciclo día/noche, índice espacial (grilla) para performance, checkpointing (guardar/cargar poblaciones), tracking de linaje/generación, panel de control visual con sliders, script de reportes gráficos (`sim/report.py`).

Bugs importantes ya resueltos (no repetir el diagnóstico si vuelven a aparecer síntomas parecidos): sonar ciego de nacimiento, banco neuronal mal calibrado (casi nunca disparaba), bugs de progreso/orfandad de huevos, conexión colgante heredable al perder un bloque en combate (`remove_block` no sincronizaba `genome.connections`), ventaja de "muerte cerebral" (parcialmente corregida con costo tisular mínimo), varios casos de "Aider dejó el feature a medias".

## Decisiones de diseño tomadas, pendientes de implementar

1. **`incubadora` debe ser un bloque garantizado al nacer** (junto con boca/generador/actuador/sonar) — sin él, la criatura nunca puede reproducirse, no tiene sentido simularla. Decidido, no implementado todavía.
2. **Rediseño del ciclo de vida del huevo** (ver design.md sección 13): costo escalado por tamaño genético del hijo (`capacidad_huevo = base + K × cantidad_de_bloques`), dos fases (interno/externo), la madre puede largarlo en cualquier momento pero antes del 50% de desarrollo se pierde si no está "adentro" — se decidió que el umbral de viabilidad sea **50%**, no 80% (favorece diversidad de estrategias: madres "negligentes" vs "abnegadas"). Falta decidir: tasa de crecimiento autónomo de un huevo ya externo y viable.
3. **Banco neuronal ya no está protegido** de la mutación que quita bloques — una criatura puede evolucionar a "vivir sin cerebro" (reflejo puro, sensor cableado directo a un actuador) — ya verificado que el motor lo soporta sin crashear.
4. **Propuesta en discusión, sin decidir**: dividir `sonar` en dos bloques (`radar_criaturas` y `radar_comida`) en vez de uno solo con ambas señales mezcladas.
5. Números recién ajustados (banco 5→8 neuronas, cableado inicial duplicado, tasa de mutación de conexiones proporcional al tamaño del genoma ~5%) — implementados y probados, ver si con más tiempo de corrida esto mejora la tasa de reproducción sostenida (todavía no se corrió una prueba larga con estos cambios).

## Próximo paso sugerido

Implementar el punto 1 (incubadora garantizada) es chico y rápido. El rediseño del huevo (punto 2) es más grande, conviene dispatchearlo a Aider en una tarea bien acotada citando exactamente los números de design.md sección 13 una vez que estén definidos del todo.
