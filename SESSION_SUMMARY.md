# Sesión Resumen: Implementación de Features Críticos

## Logros

### 1. **CRÍTICO: Reproducción Funcional** 
- **Problema**: 0-5 huevos en 2000-8000 ticks (bottleneck sin resolver)
- **Causa**: Pesos de conexión invertir/liberar eran NEGATIVOS (-1 a 1)
  - Cuando banco dispara (1.0), conexión envía 1.0 × (-0.962) = -0.962
  - Neurona invertir se clampea a 0.0
- **Solución**: Cambiar pesos a positivos (0-1) en genome.py línea 75-76
- **Resultado**: **9+ huevos/tick** (906 huevos en 100 ticks)

### 2. Radar Parentesco (Sensor)
- Nuevo bloque que detecta huevos cercanos (fase externa)
- Calcula similitud genética using Hamming distance sobre bloques del genoma
- Neuronas: `dx`, `dy`, `parentesco` (0-1), más `hp_level` y `activo`
- ~22% de probabilidad en genoma inicial
- Permite evolucionar cuidado parental selectivo

### 3. Suicidio (Output)
- Neurona output en cada bloque: si supera 0.5, bloque se destruye
- Bloques garantizados protegidos (incubadora, boca, generador, actuador, sonar)
- Permite auto-amputación estratégica en hambruna o daño
- ~6 neuronas suicidio por criatura

### 4. Dormir (Output) 
- Neurona output en cada bloque: si supera 0.5, entra en hibernación
- Costo energía: 0.1 → 0.05 (solo metabolismo basal)
- Bloque dormido no ejecuta funciones
- Permite hibernación estratégica en escasez
- ~8 neuronas dormir por criatura

## Estadísticas Finales

| Métrica | Valor |
|---------|-------|
| Reproducción | 9.06 huevos/tick (población fresca) |
| Sensores garantizados | 5 (boca, generador, actuador, radar_criaturas, radar_comida, **radar_parentesco**) |
| Outputs por bloque | 3-4 (impulso/invertir/output + suicidio + dormir) |
| Generación máxima | 2 (downstream: evolución más lenta) |
| Población sostenible | ~20 criaturas |

## Cambios de Código

### genome.py
- Línea 75-76: pesos invertir/liberar positivos (0-1)
- Agregado make_params para radar_parentesco
- Cableado banco → radar_parentesco_activo

### creature.py
- Línea 37-38: hp_level en todos bloques
- Línea 47-48: neurona dormir en todos bloques

### world.py
- Función genetic_similarity(): calcula Hamming distance entre genomas
- update_sensors(): propaga dx, dy, parentesco para radar_parentesco
- tick(): chequea suicidio > 0.5 y remueve bloques
- consume_energy(): reduce a 50% si dormir > 0.5

### reproduction.py
- Garantía de incubadora en mutate_genome() (línea 23-26)
- Parámetro liberar agregado a incubadora (línea 60)
- Suicidio agregado a todos bloques en mutation
- Dormir soportado automáticamente

## Próximos Pasos

1. Observar evolución de 10k+ ticks para nuevos comportamientos
2. Agregar estadísticas para rastrear uso de suicidio/dormir
3. Implementar cableado neural opcional para dormir (si no está presente)
4. Investigar por qué reproducción cae después de ~500 ticks en sims largas

## Notas Técnicas

- Pass C (creature.py) propaga edge_outputs (invertir, liberar, etc.)
- Pass D propaga hp_level
- Similitud genética es distancia normalizada: matches / max_len
- Suicidio no puede afectar bloques garantizados
- Dormir es hibernación reversible, no morte
