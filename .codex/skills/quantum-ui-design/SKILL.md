---
name: quantum-ui-design
description: Visual design and motion system for the Quantum Learning Platform. Use for frontend UI implementation, redesigns, animation, scroll-driven scenes, quantum visualizations, 3D/WebGL presentation, typography, materials, responsive behavior, performance, and accessibility.
---

# Quantum Learning Platform — Visual Design & Motion Skill

## Purpose

This skill defines the visual language, interaction model, motion system, and implementation constraints for the Quantum Learning Platform.

The platform should **not** look like a generic SaaS dashboard, conventional university LMS, or stereotypical “AI/quantum” website filled with purple gradients.

The intended identity is:

> **Retro-futuristic quantum computing presented through a cold, mysterious, experimental visual system inspired by early-2000s futuristic CGI, industrial hardware, chrome, glass, pixel typography, halftone graphics, probability fields, and cinematic scroll-driven motion.**

The goal is not to imitate a particular website. The goal is to build a distinct visual language that feels like:

> **“straight from the 2000s, but somehow far more futuristic.”**

The design must remain usable as a learning platform. Visual intensity should support comprehension rather than obscure it.

---

# 1. Core Design Philosophy

## 1.1 Primary principles

1. **Quantum concepts are visual phenomena, not decorative labels.**
2. **Motion should explain something whenever practical.**
3. **The interface should feel physical, dimensional, and tactile.**
4. **Large areas of darkness are intentional.**
5. **Color is a signal, not wallpaper.**
6. **Typography is part of the composition.**
7. **The platform should feel experimental, not messy.**
8. **The strongest visuals belong to major concepts, not every tiny UI element.**
9. **The experience should feel technologically advanced without becoming generic cyberpunk.**
10. **Readability always wins when visual spectacle conflicts with learning.**

---

# 2. Overall Aesthetic

## 2.1 Emotional target

The interface should feel:

- cold
- mysterious
- futuristic
- experimental
- technical
- precise
- slightly alien
- premium
- physical
- cinematic

It should create curiosity without becoming ominous or horror-like.

## 2.2 Aesthetic target

Use a blend of:

- retro-futurism
- industrial design
- Y2K-inspired CGI
- experimental graphic design
- scientific visualization
- futuristic hardware interfaces
- minimal monochrome editorial layouts
- subtle video-game UI influence

Do **not** make it a literal early-web parody.

The Y2K influence is about materials, composition, typography, CGI language, and visual experimentation rather than fake old website layouts.

---

# 3. Color System

## 3.1 Base palette

The default environment is near-black.

Suggested foundation:

```css
--bg-void: #030405;
--bg-near-black: #07090c;
--bg-metal: #11151a;
--surface-dark: #151a20;
--surface-elevated: #1b2229;

--text-primary: #f4f7f8;
--text-secondary: #aeb7bd;
--text-muted: #68747d;

--chrome-light: #e9eef0;
--chrome-mid: #9da8ae;
--chrome-dark: #4b555c;

--quantum-blue: #4da8ff;
--quantum-cyan: #67e8ff;
```

The exact values may change during implementation, but the relationship must remain:

**black / charcoal → silver / white → restrained electric blue/cyan**

## 3.2 Accent discipline

The visual system should be **almost entirely monochrome**.

Bright accents are intentionally scarce.

Use electric blue/cyan for:

- active quantum states
- selected circuit elements
- interactive feedback
- important data
- live simulation activity
- focused controls
- key transitions

Do not paint every button cyan.

Do not use a rainbow gradient unless a quantum concept specifically benefits from spectral visualization.

## 3.3 Concept-specific accent colors

Different quantum concepts may have a restrained secondary accent, but each concept should have a coherent identity.

Examples:

- Superposition: cyan / electric blue
- Entanglement: blue with occasional violet
- Measurement: white → blue collapse
- Interference: cyan with subtle magenta interference
- Grover: blue probability field
- Teleportation: cyan transmission path
- Shor overview: silver/blue computational geometry

These colors should appear primarily inside the visualization.

---

# 4. Material Language

The interface should have a clear material vocabulary.

## 4.1 Chrome

Chrome is a major visual material.

Use chrome for:

- hero objects
- featured controls
- large UI accents
- quantum hardware metaphors
- special navigation elements
- selected 3D objects

Chrome should use realistic/high-quality light variation rather than a cheap linear gradient.

## 4.2 Glass

Use dark translucent glass for:

- floating panels
- navigation overlays
- contextual controls
- simulation tools
- information cards

Suggested qualities:

- dark translucent base
- subtle blur
- thin border
- restrained highlight
- low-opacity reflection
- minimal shadow

Do not overuse glassmorphism.

Glass is for hierarchy, not every card.

## 4.3 Black plastic

Black plastic should appear in:

- hardware-inspired controls
- circuit-builder controls
- module interfaces
- retro-futuristic device metaphors

The surface can have subtle roughness and specular response.

## 4.4 Iridescence

Holographic / iridescent effects are permitted for special moments:

- quantum state transitions
- probability fields
- major section transitions
- featured 3D objects

Keep them subtle.

The platform should never become a rainbow holographic shopping website.

## 4.5 Y2K translucency

Use translucent plastic-inspired UI sparingly:

- pill controls
- small utility widgets
- segmented controls
- special toggles
- floating labels

Avoid chunky bubble UI.

---

# 5. Typography

## 5.1 Typography system

Use a combination of:

### Primary UI font

A clean, modern, highly readable sans-serif.

Use for:

- body text
- navigation
- buttons
- explanations
- metadata
- learning content

### Secondary technical font

A restrained monospace or technical typeface.

Use for:

- circuit labels
- qubit identifiers
- coordinates
- simulation values
- code
- technical metadata
- small system annotations

### Display / pixel font

Use selectively for major titles and visual moments.

It may appear in:

- hero typography
- section markers
- algorithm names
- experimental labels

Do not use the pixel font for paragraphs.

## 5.2 Typography composition

Typography can be highly experimental.

Allowed:

- oversized words
- unusual line breaks
- offset labels
- vertical labels
- pixelated display text
- large numerical indicators
- small technical annotations
- overlapping text and visual objects

But every experimental choice must remain readable.

## 5.3 Heading behavior

Major headings can behave like artwork.

Examples:

```text
Q U A N T U M

COMPUTING
```

or:

```text
QUANTUM
        STATES
```

or:

```text
SUPER
POSITION
```

Use typography as part of the composition instead of treating it as an ordinary heading.

---

# 6. Layout System

## 6.1 Negative space

Large empty areas are intentional.

Do not fill every region.

The platform should frequently have:

- a black void
- one dominant object
- one large typographic statement
- sparse supporting UI

This creates the cinematic feel.

## 6.2 Asymmetry

Favor asymmetric compositions.

Do not center every section.

Use:

- objects offset from center
- typography pushed to an edge
- floating technical labels
- asymmetric grids
- overlapping layers
- large unused regions

## 6.3 Depth

Build pages in layers:

```text
Background field
    ↓
Ambient particles / texture
    ↓
Large environmental geometry
    ↓
Primary 3D object
    ↓
Typography
    ↓
Interactive UI
    ↓
Micro-details
```

The depth should remain clear.

---

# 7. Background System

The background is a major part of the experience.

It should never be a static color block across the entire platform.

## 7.1 Background ingredients

Use a carefully layered combination of:

- near-black base
- animated particles
- quantum probability fields
- halftone dot matrices
- interference waves
- subtle grain/noise
- faint geometry
- occasional light streaks
- sparse glowing nodes
- mathematical or circuit-like structures

Not every layer should be active at the same time.

## 7.2 Probability fields

Probability fields can be represented using:

- particle density
- soft volumetric clouds
- dot density
- procedural noise
- flowing vector fields
- luminous point distributions

The field should respond subtly to interaction when appropriate.

## 7.3 Halftone fields

Halftone patterns are a signature visual element.

Use them for:

- probability distributions
- object silhouettes
- section transitions
- atmospheric structures
- abstract quantum visualizations

Avoid simply placing a static dot-pattern PNG behind everything.

Prefer procedural or dynamically animated fields where practical.

## 7.4 Interference waves

Interference should appear as:

- layered wave patterns
- shifting contour lines
- intensity bands
- interference fringes
- particle accumulation zones

Animation should remain smooth and physically suggestive.

---

# 8. Mouse Interaction

The background should react **slightly** to the pointer.

Examples:

- particle field shifts toward pointer
- subtle parallax
- a probability cloud bends slightly
- object lighting follows cursor
- halftone field deforms a few pixels
- glass reflections change with pointer position

Never allow cursor interaction to destroy the composition.

Avoid exaggerated “everything follows my mouse” effects.

---

# 9. Scroll-Driven Cinematic System

## 9.1 Fundamental principle

Scrolling should control visual progression.

The preferred experience is:

```text
scroll position
    ↓
scene state
    ↓
camera / object transform
    ↓
visual transformation
    ↓
educational concept
```

The platform should feel as though the user is moving through an interactive scientific installation.

## 9.2 Example scene progression

```text
0%
    Object appears in darkness

20%
    Object rotates
    Ambient particles activate

40%
    Object begins dissolving

60%
    Particles form a probability field

75%
    Field becomes a quantum circuit

90%
    Circuit becomes the next concept

100%
    Transition into learning content
```

This is the target level of ambition for major landing-page sections.

## 9.3 Scroll should control

Possible scroll-linked properties:

- camera position
- object rotation
- object scale
- object position
- opacity
- particle density
- particle velocity
- field intensity
- typography position
- light intensity
- depth / parallax
- distortion amount
- circuit construction
- section reveal progress

## 9.4 Scene transitions

Prefer transformations over hard cuts.

Examples:

```text
3D hardware
    →
chrome fragment
    →
particle cloud
    →
probability distribution
    →
quantum circuit
```

This should feel like one visual idea becoming another.

---

# 10. Landing Page

## 10.1 Hero objective

The hero must communicate **quantum computing immediately** while still feeling mysterious and artistic.

The first visual should contain:

- a strong quantum visual
- an animated field or object
- high-impact typography
- sparse interface
- strong negative space

## 10.2 Hero composition

Use an asymmetric full-screen composition.

Possible structure:

```text
------------------------------------------------
|                                              |
|   QUANTUM                                   |
|        COMPUTING            [3D OBJECT]      |
|                                              |
|                probability field             |
|                                              |
|  SCROLL TO EXPLORE                           |
------------------------------------------------
```

The actual composition can vary.

## 10.3 Hero animation

The hero should be alive immediately.

Animation can include:

- very slow object rotation
- subtle camera movement
- moving particle field
- breathing light
- halftone displacement
- microscopic grain movement
- text reveal

The motion should feel expensive, not frantic.

---

# 11. Educational Module Design

Visual drama belongs primarily to major concepts.

## 11.1 Learning section structure

A lesson can use:

```text
SECTION TITLE
      ↓
concept introduction
      ↓
interactive visual
      ↓
short explanation
      ↓
interactive exploration
      ↓
knowledge check
```

## 11.2 Major concept scenes

Each major concept should have a visual centerpiece.

Examples:

### Superposition

A single qubit can be represented as:

- a field
- a rotating state object
- a probability cloud
- layered wave geometry

Interaction changes the visual state.

### Entanglement

Two objects/nodes should become visibly correlated.

Interaction with one should visibly influence the representation of the other.

### Measurement

The system begins as a distributed probability representation and transitions into a definite observed outcome.

The transition should be visually obvious but not misleading.

### Interference

Use moving wave surfaces or particle-density patterns to demonstrate constructive and destructive interference.

---

# 12. 3D Object Language

## 12.1 Object style

3D objects should combine:

- glossy Y2K CGI
- metallic realism
- dark industrial hardware
- scientific instrumentation
- abstract quantum forms

The result should feel manufactured but futuristic.

## 12.2 Appropriate objects

Use:

- chrome quantum processors
- abstract qubit devices
- physical-looking gates
- cryogenic hardware-inspired forms
- metallic nodes
- glass probability volumes
- abstract particles
- futuristic scientific instruments

## 12.3 Object placement

Do not put a 3D object in every card.

3D should be reserved for:

- hero
- major learning concepts
- major algorithm scenes
- section transitions
- circuit-builder centerpiece

---

# 13. Quantum Circuit Builder

The builder should feel like a **Y2K futuristic computer interface crossed with a video game instrument panel**.

## 13.1 Visual structure

Use:

- dark background
- glass/metal panels
- glowing circuit paths
- metallic/glass gates
- technical labels
- pixel or monospace annotations

## 13.2 Gate appearance

Gates may use:

- glass
- metallic surfaces
- subtle glow
- pixel/Y2K labels
- physically inspired depth

Use a restrained combination instead of making every gate visually noisy.

## 13.3 Circuit execution animation

The circuit execution must remain **extremely subtle**.

Preferred sequence:

```text
Gate activation
    ↓
small energy pulse
    ↓
pulse travels along wire
    ↓
linked qubit responds
    ↓
result updates
```

The pulse should be visually satisfying but never distract from the actual circuit.

## 13.4 Interaction feedback

When a gate is:

- hovered → subtle glow / depth change
- selected → stronger outline
- dragged → physical lift
- placed → short snap animation
- executed → small state response

---

# 14. Motion System

## 14.1 Overall motion intensity

Target: **10/10 visual ambition, but balanced implementation.**

The site can contain lots of animation, but not every element should constantly move.

Use:

- slow environmental motion
- medium UI motion
- fast event-driven feedback
- scroll-driven cinematic sequences

## 14.2 Motion character

Primary motion language:

> **smooth, Apple-like physical motion applied to experimental Y2K/quantum visuals**

Use:

- spring-like easing
- smooth interpolation
- inertia
- subtle overshoot
- acceleration/deceleration
- physical object movement

Avoid:

- random bouncing
- excessive elastic effects
- perpetual spinning
- generic ease-in-out on everything
- decorative animation with no hierarchy

## 14.3 Motion hierarchy

### Ambient

Very slow.

Examples:

- particle drift
- light movement
- grain
- field movement

### Interaction

Fast enough to feel responsive.

Examples:

- hover
- click
- drag
- focus

### Cinematic

Longer and strongly tied to scroll.

Examples:

- object transformation
- field formation
- section transitions

### State change

Short and clear.

Examples:

- gate execution
- measurement
- quiz feedback
- simulation result

---

# 15. Hover Design

Hover interactions may:

- glow
- distort
- physically lift
- rotate slightly
- change reflective lighting
- reveal information
- alter particle behavior

Keep the displacement small.

The interface should feel tactile without becoming slippery.

---

# 16. Page Transitions

Do not rely on elaborate page-transition effects.

The chosen visual direction prefers **strong section-level transformations** over theatrical route changes.

For normal navigation:

- fast fade
- slight blur
- subtle movement
- preserve orientation

Save cinematic transitions for major experiential moments.

---

# 17. Texture System

Textures are encouraged.

Use:

- film grain
- low-resolution noise
- CRT scanlines
- subtle screen texture
- halftone dots
- brushed metal
- roughness variation

Textures should be subtle enough that text remains crisp.

Never apply heavy CRT distortion to educational text.

---

# 18. Responsive Design

Mobile should preserve the visual identity.

Desktop can use:

- heavy WebGL
- large 3D scenes
- full-screen scroll choreography
- layered composition

Mobile should simplify intelligently rather than simply shrinking desktop.

## 18.1 Mobile fallbacks

On smaller screens:

- reduce particle counts
- reduce 3D polygon complexity
- reduce blur
- simplify scene transformations
- preserve key objects
- preserve major typography
- keep the black/metal visual identity
- maintain scroll-driven storytelling where possible

Do not remove the visual identity entirely.

---

# 19. Performance

The visual ambition is high, but performance must remain controlled.

## 19.1 Performance priorities

Prioritize:

1. interaction responsiveness
2. text readability
3. scroll smoothness
4. learning content availability
5. visual fidelity

## 19.2 Techniques

Use appropriate:

- GPU-accelerated transforms
- requestAnimationFrame
- lazy-loaded 3D assets
- adaptive particle counts
- intersection-based scene activation
- reduced DPR where appropriate
- texture compression
- progressive loading
- scene disposal
- object pooling
- instancing for repeated particles

Do not keep every WebGL scene active simultaneously.

## 19.3 Scene lifecycle

Major animated scenes should:

- initialize when entering the relevant section
- pause when far outside the viewport
- dispose resources when no longer needed
- avoid duplicate render loops

---

# 20. Accessibility

Respect `prefers-reduced-motion`.

When reduced motion is enabled:

- disable large camera movements
- reduce particle motion
- replace scroll-controlled 3D movement with opacity/position changes
- remove strong distortions
- preserve information
- preserve interaction
- maintain visual hierarchy

Do not make the reduced-motion experience feel broken.

---

# 21. Visual Do / Don't

## DO

- use black space confidently
- make important objects feel physical
- use chrome deliberately
- use cyan/blue sparingly
- use halftone fields
- create animated probability distributions
- use scroll as a storytelling mechanism
- make typography visually interesting
- make quantum concepts visually transform
- create tactile UI feedback
- combine modern usability with retro-futuristic materials

## DON'T

- generic purple AI gradients
- generic neon cyberpunk grids
- excessive glassmorphism
- excessive rainbow gradients
- glowing everything
- giant rounded SaaS cards everywhere
- stock illustrations
- generic “quantum atom” clip art
- excessive floating blobs
- fake old-web layouts
- unreadable pixel-font body text
- animation that competes with educational content
- constant motion with no purpose
- huge shadows around every element
- overly rounded modern SaaS UI

---

# 22. Visual Anti-Patterns

Reject designs that look like:

### Generic AI SaaS

```text
purple gradient
rounded card
purple button
floating blob
Inter
“Unlock the future”
```

### Generic Cyberpunk

```text
black
neon magenta
neon cyan
wireframe city
random HUD
glitch everywhere
```

### Generic Quantum Website

```text
atom icon
purple sphere
particle dots
gradient background
“Explore Quantum”
```

The target should be more physical, artistic, and controlled.

---

# 23. Component Design Rules

## Buttons

Buttons should feel tactile.

Possible properties:

- metallic or dark-glass surface
- thin highlight
- subtle depth
- tiny hover lift
- restrained glow when active

Primary buttons should not dominate the entire page.

## Cards

Use cards only where they help organize information.

Cards may be:

- dark glass
- dark metal
- transparent layered panels

Not every section needs a card.

## Navigation

Navigation should be minimal and technically styled.

Possible details:

- small monospace metadata
- thin rules
- compact active indicators
- subtle glass panel
- tiny system labels

---

# 24. Microcopy and Labels

Small technical annotations can reinforce the aesthetic.

Examples:

```text
QUBIT 01
STATE: SUPERPOSITION
PROBABILITY: 0.50 / 0.50
```

or:

```text
SYSTEM / QUANTUM-03
SIMULATION READY
```

or:

```text
NODE 04
ENTANGLED
```

These labels are visual accents, not a replacement for clear educational explanations.

---

# 25. Scroll Section Blueprint

A major learning section can use this pattern:

```text
[1] ENTER
    black void
    title appears

[2] REVEAL
    3D object emerges

[3] INTERACT
    pointer subtly influences the scene

[4] TRANSFORM
    object becomes quantum visualization

[5] EXPLAIN
    supporting text becomes prominent

[6] EXPLORE
    user interacts with the concept

[7] RESOLVE
    visual settles

[8] CONTINUE
    next scene begins
```

This is the preferred cinematic structure.

---

# 26. Suggested Landing Page Story

A possible high-level flow:

## Scene 01 — Quantum

Black void.

A chrome quantum object slowly rotates.

Pixel/experimental typography introduces the platform.

Scroll begins.

## Scene 02 — States

The object breaks into particles.

Particles form a probability field.

A qubit state becomes visible.

## Scene 03 — Gates

Probability particles organize into a quantum circuit.

Gates construct themselves.

The user sees that gates are operations, not decorative symbols.

## Scene 04 — Entanglement

Two distant states become visibly connected.

A change in one representation influences the other.

## Scene 05 — Algorithms

The scene transitions into a more technical interface.

Deutsch-Jozsa, Grover, Teleportation, and Shor are introduced as distinct visual systems.

## Scene 06 — Build

The platform transitions into the circuit builder.

The user can construct a circuit.

## Scene 07 — Learn

The interface becomes quieter.

Content, explanations, quizzes, and practical exercises take priority.

This alternation between spectacle and clarity is important.

---

# 27. Educational Visualization Rules

The platform is educational, so visualizations must not imply scientifically incorrect behavior merely because the animation looks cool.

When a visualization is conceptual rather than physically exact, label it appropriately.

Prefer:

> “Conceptual visualization”

when needed.

Avoid presenting decorative animation as literal physical behavior.

The purpose of the visual layer is to make abstract quantum concepts easier to reason about.

---

# 28. Implementation Guidance

Use modern web tooling appropriate to the existing project.

For large visual scenes, consider:

- WebGL
- Three.js
- React Three Fiber
- procedural canvas rendering
- SVG for vector fields and diagrams
- CSS transforms for lightweight motion
- scroll-linked animation libraries where they fit the project

Choose the simplest technology capable of producing the desired result.

Do not introduce WebGL when CSS or SVG can achieve the same result at lower complexity.

## 28.1 Animation architecture

Prefer centralized animation/state control.

Avoid hundreds of unrelated timers.

Prefer:

```text
scroll progress
      ↓
scene controller
      ↓
derived visual states
      ↓
rendered components
```

This makes cinematic sequences easier to tune.

---

# 29. Design Tokens

Create reusable tokens for:

- background shades
- chrome levels
- glass opacity
- border opacity
- glow intensity
- motion duration
- easing curves
- spacing
- typography scale
- particle density
- scene intensity

Example:

```css
--motion-fast: 180ms;
--motion-ui: 320ms;
--motion-scene: 900ms;
--motion-cinematic: 1600ms;

--glow-subtle: 0.12;
--glow-medium: 0.24;
--glow-strong: 0.42;

--glass-opacity: 0.42;
--border-opacity: 0.18;
```

Exact values are implementation details and should be tuned visually.

---

# 30. Agent Behavior Rules

When implementing a new page or component:

1. First ask whether the element actually needs to exist.
2. Prefer one strong visual idea over five competing ideas.
3. Use the established material and color language.
4. Reuse existing animation primitives.
5. Reuse existing 3D/particle systems where possible.
6. Do not invent a new visual style for every page.
7. Keep educational content readable.
8. Ensure animations have hierarchy.
9. Test the scene at realistic viewport sizes.
10. Test reduced-motion behavior.
11. Test performance during scrolling.
12. Remove decorative animation that does not improve the experience.

---

# 31. Quality Bar

Before considering a page complete, verify:

### Visual

- Does it feel cold, mysterious, futuristic, and experimental?
- Is the black space intentional?
- Are materials convincing?
- Is the color restrained?
- Does the typography feel distinctive?
- Does the page avoid generic AI aesthetics?

### Motion

- Is the page alive?
- Do major scenes respond to scrolling?
- Are transformations smooth?
- Is interaction tactile?
- Does motion support the content?

### Educational

- Can users read everything?
- Does the visualization communicate the concept?
- Is conceptual animation clearly distinguished from literal simulation?
- Does visual spectacle ever overpower explanation?

### Technical

- Does scrolling remain smooth?
- Are WebGL resources managed correctly?
- Are scenes lazy-loaded?
- Does mobile remain usable?
- Does `prefers-reduced-motion` work?

---

# 32. Final Creative North Star

Every design decision should move toward this mental image:

> A mysterious black technological environment from an alternate version of the early 2000s, where quantum computing has become a physical design language. Chrome hardware floats in a void. Halftone probability clouds drift around it. Pixel typography and clean modern text coexist. Glass and black plastic controls feel manufactured. Quantum states appear as living fields. Circuits assemble themselves. Scrolling moves the camera through these transformations. Everything is highly animated, but nothing is animated merely because it can be.

The experience should make the user think:

> **“This looks like it came from the 2000s, but it somehow feels more futuristic than modern websites.”**

That is the target.
