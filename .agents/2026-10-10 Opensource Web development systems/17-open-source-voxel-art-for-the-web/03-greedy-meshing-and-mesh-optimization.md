# Greedy Meshing & Voxel Geometry Optimization (2026)

> **Algorithmic Mastery:** How greedy meshing slashes voxel polygon counts by 90%–97% and produces buttery smooth 120 FPS web experiences, paired with procedural vertex Ambient Occlusion (AO).

---

## 1. Why Greedy Meshing is Essential

Consider a 16x16x16 solid cube of voxels (4,096 voxels):
- **Naive Cube Mesh:** $4,096 \text{ voxels} \times 6 \text{ faces} \times 2 \text{ triangles} = \mathbf{49,152 \text{ triangles}}$.
- **Culled Faces (Outer skin only):** $16 \times 16 \times 6 \text{ faces} \times 2 = \mathbf{3,072 \text{ triangles}}$.
- **Greedy Meshed (Merged quads):** $6 \text{ quad faces} \times 2 = \mathbf{12 \text{ triangles}}$!

```
Naive Voxel Faces:
┌─┬─┬─┬─┐
├─┼─┼─┼─┤  ===> 16 small quads (32 triangles)
├─┼─┼─┼─┤
└─┴─┴─┴─┘

Greedy Meshed:
┌───────┐
│       │  ===> 1 single large merged quad (2 triangles)
└───────┘
```

---

## 2. The Greedy Meshing Algorithm Explained

Originating from Mikola Lysenko's open-source research, the algorithm operates across three principal coordinate sweeps ($d \in \{0, 1, 2\}$ for $X, Y, Z$ axes):

1. **Slice the Volume:** Iterate layer-by-layer through the 3D voxel grid.
2. **Compute Face Mask:** For each cell in the 2D slice, check if there is a boundary between solid and empty space:
   - `mask[x, y] = (current == solid && neighbor == empty) ? color : null`
3. **Expand Quads Greedily:**
   - Scan along width ($W$) while cells share the identical material/color.
   - Scan along height ($H$) while the entire row of width $W$ matches.
   - Emit a single quad spanning $W \times H$.
   - Clear the merged cells in the mask.
   - Repeat until the slice mask is empty.

---

## 3. High-Performance TypeScript Greedy Mesher for Three.js

```typescript
import * as THREE from 'three';

export interface VoxelGrid {
  dims: [number, number, number];
  // 1D flattened array: index = x + y * dims[0] + z * dims[0] * dims[1]
  data: Uint8Array;
  palette: THREE.Color[];
}

export function greedyMesh(grid: VoxelGrid): THREE.BufferGeometry {
  const [dx, dy, dz] = grid.dims;
  const positions: number[] = [];
  const normals: number[] = [];
  const colors: number[] = [];
  const indices: number[] = [];

  let vertexCount = 0;

  function getVoxel(x: number, y: number, z: number): number {
    if (x < 0 || x >= dx || y < 0 || y >= dy || z < 0 || z >= dz) return 0;
    return grid.data[x + y * dx + z * dx * dy];
  }

  // Iterate over 3 axes: 0=x, 1=y, 2=z
  for (let d = 0; d < 3; d++) {
    const u = (d + 1) % 3;
    const v = (d + 2) % 3;

    const x = [0, 0, 0];
    const q = [0, 0, 0];
    q[d] = 1;

    const mask = new Int32Array(grid.dims[u] * grid.dims[v]);

    for (x[d] = -1; x[d] < grid.dims[d]; ) {
      let n = 0;

      // 1. Compute the mask for this slice
      for (x[v] = 0; x[v] < grid.dims[v]; ++x[v]) {
        for (x[u] = 0; x[u] < grid.dims[u]; ++x[u]) {
          const a = x[d] >= 0 ? getVoxel(x[0], x[1], x[2]) : 0;
          const b = x[d] < grid.dims[d] - 1 ? getVoxel(x[0] + q[0], x[1] + q[1], x[2] + q[2]) : 0;

          if (a !== 0 && b !== 0 && a === b) {
            mask[n++] = 0; // Internal occluded face
          } else if (a !== 0) {
            mask[n++] = a; // Front face
          } else if (b !== 0) {
            mask[n++] = -b; // Back face
          } else {
            mask[n++] = 0;
          }
        }
      }

      ++x[d];
      n = 0;

      // 2. Greedily extract quads from mask
      for (let j = 0; j < grid.dims[v]; ++j) {
        for (let i = 0; i < grid.dims[u]; ) {
          const c = mask[n];
          if (c !== 0) {
            // Find width
            let w = 1;
            while (i + w < grid.dims[u] && mask[n + w] === c) {
              w++;
            }

            // Find height
            let h = 1;
            let canExtend = true;
            while (j + h < grid.dims[v] && canExtend) {
              for (let k = 0; k < w; ++k) {
                if (mask[n + k + h * grid.dims[u]] !== c) {
                  canExtend = false;
                  break;
                }
              }
              if (canExtend) h++;
            }

            // Add quad vertices
            x[u] = i;
            x[v] = j;
            const du = [0, 0, 0];
            const dv = [0, 0, 0];
            du[u] = w;
            dv[v] = h;

            const isBack = c < 0;
            const matId = Math.abs(c);
            const color = grid.palette[matId] || new THREE.Color(1, 1, 1);

            const normal = [0, 0, 0];
            normal[d] = isBack ? -1 : 1;

            // Define 4 quad corners
            const p0 = [x[0], x[1], x[2]];
            const p1 = [x[0] + du[0], x[1] + du[1], x[2] + du[2]];
            const p2 = [x[0] + du[0] + dv[0], x[1] + du[1] + dv[1], x[2] + du[2] + dv[2]];
            const p3 = [x[0] + dv[0], x[1] + dv[1], x[2] + dv[2]];

            positions.push(...p0, ...p1, ...p2, ...p3);
            normals.push(...normal, ...normal, ...normal, ...normal);
            colors.push(
              color.r, color.g, color.b,
              color.r, color.g, color.b,
              color.r, color.g, color.b,
              color.r, color.g, color.b
            );

            // Two triangles
            if (isBack) {
              indices.push(vertexCount, vertexCount + 2, vertexCount + 1);
              indices.push(vertexCount, vertexCount + 3, vertexCount + 2);
            } else {
              indices.push(vertexCount, vertexCount + 1, vertexCount + 2);
              indices.push(vertexCount, vertexCount + 2, vertexCount + 3);
            }
            vertexCount += 4;

            // Clear mask for consumed cells
            for (let l = 0; l < h; ++l) {
              for (let k = 0; k < w; ++k) {
                mask[n + k + l * grid.dims[u]] = 0;
              }
            }

            i += w;
            n += w;
          } else {
            i++;
            n++;
          }
        }
      }
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();

  return geometry;
}
```

---

## 4. Procedural Vertex Ambient Occlusion (AO)

Pure flat voxel models can look artificial without soft self-shadowing in crevices and corners. Computing real-time screen-space ambient occlusion (SSAO) is GPU intensive.

Instead, calculate **per-vertex Ambient Occlusion** during meshing by inspecting the 3 adjacent voxels surrounding every vertex corner:

```
Corner AO Calculation:
Side 1 (s1) ────┐
Corner (c)  ────┼───> AO Score:
Side 2 (s2) ────┘     - Both sides blocked: Score 3 (Deep Crevice)
                      - One side + corner: Score 2 (Corner)
                      - One side only: Score 1 (Slight shade)
                      - Clear: Score 0 (Full Light)
```

### AO Formula:
```typescript
function vertexAO(side1: boolean, side2: boolean, corner: boolean): number {
  if (side1 && side2) return 3; // Fully occluded crevice
  return (side1 ? 1 : 0) + (side2 ? 1 : 0) + (corner ? 1 : 0);
}

// Convert AO (0..3) to illumination factor in vertex shader:
// float aoFactor = 1.0 - (float(aoScore) * 0.22);
```

### Key Performance Benefits of Vertex AO:
1. **0ms GPU Runtime Cost:** AO is pre-baked into vertex colors or a single UV channel.
2. **Mobile Friendly:** Renders at full framerate on entry-level smartphones and tablets.
3. **Sublime Stylized Aesthetics:** Delivers the beloved "soft toy" clay aesthetic characteristic of premium voxel indie games.
