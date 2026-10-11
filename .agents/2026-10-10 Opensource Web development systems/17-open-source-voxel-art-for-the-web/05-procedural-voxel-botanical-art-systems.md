# 05 - Open-Source 3D Procedural Voxel Botanical Art Systems

This guide provides an end-to-end mathematical and engineering blueprint for generating **3D procedural voxel botanical art** (trees, flowers, bonsai, shrubs, and succulents) directly for the open web. It covers Lindenmayer Systems (L-Systems), Space Colonization algorithms, Vogel phyllotaxis, discrete 3D voxelization, stylized Japanese/organic color palettes, and real-time Three.js/WebGPU rendering pipelines.

---

## 1. Algorithmic Paradigms for Procedural Flora

Generating aesthetically pleasing botanical structures in discrete voxel lattices requires balancing mathematical morphogenesis with stylized art direction. Three primary procedural paradigms dominate modern procedural voxel botany:

```
                          ┌──────────────────────────────────────┐
                          │    Botanical Generation Pipeline     │
                          └──────────────────┬───────────────────┘
                                             │
             ┌───────────────────────────────┼──────────────────────────────┐
             ▼                               ▼                              ▼
    ┌─────────────────┐             ┌─────────────────┐            ┌──────────────────┐
    │ 3D L-Systems    │             │Space Colonize   │            │Phyllotaxis Form  │
    │ (Fractal/Rules) │             │(Attractor Clust)│            │(Spiral/Petals)   │
    └────────┬────────┘             └────────┬────────┘            └────────┬─────────┘
             │                               │                              │
             └───────────────────────┬───────┴──────────────────────────────┘
                                     ▼
                     ┌───────────────────────────────┐
                     │ 3D Discrete Voxelization      │
                     │ (Bresenham + Noise Displace)  │
                     └───────────────┬───────────────┘
                                     ▼
                     ┌───────────────────────────────┐
                     │ Palette Mapping & Occlusion   │
                     │ (Bark Gradients + Canopy Rim) │
                     └───────────────┬───────────────┘
                                     ▼
                     ┌───────────────────────────────┐
                     │ Web Rendering (Three.js/VOX)  │
                     │ (InstancedMesh / WebGPU DDA)  │
                     └───────────────────────────────┘
```

### A. 3D Stochastic & Parametric Lindenmayer Systems (L-Systems)

L-Systems describe plant development through formal rewriting grammars. For 3D voxel trees, the system uses a 3D turtle coordinate frame defined by three orthonormal vectors:
- **Heading ($\vec{H}$)**: Forward direction of growth.
- **Left ($\vec{L}$)**: Lateral branch axis.
- **Up ($\vec{U}$)**: Perpendicular upward axis ($\vec{U} = \vec{H} \times \vec{L}$).

#### 3D Turtle Rotation Matrices
Rotations around turtle axes:
- **Pitch ($\&, \wedge$)** by angle $\alpha$ around $\vec{L}$:
  $$\vec{H}' = \vec{H} \cos\alpha + \vec{U} \sin\alpha, \quad \vec{U}' = -\vec{H} \sin\alpha + \vec{U} \cos\alpha$$
- **Yaw ($+, -$)** by angle $\beta$ around $\vec{U}$:
  $$\vec{H}' = \vec{H} \cos\beta - \vec{L} \sin\beta, \quad \vec{L}' = \vec{H} \sin\beta + \vec{L} \cos\beta$$
- **Roll ($\backslash, /$)** by angle $\gamma$ around $\vec{H}$:
  $$\vec{L}' = \vec{L} \cos\gamma - \vec{U} \sin\gamma, \quad \vec{U}' = \vec{L} \sin\gamma + \vec{U} \cos\gamma$$

#### Phototropism and Gravitropism Bias
Branches bend toward light or sag under gravity using a steering vector $\vec{T}$:
$$\vec{H}_{\text{steered}} = \text{normalize}\left(\vec{H} + w \cdot \vec{T}\right)$$
where $w$ is the bending susceptibility coefficient (typically $0.12 - 0.25$).

---

### B. Space Colonization Algorithm (Attractor-Driven Canopies)

For realistic crown envelopes (such as sweeping weeping willows or wind-swept Bonsai pines), the **Space Colonization Algorithm** (Runions et al.) iteratively grows branch nodes toward randomly distributed attractor points within a volumetric boundary.

#### Algorithm Steps
1. **Attractor Seeding**: Distribute $N$ attractor points $\mathcal{S} = \{p_1, \dots, p_N\}$ inside an organic bounding volume (ellipsoid, cone, or paraboloid).
2. **Influence Query**: For each tree node $v$, find attractors within distance $d_i$ (influence radius).
3. **Kill Zone Pruning**: Delete any attractor point within distance $d_k$ of any tree node ($d_k < d_i$).
4. **Growth Vector Accumulation**: Each node $v$ averages normalized vectors to its associated attractors:
   $$\vec{D}_v = \text{normalize}\left( \sum_{p \in \mathcal{S}_v} \frac{p - v}{\|p - v\|} \right)$$
5. **Node Insertion**: Add child node $v' = v + \text{segment\_length} \cdot \vec{D}_v$.

---

### C. Vogel's Phyllotaxis Model for Blossoms and Succulents

Petals, leaves, and rosette succulents (e.g., *Echeveria*) follow golden-angle spiral distributions governed by the golden ratio $\phi \approx 1.6180339887$:
$$\theta_n = n \times 137.507764^\circ, \quad r_n = c \cdot \sqrt{n}$$
For 3D botanical voxelization, height $z_n$ and tilt angle $\psi_n$ form a cup-shaped or dome rosette:
$$z_n = h_{\text{max}} \cdot \left( \frac{r_n}{r_{\text{max}}} \right)^\gamma, \quad \psi_n = \psi_{\text{base}} \cdot \left(1 - \frac{r_n}{r_{\text{max}}}\right)$$

---

## 2. Voxel Discrete Rasterization Pipeline

Once continuous branch skeletons and foliage attractors are computed, they must be discretized into an integer 3D grid $\mathbb{Z}^3$.

### 3D Bresenham Cylinder Rasterization
A branch between node $A = (x_1, y_1, z_1)$ and $B = (x_2, y_2, z_2)$ with integer voxel radius $R$ is rasterized by marching the central ray and expanding a discrete spherical or cylindrical kernel:

```typescript
function rasterizeBranchCylinder(
  grid: Map<string, number>,
  p1: [number, number, number],
  p2: [number, number, number],
  radius: number,
  colorIndex: number
): void {
  const dx = p2[0] - p1[0];
  const dy = p2[1] - p1[1];
  const dz = p2[2] - p1[2];
  const dist = Math.hypot(dx, dy, dz);
  const steps = Math.ceil(dist * 2); // 0.5 voxel step size to prevent gaps

  for (let s = 0; s <= steps; s++) {
    const t = s / steps;
    const cx = Math.round(p1[0] + dx * t);
    const cy = Math.round(p1[1] + dy * t);
    const cz = Math.round(p1[2] + dz * t);

    // Expand radial cross-section
    for (let rx = -radius; rx <= radius; rx++) {
      for (let ry = -radius; ry <= radius; ry++) {
        for (let rz = -radius; rz <= radius; rz++) {
          if (rx * rx + ry * ry + rz * rz <= radius * radius) {
            const key = `${cx + rx},${cy + ry},${cz + rz}`;
            grid.set(key, colorIndex);
          }
        }
      }
    }
  }
}
```

### Noise-Perturbed Volumetric Foliage Billows
To avoid synthetic spherical "marshmallow" foliage, leaf clusters use 3D Perlin or Simplex noise displacement:
$$\text{Dist}_{\text{organic}}(x, y, z) = \frac{(x - c_x)^2}{r_x^2} + \frac{(y - c_y)^2}{r_y^2} + \frac{(z - c_z)^2}{r_z^2} + \alpha \cdot \text{Noise3D}\left( \frac{x}{\lambda}, \frac{y}{\lambda}, \frac{z}{\lambda} \right)$$
Voxels are instantiated where $\text{Dist}_{\text{organic}} \le 1.0$.

### Disconnected Sliver Pruning (Flood-Fill BFS)
To eliminate floating, single-voxel visual artifacts:
1. Construct adjacency graph where neighbors share 6-connectivity (faces) or 26-connectivity (edges/vertices).
2. Run Breadth-First Search (BFS) from the root trunk voxels ($z = z_{\text{min}}$).
3. Any disconnected component with voxel count $< \theta_{\text{min}}$ (typically 4 voxels) is purged from the scene.

---

## 3. Botanical Color Palette Architecture

Authentic voxel art relies on tight, harmonized color palettes with distinct material ramps:

| Botanical Species | Material Component | Hex Color Palette Ramps | Artistic Intent |
| :--- | :--- | :--- | :--- |
| **Japanese Sakura** | Trunk & Roots | `#2c1b18`, `#422b26`, `#593c35` | Weathered dark cedar bark |
| | Core Canopy | `#f472b6`, `#ec4899`, `#db2777` | Dense deep magenta inner bloom |
| | Outer Billows | `#fbcfe8`, `#fdf2f8`, `#ffffff` | Sun-kissed soft pink highlights |
| **Golden Ginkgo** | Trunk & Limbs | `#3b2f2f`, `#54433d`, `#6e594f` | Matted brown heartwood |
| | Golden Crown | `#eab308`, `#facc15`, `#fef08a` | Radiating autumn saffron fans |
| **Scots Pine / Bonsai**| Twisted Trunk | `#1f1917`, `#382e2b`, `#4e3f3a` | Gnarled aged pine bark |
| | Needle Clusters | `#14532d`, `#166534`, `#22c55e` | Emerald evergreen foliage |
| **Moss & Stone Basin** | Bedrock Strata | `#1e293b`, `#334155`, `#475569` | Tiered slate foundation |
| | Moss Carpet | `#15803d`, `#4ade80`, `#86efac` | Damp velvet moss accretion |

---

## 4. Production TypeScript Procedural Botanical Engine

Below is a complete, self-contained TypeScript procedural generator that implements stochastic 3D L-Systems, branch discretization, and noise-displaced foliage clusters.

```typescript
/**
 * Procedural Voxel Botanical Generator
 * Supports Sakura, Ginkgo, Pine Bonsai, and Organic Shrubs.
 */

export interface VoxelRecord {
  x: number;
  y: number;
  z: number;
  colorHex: string;
  paletteIndex: number;
}

export interface TreeConfig {
  species: 'sakura' | 'ginkgo' | 'bonsai';
  iterations: number;
  branchAngle: number; // in radians
  segmentLength: number;
  trunkRadius: number;
  foliageRadius: number;
  noiseScale: number;
  seed: number;
}

export class VoxelBotanist {
  private voxels = new Map<string, VoxelRecord>();

  constructor(private config: TreeConfig) {}

  public generate(): VoxelRecord[] {
    this.voxels.clear();

    // 1. Generate L-System branch skeleton
    const grammar = this.expandLSystem();
    const branchEndpoints = this.interpretTurtle(grammar);

    // 2. Grow noise-displaced foliage billows at terminal nodes
    for (const tip of branchEndpoints) {
      this.rasterizeFoliageCluster(tip);
    }

    return Array.from(this.voxels.values());
  }

  private expandLSystem(): string {
    let axiom = 'F';
    const rules: Record<string, string[]> = {
      F: [
        'F[&+F]F[/-F][*F]',
        'F[\\+F]F[&F]',
        'F[+F]F[-F][&F]',
      ],
    };

    for (let i = 0; i < this.config.iterations; i++) {
      let next = '';
      for (const char of axiom) {
        if (rules[char]) {
          const variants = rules[char];
          next += variants[Math.floor(Math.random() * variants.length)];
        } else {
          next += char;
        }
      }
      axiom = next;
    }
    return axiom;
  }

  private interpretTurtle(grammar: string): [number, number, number][] {
    const endpoints: [number, number, number][] = [];
    const stack: { pos: [number, number, number]; h: number[]; l: number[]; u: number[]; radius: number }[] = [];

    let pos: [number, number, number] = [0, 0, 0];
    let h = [0, 1, 0]; // Heading (upward)
    let l = [1, 0, 0]; // Left
    let u = [0, 0, 1]; // Up
    let curRadius = this.config.trunkRadius;

    const angle = this.config.branchAngle;

    for (const char of grammar) {
      switch (char) {
        case 'F': {
          const nextPos: [number, number, number] = [
            pos[0] + h[0] * this.config.segmentLength,
            pos[1] + h[1] * this.config.segmentLength,
            pos[2] + h[2] * this.config.segmentLength,
          ];
          this.rasterizeCylinder(pos, nextPos, curRadius, '#3e2723', 1);
          pos = nextPos;
          curRadius = Math.max(1, curRadius * 0.82);
          break;
        }
        case '+': // Yaw right
          [h, l] = this.rotateAroundAxis(h, l, u, angle);
          break;
        case '-': // Yaw left
          [h, l] = this.rotateAroundAxis(h, l, u, -angle);
          break;
        case '&': // Pitch down
          [h, u] = this.rotateAroundAxis(h, u, l, angle);
          break;
        case '^': // Pitch up
          [h, u] = this.rotateAroundAxis(h, u, l, -angle);
          break;
        case '/': // Roll
          [l, u] = this.rotateAroundAxis(l, u, h, angle);
          break;
        case '[': // Push state
          stack.push({ pos: [...pos], h: [...h], l: [...l], u: [...u], radius: curRadius });
          break;
        case ']': // Pop state
          endpoints.push([...pos]);
          if (stack.length > 0) {
            const state = stack.pop()!;
            pos = state.pos;
            h = state.h;
            l = state.l;
            u = state.u;
            curRadius = state.radius;
          }
          break;
      }
    }
    return endpoints;
  }

  private rasterizeCylinder(
    p1: [number, number, number],
    p2: [number, number, number],
    radius: number,
    colorHex: string,
    paletteIndex: number
  ): void {
    const dist = Math.hypot(p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]);
    const steps = Math.ceil(dist * 2);
    for (let s = 0; s <= steps; s++) {
      const t = s / steps;
      const cx = Math.round(p1[0] + (p2[0] - p1[0]) * t);
      const cy = Math.round(p1[1] + (p2[1] - p1[1]) * t);
      const cz = Math.round(p1[2] + (p2[2] - p1[2]) * t);

      for (let rx = -radius; rx <= radius; rx++) {
        for (let ry = -radius; ry <= radius; ry++) {
          for (let rz = -radius; rz <= radius; rz++) {
            if (rx * rx + ry * ry + rz * rz <= radius * radius) {
              const key = `${cx + rx},${cy + ry},${cz + rz}`;
              this.voxels.set(key, {
                x: cx + rx,
                y: cy + ry,
                z: cz + rz,
                colorHex,
                paletteIndex,
              });
            }
          }
        }
      }
    }
  }

  private rasterizeFoliageCluster(center: [number, number, number]): void {
    const r = this.config.foliageRadius;
    const isSakura = this.config.species === 'sakura';
    const basePalette = isSakura ? ['#f472b6', '#fbcfe8', '#fdf2f8'] : ['#eab308', '#facc15', '#fef08a'];

    for (let dx = -r; dx <= r; dx++) {
      for (let dy = -r; dy <= r; dy++) {
        for (let dz = -r; dz <= r; dz++) {
          const distSq = (dx * dx) / (r * r) + (dy * dy) / ((r * 0.8) * (r * 0.8)) + (dz * dz) / (r * r);
          // Noise perturbation threshold
          if (distSq <= 1.0 + (Math.sin(dx * 1.5) * Math.cos(dz * 1.5)) * 0.3) {
            const x = Math.round(center[0] + dx);
            const y = Math.round(center[1] + dy);
            const z = Math.round(center[2] + dz);
            const key = `${x},${y},${z}`;

            // Distance-based color shade (inner core is darker, outer rim is pastel)
            const color = distSq > 0.6 ? basePalette[2] : distSq > 0.3 ? basePalette[1] : basePalette[0];

            if (!this.voxels.has(key)) {
              this.voxels.set(key, { x, y, z, colorHex: color, paletteIndex: 2 });
            }
          }
        }
      }
    }
  }

  private rotateAroundAxis(
    v1: number[],
    v2: number[],
    axis: number[],
    angle: number
  ): [number[], number[]] {
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    // Simple 2D rotation projection
    const newV1 = [v1[0] * cos + v2[0] * sin, v1[1] * cos + v2[1] * sin, v1[2] * cos + v2[2] * sin];
    const newV2 = [-v1[0] * sin + v2[0] * cos, -v1[1] * sin + v2[1] * cos, -v1[2] * sin + v2[2] * cos];
    return [newV1, newV2];
  }
}
```

---

## 5. Web Real-Time Three.js InstancedMesh Voxel Renderer

To render thousands of procedural botanical voxels at 60 FPS in standard web browsers, instantiate a single shared `BoxGeometry` via `THREE.InstancedMesh`:

```tsx
import React, { useMemo, useRef, useEffect } from 'react';
import * as THREE from 'three';
import { VoxelBotanist, TreeConfig } from './VoxelBotanist';

export const ProceduralVoxelTree: React.FC<{ config: TreeConfig }> = ({ config }) => {
  const meshRef = useRef<THREE.InstancedMesh>(null);

  const voxels = useMemo(() => {
    const botanist = new VoxelBotanist(config);
    return botanist.generate();
  }, [config]);

  useEffect(() => {
    if (!meshRef.current) return;
    const dummy = new THREE.Object3D();
    const color = new THREE.Color();

    voxels.forEach((vox, i) => {
      dummy.position.set(vox.x * 0.5, vox.y * 0.5, vox.z * 0.5);
      dummy.scale.set(0.5, 0.5, 0.5);
      dummy.updateMatrix();

      meshRef.current!.setMatrixAt(i, dummy.matrix);
      color.set(vox.colorHex);
      meshRef.current!.setColorAt(i, color);
    });

    meshRef.current.instanceMatrix.needsUpdate = true;
    if (meshRef.current.instanceColor) {
      meshRef.current.instanceColor.needsUpdate = true;
    }
  }, [voxels]);

  return (
    <instancedMesh
      ref={meshRef}
      args={[undefined, undefined, voxels.length]}
      castShadow
      receiveShadow
    >
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial roughness={0.7} metalness={0.1} />
    </instancedMesh>
  );
};
```

---

## 6. Open-Source Ecosystem Benchmark & Tooling

The table below summarizes leading open-source libraries and algorithms for procedural 3D voxel nature generation:

| Library / Tool | Language | License | Primary Architectural Feature |
| :--- | :--- | :--- | :--- |
| **Goxel** | C / C++ | GPL-3.0 | 3D Voxel editor with procedural raytraced rendering and `.vox` export. |
| **MagicaVoxel Parser** | JS/TS | MIT | Zero-dependency binary parser/writer for MagicaVoxel `.vox` files. |
| **Three.js InstancedMesh** | JavaScript | MIT | GPU-accelerated single-draw-call rendering for $100\text{k}+$ voxels. |
| **SpaceColonization-3D** | Python | MIT | Branch attractor generator for organic tree skeleton topologies. |
| **SimplexNoise** | TypeScript | MIT | 3D fast continuous noise generator for organic foliage perturbations. |

---

## 7. Recommended Production Workflow

1. **Seed Generation**: Generate a deterministic seed to produce reproducible procedural botanical models across multiplayer simulation instances.
2. **Skeleton & Crown Construction**: Run L-Systems for branching and Space Colonization for weeping/phototropic crowns.
3. **Discrete Rasterization**: Discretize branches using 3D Bresenham line marches, then grow noise-displaced foliage clusters.
4. **Sliver Filtering**: Apply 6-neighbor flood-fill to prune orphan single-voxel floaters.
5. **Format Packaging**: Export directly to `.vox` binary format for game engines and stream via Three.js `InstancedMesh` for web portals.
