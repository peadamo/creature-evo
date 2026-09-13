# Protocolo de coordinación multi-modelo

Leer esto al arrancar cualquier sesión de Claude Code sobre este proyecto, sea cual sea el modelo que la esté corriendo. El objetivo es minimizar gasto de tokens de Cloud sin frenar el avance del proyecto.

## Jerarquía de costo/capacidad (de más barato a más caro)

1. **Ollama local (qwen2.5-coder:32b vía Aider, o consulta directa vía API para análisis/texto)** — gratis en tokens de Cloud, pero más lento en tiempo real. Preferir siempre que la tarea lo tolere, sobre todo cuando el usuario no está presente (de noche, ausente).
2. **Haiku** — el más barato de los modelos de Cloud, coordinador principal. Corre la sesión por defecto.
3. **Sonnet** — intermedio en costo/capacidad.
4. **Opus** — el más caro y capaz. Reservar para lo genuinamente difícil.
5. **Fable** — evaluar caso por caso si vale la pena habilitarlo (no usado todavía en este proyecto).

## Regla general

**Escribir código real (ediciones de archivos) va primero a Aider (Ollama local), no a ningún modelo de Cloud.** Un modelo de Cloud (Haiku/Sonnet/Opus) solo edita un archivo directamente cuando el cambio es trivial (1-3 líneas, obvio) o cuando Aider ya falló una vez en exactamente esa misma tarea.

## Cuándo escalar a un modelo más caro

- **Haiku → Sonnet**: cuando la tarea requiere entender una cadena de bugs interrelacionados, diseñar un cambio de arquitectura no trivial, o revisar un diff de Aider que toca varios archivos a la vez y el riesgo de dejar pasar un bug es alto.
- **Sonnet → Opus**: cuando el problema es genuinamente ambiguo, requiere razonamiento profundo sobre trade-offs de diseño (ej. rediseño del ciclo de vida del huevo, decisiones de balance con múltiples variables interactuando), o cuando Sonnet ya intentó una vez y no llegó a una solución sólida.
- **Mecanismo técnico**: usar la herramienta `Agent` con el parámetro `model` (`haiku`/`sonnet`/`opus`) para lanzar un subagente en el modelo que corresponda, dentro de la misma sesión — no hace falta cambiar de conversación. El subagente devuelve su resultado al coordinador, que sigue al mando.
- No escalar "por las dudas" — si la tarea es rutinaria (chequeo de estabilidad, commit, documentar un hallazgo), se queda en el modelo que está corriendo la sesión.

## Uso de Ollama para pensamiento (no solo código)

Los modelos locales de Ollama no son solo para Aider/programar — sirven para consultas de texto/análisis directas (`ollama run <modelo> "pregunta"` o la API en `http://127.0.0.1:11434`), sin gastar tokens de Cloud. Útil para brainstorming, análisis filosófico/conceptual de bajo riesgo, o cualquier pregunta donde una respuesta "más lenta pero gratis" sea aceptable.

**Importante — aprendido en esta sesión**: no correr Aider y una consulta de Ollama en simultáneo (compiten por la misma VRAM, se ralentizan mutuamente). Secuenciar, no paralelizar, salvo que la placa tenga margen de sobra.

**Importante — costo real del navegador**: usar el navegador para consultarle algo a un modelo externo (Gemini vía Google, ChatGPT, etc.) tiene un costo de tokens de Cloud propio (cada click/screenshot/lectura de página es una llamada de herramienta) que puede terminar siendo **más caro** que simplemente responder la pregunta directamente, sobre todo para preguntas cortas. Reservarlo para casos donde de verdad se necesite el conocimiento/opinión externa y no una respuesta rápida.

## Rol del usuario

El usuario es la voz conceptual, ética y de diseño del proyecto — no aporta código ni decide implementación técnica en detalle, aporta dirección, hipótesis, y criterio de qué vale la pena explorar. El equipo de agentes (Haiku coordinador + Aider programador + escalamiento a Sonnet/Opus cuando haga falta + Ollama para pensamiento gratis) es responsable de la ejecución técnica.

## Contexto del proyecto

Ver [`docs/HANDOFF.md`](HANDOFF.md) para el estado actual, decisiones pendientes, y setup del entorno. Ver [`docs/design.md`](design.md) para el historial técnico completo (bugs encontrados, experimentos, hallazgos).
