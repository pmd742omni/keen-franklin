#!/usr/bin/env python3
"""Procedural 3D Voxel Botanical Generator CLI.

Synthesizes stylized, organic voxel flora (Sakura Cherry Blossoms, Golden Ginkgo,
Japanese Pine Bonsai, Vogel Rosette Succulents) using 3D L-Systems, discrete
rasterization, and noise-perturbed canopy billows.
Exports to MagicaVoxel .vox binary and web-ready JSON voxel grids.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import struct
import sys
from collections import deque
from pathlib import Path
from typing import Dict, List, Set, Tuple


class PaletteRegistry:
    """Pre-calibrated organic botanical color palettes."""
    
    PALETTES = {
        "sakura": {
            "bark": ["#2c1b18", "#422b26", "#593c35"],
            "foliage_core": ["#ec4899", "#db2777"],
            "foliage_mid": ["#f472b6", "#f43f5e"],
            "foliage_rim": ["#fbcfe8", "#fdf2f8", "#ffffff"],
        },
        "ginkgo": {
            "bark": ["#3b2f2f", "#54433d", "#6e594f"],
            "foliage_core": ["#d97706", "#b45309"],
            "foliage_mid": ["#eab308", "#ca8a04"],
            "foliage_rim": ["#facc15", "#fef08a", "#fef9c3"],
        },
        "bonsai": {
            "bark": ["#1f1917", "#382e2b", "#4e3f3a"],
            "foliage_core": ["#14532d", "#0f3a20"],
            "foliage_mid": ["#166534", "#15803d"],
            "foliage_rim": ["#22c55e", "#4ade80", "#86efac"],
        },
        "succulent": {
            "bark": ["#1e293b", "#334155"],
            "foliage_core": ["#065f46", "#047857"],
            "foliage_mid": ["#10b981", "#34d399"],
            "foliage_rim": ["#f43f5e", "#fb7185", "#fda4af"],  # Rosette pink leaf tips
        },
        "willow": {
            "bark": ["#2e2520", "#453830", "#5c4c42"],
            "foliage_core": ["#166534", "#15803d"],
            "foliage_mid": ["#22c55e", "#4ade80"],
            "foliage_rim": ["#86efac", "#bbf7d0", "#dcfce7"],  # Soft lime weeping fronds
        },
    }

    @staticmethod
    def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
        hex_str = hex_str.lstrip("#")
        return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore


class ProceduralVoxelBotanist:
    """Generates procedural 3D voxel botanical models."""

    def __init__(self, species: str = "sakura", seed: int = 42):
        self.species = species if species in PaletteRegistry.PALETTES else "sakura"
        self.palette = PaletteRegistry.PALETTES[self.species]
        self.seed = seed
        self.rng = random.Random(seed)
        self.voxels: Dict[Tuple[int, int, int], str] = {}

    def generate(self, iterations: int = 3) -> Dict[Tuple[int, int, int], str]:
        """Synthesize botanical model based on species."""
        self.voxels.clear()

        if self.species == "succulent":
            self._generate_phyllotaxis_succulent()
        elif self.species == "willow":
            self._generate_space_colonization_willow(iterations)
        else:
            endpoints = self._generate_lsystem_tree(iterations)
            for tip in endpoints:
                self._rasterize_foliage_cluster(tip)

        self._prune_orphan_voxels()
        return self.voxels

    def _generate_lsystem_tree(self, iterations: int) -> List[Tuple[float, float, float]]:
        """L-System grammar generation with 3D turtle state machine."""
        axiom = "F"
        rules = {
            "F": ["F[+F]F[-F][&F]", "F[&F]F[^F][+F]", "F[+F]F[-F]"],
        }

        grammar = axiom
        for _ in range(iterations):
            next_g = []
            for ch in grammar:
                if ch in rules:
                    next_g.append(self.rng.choice(rules[ch]))
                else:
                    next_g.append(ch)
            grammar = "".join(next_g)

        # 3D Turtle Interpretation
        pos = (0.0, 0.0, 0.0)
        h = (0.0, 1.0, 0.0)  # Heading up
        l = (1.0, 0.0, 0.0)  # Left
        u = (0.0, 0.0, 1.0)  # Up

        stack = []
        endpoints = []
        radius = 2.5
        segment_len = 5.0
        angle = math.radians(28.0)

        bark_colors = self.palette["bark"]

        for ch in grammar:
            if ch == "F":
                next_pos = (
                    pos[0] + h[0] * segment_len,
                    pos[1] + h[1] * segment_len,
                    pos[2] + h[2] * segment_len,
                )
                bark_col = self.rng.choice(bark_colors)
                self._rasterize_cylinder(pos, next_pos, max(1, int(round(radius))), bark_col)
                pos = next_pos
                radius = max(0.8, radius * 0.8)
            elif ch == "+":
                h, l = self._rotate_2d(h, l, angle)
            elif ch == "-":
                h, l = self._rotate_2d(h, l, -angle)
            elif ch == "&":
                h, u = self._rotate_2d(h, u, angle)
            elif ch == "^":
                h, u = self._rotate_2d(h, u, -angle)
            elif ch == "[":
                stack.append((pos, h, l, u, radius))
            elif ch == "]":
                endpoints.append(pos)
                if stack:
                    pos, h, l, u, radius = stack.pop()

        return endpoints

    def _rotate_2d(
        self, v1: Tuple[float, float, float], v2: Tuple[float, float, float], angle: float
    ) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        new_v1 = (
            v1[0] * cos_a + v2[0] * sin_a,
            v1[1] * cos_a + v2[1] * sin_a,
            v1[2] * cos_a + v2[2] * sin_a,
        )
        new_v2 = (
            -v1[0] * sin_a + v2[0] * cos_a,
            -v1[1] * sin_a + v2[1] * cos_a,
            -v1[2] * sin_a + v2[2] * cos_a,
        )
        return new_v1, new_v2

    def _rasterize_cylinder(
        self,
        p1: Tuple[float, float, float],
        p2: Tuple[float, float, float],
        radius: int,
        color: str,
    ) -> None:
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dz = p2[2] - p1[2]
        dist = math.hypot(dx, dy, dz)
        steps = max(1, int(math.ceil(dist * 2)))

        for s in range(steps + 1):
            t = s / steps
            cx = int(round(p1[0] + dx * t))
            cy = int(round(p1[1] + dy * t))
            cz = int(round(p1[2] + dz * t))

            for rx in range(-radius, radius + 1):
                for ry in range(-radius, radius + 1):
                    for rz in range(-radius, radius + 1):
                        if rx * rx + ry * ry + rz * rz <= radius * radius:
                            self.voxels[(cx + rx, cy + ry, cz + rz)] = color

    def _rasterize_foliage_cluster(self, center: Tuple[float, float, float]) -> None:
        """Noise-displaced volumetric canopy billow."""
        radius = 4
        cx, cy, cz = int(round(center[0])), int(round(center[1])), int(round(center[2]))

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                for dz in range(-radius, radius + 1):
                    # Normalized ellipsoidal distance with vertical squashing
                    d_sq = (dx * dx) / (radius * radius) + (dy * dy) / ((radius * 0.75) ** 2) + (dz * dz) / (radius * radius)
                    # Organic surface perturbation
                    noise = (math.sin(dx * 1.8) * math.cos(dz * 1.8)) * 0.25
                    if d_sq + noise <= 1.0:
                        pos = (cx + dx, cy + dy, cz + dz)
                        if pos not in self.voxels:
                            # Color layering by radial depth
                            if d_sq > 0.7:
                                col = self.rng.choice(self.palette["foliage_rim"])
                            elif d_sq > 0.4:
                                col = self.rng.choice(self.palette["foliage_mid"])
                            else:
                                col = self.rng.choice(self.palette["foliage_core"])
                            self.voxels[pos] = col

    def _generate_phyllotaxis_succulent(self) -> None:
        """Procedural succulent using Vogel golden ratio phyllotaxis spiral."""
        golden_angle = math.radians(137.507764)
        num_petals = 72
        scale_c = 1.1

        for n in range(num_petals):
            theta = n * golden_angle
            r = scale_c * math.sqrt(n)
            z = (n / num_petals) ** 1.6 * 6.0  # Upward cup curvature

            # Voxelize petal leaf
            petal_len = max(2, int(2 + (n / num_petals) * 4))
            petal_width = max(1, int(1 + (n / num_petals) * 2))

            for l in range(petal_len):
                curr_r = r + l
                px = int(round(curr_r * math.cos(theta)))
                py = int(round(z + (l / petal_len) * 1.5))
                pz = int(round(curr_r * math.sin(theta)))

                # Lateral petal width
                for w in range(-petal_width, petal_width + 1):
                    wx = px + int(round(w * -math.sin(theta)))
                    wz = pz + int(round(w * math.cos(theta)))
                    pos = (wx, py, wz)

                    if l >= petal_len - 1:
                        col = self.rng.choice(self.palette["foliage_rim"])
                    elif l >= petal_len // 2:
                        col = self.rng.choice(self.palette["foliage_mid"])
                    else:
                        col = self.rng.choice(self.palette["foliage_core"])

                    self.voxels[pos] = col

    def _generate_space_colonization_willow(self, iterations: int) -> None:
        """Space Colonization Algorithm for Weeping Willow canopy & drooping fronds."""
        # 1. Distribute attractors within a weeping dome envelope
        num_attractors = 140
        attractors: List[List[float]] = []
        for _ in range(num_attractors):
            theta = self.rng.uniform(0, 2 * math.pi)
            rad = self.rng.uniform(4.0, 18.0)
            # Inverted canopy profile for weeping dome
            y = self.rng.uniform(14.0, 24.0) - (rad / 18.0) ** 2 * 6.0
            x = rad * math.cos(theta)
            z = rad * math.sin(theta)
            attractors.append([x, y, z])

        # 2. Seed trunk nodes
        nodes: List[List[float]] = [[0.0, float(y), 0.0] for y in range(0, 14, 2)]
        parent_map: Dict[int, Optional[int]] = {i: i - 1 for i in range(1, len(nodes))}
        parent_map[0] = None

        d_kill = 3.0
        d_influence = 15.0
        step_len = 2.4

        # 3. Growth iterations
        for _ in range(iterations * 4):
            if not attractors:
                break

            node_attractors: Dict[int, List[List[float]]] = {}
            surviving: List[List[float]] = []

            for att in attractors:
                closest_idx = -1
                min_dist = float("inf")
                for idx, node in enumerate(nodes):
                    d = math.hypot(att[0] - node[0], att[1] - node[1], att[2] - node[2])
                    if d < min_dist:
                        min_dist = d
                        closest_idx = idx

                if min_dist > d_kill:
                    surviving.append(att)
                    if min_dist < d_influence:
                        node_attractors.setdefault(closest_idx, []).append(att)

            attractors = surviving

            new_nodes = []
            for idx, atts in node_attractors.items():
                curr = nodes[idx]
                avg_dir = [0.0, 0.0, 0.0]
                for a in atts:
                    d = math.hypot(a[0] - curr[0], a[1] - curr[1], a[2] - curr[2])
                    if d > 0:
                        avg_dir[0] += (a[0] - curr[0]) / d
                        avg_dir[1] += (a[1] - curr[1]) / d
                        avg_dir[2] += (a[2] - curr[2]) / d

                # Downward weeping gravitropism bias
                avg_dir[1] -= 0.18

                norm = math.hypot(avg_dir[0], avg_dir[1], avg_dir[2])
                if norm > 0:
                    new_node = [
                        curr[0] + (avg_dir[0] / norm) * step_len,
                        curr[1] + (avg_dir[1] / norm) * step_len,
                        curr[2] + (avg_dir[2] / norm) * step_len,
                    ]
                    new_idx = len(nodes) + len(new_nodes)
                    new_nodes.append((new_idx, new_node, idx))

            if not new_nodes:
                break

            for n_idx, n_pos, p_idx in new_nodes:
                nodes.append(n_pos)
                parent_map[n_idx] = p_idx

        # 4. Rasterize branch cylinders
        for c_idx, p_idx in parent_map.items():
            if p_idx is not None:
                p1 = nodes[p_idx]
                p2 = nodes[c_idx]
                height_fraction = max(0.2, 1.0 - (p1[1] / 24.0))
                rad = max(1, int(round(height_fraction * 2.2)))
                col = self.rng.choice(self.palette["bark"])
                self._rasterize_cylinder(tuple(p1), tuple(p2), rad, col)

        # 5. Grow weeping foliage cascades at terminal branch tips
        leaf_nodes = set(range(len(nodes))) - set(p for p in parent_map.values() if p is not None)
        for ln in leaf_nodes:
            pt = nodes[ln]
            cascade_len = self.rng.randint(6, 14)
            cx, cy, cz = int(round(pt[0])), int(round(pt[1])), int(round(pt[2]))
            for drop in range(cascade_len):
                wx = cx + int(round(math.sin(drop * 0.5) * 1.2))
                wz = cz + int(round(math.cos(drop * 0.5) * 1.2))
                wy = cy - drop
                pos = (wx, wy, wz)
                if drop > cascade_len // 2:
                    col = self.rng.choice(self.palette["foliage_rim"])
                elif drop > cascade_len // 4:
                    col = self.rng.choice(self.palette["foliage_mid"])
                else:
                    col = self.rng.choice(self.palette["foliage_core"])
                self.voxels[pos] = col

    def _prune_orphan_voxels(self, min_cluster_size: int = 4) -> None:
        """BFS flood-fill connected components to remove disconnected floaters."""
        if not self.voxels:
            return

        visited: Set[Tuple[int, int, int]] = set()
        to_remove: Set[Tuple[int, int, int]] = set()

        directions = [
            (1, 0, 0), (-1, 0, 0),
            (0, 1, 0), (0, -1, 0),
            (0, 0, 1), (0, 0, -1),
        ]

        for pt in list(self.voxels.keys()):
            if pt in visited:
                continue

            cluster = []
            queue = deque([pt])
            visited.add(pt)

            while queue:
                curr = queue.popleft()
                cluster.append(curr)

                for dx, dy, dz in directions:
                    neighbor = (curr[0] + dx, curr[1] + dy, curr[2] + dz)
                    if neighbor in self.voxels and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            if len(cluster) < min_cluster_size:
                to_remove.update(cluster)

        for pt in to_remove:
            self.voxels.pop(pt, None)

    def export_json(self, filepath: str) -> None:
        """Export voxel grid to JSON format."""
        data = {
            "species": self.species,
            "seed": self.seed,
            "voxel_count": len(self.voxels),
            "voxels": [
                {"x": k[0], "y": k[1], "z": k[2], "color": v}
                for k, v in self.voxels.items()
            ],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def export_vox(self, filepath: str) -> None:
        """Export voxel grid to MagicaVoxel .vox binary format."""
        if not self.voxels:
            return

        # Shift coordinate bounds so min is 0
        min_x = min(k[0] for k in self.voxels)
        min_y = min(k[1] for k in self.voxels)
        min_z = min(k[2] for k in self.voxels)

        size_x = max(k[0] for k in self.voxels) - min_x + 1
        size_y = max(k[1] for k in self.voxels) - min_y + 1
        size_z = max(k[2] for k in self.voxels) - min_z + 1

        # Palette indexing (1..255)
        unique_colors = list(set(self.voxels.values()))[:254]
        color_map = {c: i + 1 for i, c in enumerate(unique_colors)}

        # Pack XYZI chunk
        num_voxels = len(self.voxels)
        xyzi_payload = bytearray(struct.pack("<I", num_voxels))
        for (vx, vy, vz), col in self.voxels.items():
            cx = max(0, min(255, vx - min_x))
            cy = max(0, min(255, vz - min_z))  # Swap Y and Z for MagicaVoxel coordinate system
            cz = max(0, min(255, vy - min_y))
            pal_idx = color_map.get(col, 1)
            xyzi_payload.extend(struct.pack("BBBB", cx, cy, cz, pal_idx))

        xyzi_chunk = b"XYZI" + struct.pack("<II", len(xyzi_payload), 0) + xyzi_payload
        size_chunk = b"SIZE" + struct.pack("<II", 12, 0) + struct.pack("<III", size_x, size_z, size_y)

        # RGBA palette chunk
        rgba_payload = bytearray()
        for i in range(256):
            if i < len(unique_colors):
                r, g, b = PaletteRegistry.hex_to_rgb(unique_colors[i])
                rgba_payload.extend(struct.pack("BBBB", r, g, b, 255))
            else:
                rgba_payload.extend(b"\x00\x00\x00\xff")
        rgba_chunk = b"RGBA" + struct.pack("<II", 1024, 0) + rgba_payload

        main_children = size_chunk + xyzi_chunk + rgba_chunk
        main_chunk = b"MAIN" + struct.pack("<II", 0, len(main_children)) + main_children

        with open(filepath, "wb") as f:
            f.write(b"VOX ")
            f.write(struct.pack("<I", 150))
            f.write(main_chunk)


def main():
    parser = argparse.ArgumentParser(description="Procedural 3D Voxel Botanical Generator")
    parser.add_argument(
        "--species",
        choices=["sakura", "ginkgo", "bonsai", "succulent", "willow"],
        default="sakura",
        help="Botanical species archetype (default: sakura)",
    )
    parser.add_argument("--iterations", type=int, default=3, help="L-System depth (default: 3)")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic PRNG seed")
    parser.add_argument("--out-json", type=str, default=None, help="Output JSON path")
    parser.add_argument("--out-vox", type=str, default=None, help="Output MagicaVoxel .vox path")
    parser.add_argument("--stats", action="store_true", help="Print voxel bounds and metrics")

    args = parser.parse_args()

    botanist = ProceduralVoxelBotanist(species=args.species, seed=args.seed)
    voxels = botanist.generate(iterations=args.iterations)

    print(f"Generated {len(voxels)} voxels for '{args.species}' (seed={args.seed}).")

    if args.stats and voxels:
        xs = [k[0] for k in voxels]
        ys = [k[1] for k in voxels]
        zs = [k[2] for k in voxels]
        print(f"Bounding Box: X=[{min(xs)}, {max(xs)}] Y=[{min(ys)}, {max(ys)}] Z=[{min(zs)}, {max(zs)}]")
        print(f"Dimensions: {max(xs) - min(xs) + 1}x{max(ys) - min(ys) + 1}x{max(zs) - min(zs) + 1}")

    if args.out_json:
        botanist.export_json(args.out_json)
        print(f"Exported JSON to {args.out_json}")

    if args.out_vox:
        botanist.export_vox(args.out_vox)
        print(f"Exported MagicaVoxel to {args.out_vox}")


if __name__ == "__main__":
    main()
