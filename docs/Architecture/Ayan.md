# Ayan

Ayan — Frontend Lead + Circuit Builder

Goal: Build the entire user-facing quantum circuit experience.

The roadmap assigns P1 the circuit builder and visualization deliverables.

P1 should build
1. Circuit Builder

Using React Flow:

Gate Palette
 ├── H
 ├── X
 ├── Y
 ├── Z
 ├── CNOT
 ├── Toffoli
 └── Measurement

Student should be able to:

Drag H → Qubit 0
Drag CNOT → Qubit 0/Qubit 1
Remove gate
Move gate
Clear circuit
Run circuit
2. Circuit visualization

Build:

Circuit diagram
Gate rendering
Qubit wires
Measurement visualization
3. Bloch sphere

Use Three.js / React Three Fiber.

4. Probability visualization

Example:

00 █████████████████ 50%
11 █████████████████ 50%
5. State vector display

Example:

|ψ⟩ = 0.707|00⟩ + 0.707|11⟩
P1's deliverable

By integration:

Student
   ↓
Open Builder
   ↓
Drag gates
   ↓
Circuit generated
   ↓
Click RUN
   ↓
Send circuit JSON → Backend