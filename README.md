# creature-evo

2D physics-based artificial life simulation. Creatures with an evolvable body (morphology) and an evolvable neural network brain compete, survive, and reproduce under environmental pressure, using GPU compute for parallel simulation and evaluation.

## Goal

Explore whether an open-ended body+brain co-evolution system can satisfy the biological criteria commonly used to define "life" (metabolism, homeostasis, reproduction, adaptation, response to environment) — as a concrete, running counterexample to claims that these are exclusively properties of biological organisms.

## Status

Working CPU prototype in `sim/` (numpy + pygame). See [docs/design.md](docs/design.md) section 8 for the living roadmap: what's implemented, what's designed but pending, and the backlog of conceptual ideas.

Run it: `python -m sim.main <ticks>` (headless) or `python -m sim.main <ticks> --visual` (pygame window).

## Stack (planned)

- Simulation core: Python + GPU compute (Taichi or NVIDIA Warp) targeting an RTX 4080 Super
- Evolution: genetic algorithm, NEAT-style — genome encodes both body morphology and neural network topology
- Local coding agent: Aider + Ollama (qwen2.5-coder:32b) for implementation, coordinated by design docs in `docs/`

## Layout

- `docs/` — design docs, including the living roadmap in `docs/design.md`
- `sim/` — simulation engine (genome, creature/brain, physics, energy, reproduction, world loop, render)
