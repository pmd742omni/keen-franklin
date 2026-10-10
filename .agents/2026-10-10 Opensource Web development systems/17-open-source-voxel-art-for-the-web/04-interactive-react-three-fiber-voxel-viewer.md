# Interactive React Three Fiber Voxel Viewer Blueprint (2026)

> **Production Component:** Complete, ready-to-use React Three Fiber (R3F) component featuring `.vox` parsing, `InstancedMesh` hardware acceleration, studio 3-point lighting, contact shadows, and OrbitControls.

---

## 1. Component Architecture Overview

```
[VoxelCanvasContainer]
       │
       ├── <Canvas shadows gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping }}>
       │        │
       │        ├── <OrbitControls makeDefault autoRotate autoRotateSpeed={0.5} />
       │        │
       │        ├── <Environment preset="city" />
       │        ├── <directionalLight castShadow position={[10, 15, 10]} intensity={1.8} />
       │        ├── <ambientLight intensity={0.4} />
       │        │
       │        ├── <VoxelModel voxUrl="/assets/character.vox" />
       │        │         │
       │        │         ├── fetch ArrayBuffer
       │        │         ├── parseVoxBinary()
       │        │         └── <instancedMesh count={voxels.length}>
       │        │
       │        └── <ContactShadows position={[0, -0.01, 0]} opacity={0.6} blur={1.5} />
```

---

## 2. Complete Production Implementation (`VoxelViewer.tsx`)

```tsx
'use client';

import React, { Suspense, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, ContactShadows, Float, Center } from '@react-three/drei';
import * as THREE from 'three';

// -----------------------------------------------------------------------------
// 1. Types & Minimal .VOX Parser
// -----------------------------------------------------------------------------
interface Voxel {
  x: number;
  y: number;
  z: number;
  colorIndex: number;
}

interface VoxPayload {
  size: [number, number, number];
  voxels: Voxel[];
  palette: THREE.Color[];
}

function parseVox(buffer: ArrayBuffer): VoxPayload {
  const dv = new DataView(buffer);
  let offset = 8; // Skip 'VOX ' and version int32
  let size: [number, number, number] = [16, 16, 16];
  const voxels: Voxel[] = [];
  const palette: THREE.Color[] = [];

  while (offset < buffer.byteLength) {
    const chunkId = String.fromCharCode(
      dv.getUint8(offset),
      dv.getUint8(offset + 1),
      dv.getUint8(offset + 2),
      dv.getUint8(offset + 3)
    );
    const contentBytes = dv.getInt32(offset + 4, true);
    offset += 12;

    if (chunkId === 'SIZE') {
      size = [dv.getInt32(offset, true), dv.getInt32(offset + 4, true), dv.getInt32(offset + 8, true)];
    } else if (chunkId === 'XYZI') {
      const count = dv.getInt32(offset, true);
      for (let i = 0; i < count; i++) {
        const vOffset = offset + 4 + i * 4;
        voxels.push({
          x: dv.getUint8(vOffset),
          y: dv.getUint8(vOffset + 2), // MagicaVoxel Z is up; map to Three.js Y
          z: dv.getUint8(vOffset + 1),
          colorIndex: dv.getUint8(vOffset + 3),
        });
      }
    } else if (chunkId === 'RGBA') {
      for (let i = 0; i < 256; i++) {
        const r = dv.getUint8(offset + i * 4) / 255;
        const g = dv.getUint8(offset + i * 4 + 1) / 255;
        const b = dv.getUint8(offset + i * 4 + 2) / 255;
        palette.push(new THREE.Color(r, g, b));
      }
    }
    offset += contentBytes;
  }

  // Fallback default palette if RGBA chunk was absent
  if (palette.length === 0) {
    for (let i = 0; i < 256; i++) {
      palette.push(new THREE.Color().setHSL(i / 256, 0.8, 0.5));
    }
  }

  return { size, voxels, palette };
}

// -----------------------------------------------------------------------------
// 2. Hardware Instanced Voxel Renderer Component
// -----------------------------------------------------------------------------
function VoxelMesh({ modelData }: { modelData: VoxPayload }) {
  const meshRef = useRef<THREE.InstancedMesh>(null!);
  const tempObj = useMemo(() => new THREE.Object3D(), []);

  useLayoutEffect(() => {
    if (!meshRef.current) return;

    const [sx, sy, sz] = modelData.size;
    // Center the model at origin (0, 0, 0)
    const offsetX = sx / 2;
    const offsetY = sy / 2;
    const offsetZ = sz / 2;

    modelData.voxels.forEach((v, idx) => {
      tempObj.position.set(v.x - offsetX, v.y - offsetY, v.z - offsetZ);
      tempObj.updateMatrix();
      meshRef.current.setMatrixAt(idx, tempObj.matrix);

      const col = modelData.palette[v.colorIndex] || new THREE.Color(1, 1, 1);
      meshRef.current.setColorAt(idx, col);
    });

    meshRef.current.instanceMatrix.needsUpdate = true;
    if (meshRef.current.instanceColor) {
      meshRef.current.instanceColor.needsUpdate = true;
    }
  }, [modelData, tempObj]);

  return (
    <instancedMesh
      ref={meshRef}
      args={[undefined, undefined, modelData.voxels.length]}
      castShadow
      receiveShadow
    >
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial
        roughness={0.65}
        metalness={0.08}
        envMapIntensity={0.8}
      />
    </instancedMesh>
  );
}

// -----------------------------------------------------------------------------
// 3. Main Interactive Canvas Wrapper
// -----------------------------------------------------------------------------
export function VoxelViewer({ voxUrl }: { voxUrl?: string }) {
  const [model, setModel] = useState<VoxPayload | null>(null);

  useEffect(() => {
    if (voxUrl) {
      fetch(voxUrl)
        .then((res) => res.arrayBuffer())
        .then((buf) => setModel(parseVox(buf)))
        .catch((err) => console.error('Failed to load vox model:', err));
    } else {
      // Procedural sample model: Stylized voxel tree
      const sampleVoxels: Voxel[] = [];
      const samplePalette: THREE.Color[] = [
        new THREE.Color('#000000'),
        new THREE.Color('#5c3a21'), // Trunk wood
        new THREE.Color('#2d6a4f'), // Dark foliage
        new THREE.Color('#52b788'), // Bright foliage
      ];

      // Trunk
      for (let y = 0; y < 8; y++) {
        for (let x = 3; x <= 4; x++) {
          for (let z = 3; z <= 4; z++) {
            sampleVoxels.push({ x, y, z, colorIndex: 1 });
          }
        }
      }
      // Foliage crown
      for (let y = 6; y <= 12; y++) {
        for (let x = 0; x <= 7; x++) {
          for (let z = 0; z <= 7; z++) {
            if (Math.hypot(x - 3.5, y - 9, z - 3.5) < 3.8) {
              const col = Math.random() > 0.4 ? 2 : 3;
              sampleVoxels.push({ x, y, z, colorIndex: col });
            }
          }
        }
      }

      setModel({ size: [8, 13, 8], voxels: sampleVoxels, palette: samplePalette });
    }
  }, [voxUrl]);

  return (
    <div className="w-full h-[600px] relative bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
      <Canvas
        shadows
        camera={{ position: [18, 14, 18], fov: 45 }}
        gl={{
          antialias: true,
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1.2,
        }}
      >
        <Suspense fallback={null}>
          {/* Studio Lighting */}
          <ambientLight intensity={0.5} />
          <directionalLight
            position={[15, 25, 12]}
            intensity={1.8}
            castShadow
            shadow-mapSize={[2048, 2048]}
            shadow-bias={-0.0001}
          />
          <directionalLight position={[-15, 8, -12]} intensity={0.4} color="#60a5fa" />

          {/* Interactive Model */}
          {model && (
            <Center position={[0, 2, 0]}>
              <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.3}>
                <VoxelMesh modelData={model} />
              </Float>
            </Center>
          )}

          {/* Soft Ground Contact Shadow */}
          <ContactShadows
            position={[0, -2, 0]}
            opacity={0.7}
            scale={24}
            blur={2.0}
            far={10}
          />

          <OrbitControls
            makeDefault
            minDistance={8}
            maxDistance={40}
            maxPolarAngle={Math.PI / 2 + 0.1}
            enableDamping
            dampingFactor={0.05}
          />
        </Suspense>
      </Canvas>

      {/* Floating HUD */}
      <div className="absolute bottom-4 left-4 pointer-events-none text-xs text-slate-400 bg-slate-900/80 backdrop-blur px-3 py-1.5 rounded-lg border border-slate-800">
        Voxels: <span className="text-emerald-400 font-mono font-semibold">{model?.voxels.length ?? 0}</span> | 1 Draw Call (InstancedMesh)
      </div>
    </div>
  );
}
```

---

## 3. Best Practices for Production Web Embedding

1. **Enable Shadows Carefully:** Set `castShadow` and `receiveShadow` on the `InstancedMesh`. Limit shadow map resolution to `1024x1024` on mobile and `2048x2048` on desktop.
2. **ACESFilmic Tone Mapping:** Always enable `THREE.ACESFilmicToneMapping` in the Three.js renderer. Voxel colors look significantly more photographic, avoiding harsh clamp blowouts on bright white faces.
3. **Floating & Centering:** Wrap voxel entities in `@react-three/drei`'s `<Center>` and `<Float>` components to give models an organic, tactile, floating desktop miniature feel.
4. **Touch & Damping:** Set `enableDamping={true}` with `dampingFactor={0.05}` in `OrbitControls` to provide inertia when panning or orbiting on touchscreens.
