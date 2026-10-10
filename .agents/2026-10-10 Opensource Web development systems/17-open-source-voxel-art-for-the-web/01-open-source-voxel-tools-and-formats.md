# Open-Source & Free Voxel Tools, Formats, and Asset Pipelines for the Web

> **2026 Engineering Guide:** Deep survey of free and open-source voxel authoring tools, file formats (`.vox`, `.gox`, `.qb`), color palette architectures, and browser asset ingestion pipelines.

---

## 1. What is Voxel Art on the Web?

A **voxel** (volumetric pixel) represents a value on a regular grid in three-dimensional space. Unlike traditional polygonal 3D models with arbitrary vertex positions, voxel models are defined on discrete integer coordinate lattices `(x, y, z)`.

On the web, voxel art offers:
1. **Artistic Distinction:** A tactile, retro-modern, stylized aesthetic (Minecraft, Crossy Road, Teardown, The Sandbox).
2. **Deterministic Data Structures:** Extremely simple serialization (3D arrays, octrees, run-length encoding).
3. **Destructibility & Modification:** Real-time terrain carving, voxel digging, and dynamic physics without complex CSG (Constructive Solid Geometry) mesh boolean operations.
4. **Lightweight Transmission:** A complex voxel model often serializes to just tens of kilobytes in compressed binary formats.

---

## 2. Leading Free & Open-Source Voxel Authoring Tools

| Tool | License | Platform | Web Export Formats | Key Strengths |
| :--- | :--- | :--- | :--- | :--- |
| **Goxel** | **GPL-3.0 (100% Free OSS)** | Windows, macOS, Linux, Web (WASM) | `.vox`, `.obj`, `.gox`, `.ply`, `.glb` | Native layer support, unlimited grid size, procedural tools, compiles to WebAssembly for in-browser editing. |
| **MagicaVoxel** | **Free for commercial use** (Proprietary engine by Ephtracy) | Windows, macOS | `.vox`, `.obj`, `.ply`, `.mc`, `.2d` | Gold standard voxel renderer, 256-color indexed palette, raytracing viewport, keyframe animator. |
| **Kenney Voxel Tools** | **MIT / Public Domain (CC0)** | Web / Desktop | `.obj`, `.gltf` | Ultra-simple browser tool for game jams, prototyping, and modular environmental tiles. |
| **Voxel.js Web Editor** | **BSD-2-Clause (Open Source)** | In-Browser WebGL | `.json`, `.vox` | Fully extensible JavaScript-based in-browser voxel builder and playground. |
| **Qubicle Free** | Freemium | Windows, macOS | `.qb`, `.vox`, `.fbx` | Enterprise-grade voxel modeling with matrix slicing and compound mesh rigging. |

---

## 3. Core Voxel File Formats

### A. MagicaVoxel `.vox` Format (De Facto Standard)
The `.vox` format is a RIFF-style chunk-based binary format. It stores:
- **`MAIN` Chunk:** Root container.
- **`SIZE` Chunk:** Voxel bounding dimensions `(sx, sy, sz)` up to 256x256x256 per node.
- **`XYZI` Chunk:** Array of occupied voxels, each packed into 4 bytes: `x`, `y`, `z`, and `colorIndex` (1–255).
- **`RGBA` Chunk:** 256-color palette (each color RGBA encoded).
- **`nTRN` / `nGRP` / `nSHP` Chunks:** Scene graph hierarchy, translation offsets, rotations, and animation frames.

#### Parsing `.vox` in Browser JavaScript (Zero External Dependencies):
```javascript
// Minimal VOX parser slice in TypeScript
export interface Voxel {
  x: number;
  y: number;
  z: number;
  colorIndex: number;
}

export interface VoxData {
  size: { x: number; y: number; z: number };
  voxels: Voxel[];
  palette: Uint32Array;
}

export function parseVoxBinary(buffer: ArrayBuffer): VoxData {
  const dataView = new DataView(buffer);
  let offset = 0;

  // Verify 'VOX ' magic header
  const magic = String.fromCharCode(...new Uint8Array(buffer, 0, 4));
  if (magic !== 'VOX ') throw new Error('Invalid VOX file header');
  const version = dataView.getInt32(4, true);
  offset = 8;

  let size = { x: 0, y: 0, z: 0 };
  let voxels: Voxel[] = [];
  const palette = new Uint32Array(256);

  // Parse RIFF chunks
  while (offset < buffer.byteLength) {
    const chunkId = String.fromCharCode(...new Uint8Array(buffer, offset, 4));
    const contentBytes = dataView.getInt32(offset + 4, true);
    const childBytes = dataView.getInt32(offset + 8, true);
    offset += 12;

    if (chunkId === 'SIZE') {
      size.x = dataView.getInt32(offset, true);
      size.y = dataView.getInt32(offset + 4, true);
      size.z = dataView.getInt32(offset + 8, true);
    } else if (chunkId === 'XYZI') {
      const numVoxels = dataView.getInt32(offset, true);
      for (let i = 0; i < numVoxels; i++) {
        const vOffset = offset + 4 + i * 4;
        voxels.push({
          x: dataView.getUint8(vOffset),
          y: dataView.getUint8(vOffset + 1),
          z: dataView.getUint8(vOffset + 2),
          colorIndex: dataView.getUint8(vOffset + 3),
        });
      }
    } else if (chunkId === 'RGBA') {
      for (let i = 0; i < 256; i++) {
        palette[i] = dataView.getUint32(offset + i * 4, true);
      }
    }

    offset += contentBytes;
  }

  return { size, voxels, palette };
}
```

---

## 4. Palette Design Principles for Web Voxel Art

In voxel art, **color choice is 80% of the visual readability**. Because voxels have no sub-pixel texture detail or beveling, values and hue shifts must define the forms.

### Golden Rules:
1. **Hue Shifting for Shadows:**
   - Highlights shift warmer (towards yellow/orange).
   - Shadows shift cooler (towards purple/navy/blue).
   - Never simply reduce brightness (`L` in HSL); always shift hue to prevent muddy gray shadows.
2. **Restricted Palette Discipline:**
   - Limit models to 16–32 active colors.
   - Use standard open-source palettes: **Endesga 32**, **PICO-8**, **Dawnbringer 32 (DB32)**, or custom MagicaVoxel `.act` tables.
3. **High Contrast Ramp:**
   - Ensure at least 3 distinct value steps per material: *Base Light*, *Midtone*, *Core Shadow*.

---

## 5. Web Asset Pipelines: From Voxel to Optimized GLB

While raw `.vox` files can be parsed directly in JavaScript, for production web performance (especially on mobile devices), pre-converting voxel models to **GLTF / GLB** with vertex colors or compact texture atlases is standard practice:

```
[MagicaVoxel / Goxel] 
        │
        ├─ Option A: Direct Runtime Load (.vox) ──> Client Greedy Mesh / Instancing (Three.js)
        │
        └─ Option B: Build-time Optimization:
                 │
                 ▼ Export .obj + .mtl
           [Blender Python Script / gltfpack]
                 │
                 ▼ Greedy Mesh + Texture Atlas + Draco/Meshopt Compression
           [model.optimized.glb (50KB)] ──> Instant Load on Web
```
