"""2D Spatial Grid, Parcels, Terrain Costs, Weighted A* Pathfinding, and Projections."""

from __future__ import annotations

import heapq
import math
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field

from agent_city.config import DEFAULT_CONFIG, ZoneType


class Parcel(BaseModel):
    """Represents a single discrete spatial parcel (tile) within the city grid."""
    x: int
    y: int
    zone: ZoneType = Field(default=ZoneType.WILDERNESS)
    passable: bool = Field(default=True)
    terrain_cost: float = Field(default=2.0)
    building_id: Optional[str] = Field(default=None)
    building_type: Optional[str] = Field(default=None)
    level: int = Field(default=0)
    occupant_id: Optional[str] = Field(default=None)
    resource_yield: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert parcel to dictionary representation."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Parcel:
        """Create parcel from dictionary representation."""
        return cls.model_validate(data)


class CityGrid:
    """2D spatial grid managing parcel zoning, occupancy, collisions, and pathfinding."""

    def __init__(
        self,
        width: int = DEFAULT_CONFIG.grid_width,
        height: int = DEFAULT_CONFIG.grid_height,
        terrain_costs: Optional[Dict[ZoneType, float]] = None,
    ):
        self.width: int = width
        self.height: int = height
        self.terrain_costs: Dict[ZoneType, float] = (
            terrain_costs or DEFAULT_CONFIG.terrain_costs
        )
        # 2D array of Parcels: grid[y][x]
        self._grid: List[List[Parcel]] = [
            [
                Parcel(
                    x=x,
                    y=y,
                    zone=ZoneType.WILDERNESS,
                    passable=True,
                    terrain_cost=self.terrain_costs.get(ZoneType.WILDERNESS, 2.0),
                )
                for x in range(width)
            ]
            for y in range(height)
        ]
        # Fast spatial index for agent positions: agent_id -> (x, y)
        self._agent_positions: Dict[str, Tuple[int, int]] = {}
        # Fast index for building parcels: building_id -> List[(x, y)]
        self._building_parcels: Dict[str, List[Tuple[int, int]]] = {}

    def is_valid_coord(self, x: int, y: int) -> bool:
        """Check if coordinates fall within grid boundaries."""
        if type(x) is not int or type(y) is not int:
            return False
        return 0 <= x < self.width and 0 <= y < self.height

    def get_parcel(self, x: int, y: int) -> Optional[Parcel]:
        """Get parcel at (x, y) or None if out of bounds."""
        if not self.is_valid_coord(x, y):
            return None
        return self._grid[y][x]

    def set_zone(
        self,
        x: int,
        y: int,
        zone: ZoneType,
        update_cost: bool = True,
    ) -> Optional[Parcel]:
        """Set zoning type for parcel and optionally update default terrain cost."""
        parcel = self.get_parcel(x, y)
        if parcel is None:
            return None
        parcel.zone = zone
        if update_cost:
            parcel.terrain_cost = self.terrain_costs.get(zone, 2.0)
        return parcel

    def set_building(
        self,
        x: int,
        y: int,
        building_id: str,
        building_type: Optional[str] = None,
        passable: bool = False,
        level: int = 1,
    ) -> Optional[Parcel]:
        """Place a building on a parcel."""
        parcel = self.get_parcel(x, y)
        if parcel is None:
            return None
        parcel.building_id = building_id
        parcel.building_type = building_type or parcel.zone.value
        parcel.passable = passable
        parcel.level = level

        if building_id not in self._building_parcels:
            self._building_parcels[building_id] = []
        if (x, y) not in self._building_parcels[building_id]:
            self._building_parcels[building_id].append((x, y))
        return parcel

    def remove_building(self, x: int, y: int) -> Optional[Parcel]:
        """Remove building from a parcel and restore passability."""
        parcel = self.get_parcel(x, y)
        if parcel is None or parcel.building_id is None:
            return parcel

        b_id = parcel.building_id
        if b_id in self._building_parcels:
            for bx, by in list(self._building_parcels[b_id]):
                bp = self.get_parcel(bx, by)
                if bp is not None:
                    bp.building_id = None
                    bp.building_type = None
                    bp.passable = True
                    bp.level = 0
            del self._building_parcels[b_id]
        else:
            parcel.building_id = None
            parcel.building_type = None
            parcel.passable = True
            parcel.level = 0
        return parcel

    def place_multi_tile_building(
        self,
        building_id: str,
        building_type: str,
        top_left_x: int,
        top_left_y: int,
        width: int,
        height: int,
        entrance_offset: Tuple[int, int] = (0, 0),
        zone: Optional[ZoneType] = None,
    ) -> bool:
        """
        Place a multi-tile structure. All covered tiles are marked with building_id
        and passable=False, except the entrance offset tile which remains passable.
        """
        if width <= 0 or height <= 0:
            return False

        # First verify entire footprint is valid, unbuilt, and unoccupied
        for dy in range(height):
            for dx in range(width):
                px = top_left_x + dx
                py = top_left_y + dy
                parcel = self.get_parcel(px, py)
                if (
                    parcel is None
                    or parcel.building_id is not None
                    or parcel.occupant_id is not None
                ):
                    return False

        # Place tiles
        for dy in range(height):
            for dx in range(width):
                px = top_left_x + dx
                py = top_left_y + dy
                is_entrance = (dx, dy) == entrance_offset
                if zone:
                    self.set_zone(px, py, zone)
                self.set_building(
                    px,
                    py,
                    building_id=building_id,
                    building_type=building_type,
                    passable=is_entrance,
                    level=1,
                )
        return True

    def can_move_to(self, x: int, y: int, agent_id: Optional[str] = None) -> bool:
        """
        Validate whether an agent can move to parcel (x, y).
        Must be within bounds, marked passable, and either unoccupied or occupied by self.
        """
        parcel = self.get_parcel(x, y)
        if parcel is None:
            return False
        if not parcel.passable:
            return False
        if parcel.occupant_id is not None and parcel.occupant_id != agent_id:
            return False
        return True

    def set_occupant(self, x: int, y: int, occupant_id: Optional[str]) -> bool:
        """Directly set or clear occupant on parcel (x, y)."""
        parcel = self.get_parcel(x, y)
        if parcel is None:
            return False

        if occupant_id is not None:
            if parcel.occupant_id is not None and parcel.occupant_id != occupant_id:
                return False  # Collision: already occupied by someone else

            # Clear previous position if recorded elsewhere
            if occupant_id in self._agent_positions:
                old_x, old_y = self._agent_positions[occupant_id]
                if (old_x, old_y) != (x, y):
                    old_parcel = self.get_parcel(old_x, old_y)
                    if old_parcel and old_parcel.occupant_id == occupant_id:
                        old_parcel.occupant_id = None

            parcel.occupant_id = occupant_id
            self._agent_positions[occupant_id] = (x, y)
        else:
            old_occupant = parcel.occupant_id
            parcel.occupant_id = None
            if old_occupant and old_occupant in self._agent_positions:
                if self._agent_positions[old_occupant] == (x, y):
                    del self._agent_positions[old_occupant]
        return True

    def move_occupant(
        self,
        from_x: int,
        from_y: int,
        to_x: int,
        to_y: int,
        agent_id: str,
    ) -> bool:
        """
        Atomically move an occupant from (from_x, from_y) to (to_x, to_y).
        Ensures collision prevention, 1-step cardinal adjacency, and maintains spatial position index.
        """
        if abs(to_x - from_x) + abs(to_y - from_y) != 1:
            return False

        if not self.can_move_to(to_x, to_y, agent_id):
            return False

        from_parcel = self.get_parcel(from_x, from_y)
        if from_parcel is None or from_parcel.occupant_id != agent_id:
            return False

        to_parcel = self.get_parcel(to_x, to_y)
        if to_parcel is None:
            return False

        # Atomic handoff
        from_parcel.occupant_id = None
        to_parcel.occupant_id = agent_id
        self._agent_positions[agent_id] = (to_x, to_y)
        return True

    def teleport_occupant(self, to_x: int, to_y: int, agent_id: str) -> bool:
        """Move agent to new coordinates regardless of prior position."""
        if not self.can_move_to(to_x, to_y, agent_id):
            return False

        # Clear previous position if recorded
        if agent_id in self._agent_positions:
            old_x, old_y = self._agent_positions[agent_id]
            old_parcel = self.get_parcel(old_x, old_y)
            if old_parcel and old_parcel.occupant_id == agent_id:
                old_parcel.occupant_id = None

        to_parcel = self.get_parcel(to_x, to_y)
        if to_parcel is None:
            return False
        to_parcel.occupant_id = agent_id
        self._agent_positions[agent_id] = (to_x, to_y)
        return True

    def remove_occupant(self, agent_id: str) -> bool:
        """Remove agent from the grid and clear occupancy."""
        if agent_id not in self._agent_positions:
            return False
        x, y = self._agent_positions.pop(agent_id)
        parcel = self.get_parcel(x, y)
        if parcel and parcel.occupant_id == agent_id:
            parcel.occupant_id = None
        return True

    def get_occupant(self, x: int, y: int) -> Optional[str]:
        """Get agent ID occupying parcel (x, y) or None."""
        parcel = self.get_parcel(x, y)
        return parcel.occupant_id if parcel else None

    def find_agent_pos(self, agent_id: str) -> Optional[Tuple[int, int]]:
        """Look up coordinates of an agent by ID."""
        return self._agent_positions.get(agent_id)

    def get_neighbors(
        self,
        x: int,
        y: int,
        allow_diagonal: bool = False,
    ) -> List[Tuple[int, int]]:
        """Return valid adjacent neighboring parcel coordinates."""
        cardinals = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        if allow_diagonal:
            cardinals.extend(
                [(x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x - 1, y - 1)]
            )
        return [
            (nx, ny)
            for nx, ny in cardinals
            if self.is_valid_coord(nx, ny)
        ]

    def get_terrain_cost(self, x: int, y: int) -> float:
        """Get effective movement cost for parcel (x, y). Returns infinity if impassable."""
        parcel = self.get_parcel(x, y)
        if parcel is None or not parcel.passable:
            return math.inf
        return parcel.terrain_cost

    def find_path(
        self,
        start: Tuple[int, int],
        target: Tuple[int, int],
        agent_id: Optional[str] = None,
        ignore_target_occupancy: bool = True,
        max_nodes: int = 4000,
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Weighted A* Pathfinding with 4-directional cardinal movement.
        Heuristic: Manhattan Distance |x1 - x2| + |y1 - y2|.
        Edge weights: Parcel terrain costs (Road=1.0, Park=1.5, Wilderness=2.0, etc.).
        Returns the sequence of coordinates from start to target inclusive, or None if unreachable.
        """
        start_x, start_y = start
        target_x, target_y = target

        if not self.is_valid_coord(start_x, start_y) or not self.is_valid_coord(target_x, target_y):
            return None

        # If already at destination
        if start == target:
            return [start]

        target_parcel = self.get_parcel(target_x, target_y)
        if target_parcel is None or not target_parcel.passable:
            return None

        # Check target occupancy
        if not ignore_target_occupancy and target_parcel.occupant_id is not None:
            if target_parcel.occupant_id != agent_id:
                return None

        # A* Data structures
        # Priority queue stores: (f_score, tie_breaker, current_coord)
        counter = 0
        h_start = abs(start_x - target_x) + abs(start_y - target_y)
        open_set: List[Tuple[float, int, Tuple[int, int]]] = [(h_start, counter, start)]
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}

        g_score: Dict[Tuple[int, int], float] = {start: 0.0}
        f_score: Dict[Tuple[int, int], float] = {start: h_start}
        closed_set: set[Tuple[int, int]] = set()

        nodes_explored = 0

        while open_set and nodes_explored < max_nodes:
            current_f, _, current = heapq.heappop(open_set)
            nodes_explored += 1

            if current == target:
                # Reconstruct path
                path: List[Tuple[int, int]] = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            closed_set.add(current)
            cx, cy = current

            for neighbor in self.get_neighbors(cx, cy, allow_diagonal=False):
                if neighbor in closed_set:
                    continue

                nx, ny = neighbor
                is_target = (nx, ny) == target

                # Collision check for intermediate steps
                if not is_target:
                    if not self.can_move_to(nx, ny, agent_id):
                        continue
                else:
                    # Neighbor is the target
                    n_parcel = self.get_parcel(nx, ny)
                    if n_parcel is None or not n_parcel.passable:
                        continue
                    if not ignore_target_occupancy and n_parcel.occupant_id is not None and n_parcel.occupant_id != agent_id:
                        continue

                n_parcel = self.get_parcel(nx, ny)
                step_cost = n_parcel.terrain_cost if n_parcel else 2.0
                tentative_g = g_score[current] + step_cost

                if tentative_g < g_score.get(neighbor, math.inf):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h_val = abs(nx - target_x) + abs(ny - target_y)
                    f_val = tentative_g + h_val
                    f_score[neighbor] = f_val

                    counter += 1
                    heapq.heappush(open_set, (f_val, counter, neighbor))

        return None  # No viable path found within max_nodes

    # =========================================================================
    # Coordinate Projection Math (Isometric & Orthographic)
    # =========================================================================

    @staticmethod
    def to_isometric(
        x: float,
        y: float,
        tile_width: float = 64.0,
        tile_height: float = 32.0,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
    ) -> Tuple[float, float]:
        """
        Transform 2D grid coordinates (x, y) into 2.5D Isometric screen space.
        Screen X = (x - y) * (tile_width / 2) + origin_x
        Screen Y = (x + y) * (tile_height / 2) + origin_y
        """
        screen_x = (x - y) * (tile_width / 2.0) + origin_x
        screen_y = (x + y) * (tile_height / 2.0) + origin_y
        return screen_x, screen_y

    @staticmethod
    def from_isometric(
        screen_x: float,
        screen_y: float,
        tile_width: float = 64.0,
        tile_height: float = 32.0,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
    ) -> Tuple[float, float]:
        """
        Inverse isometric projection from screen coordinates back to continuous grid coordinates.
        """
        sx = (screen_x - origin_x) / (tile_width / 2.0)
        sy = (screen_y - origin_y) / (tile_height / 2.0)
        x = (sx + sy) / 2.0
        y = (sy - sx) / 2.0
        return x, y

    @staticmethod
    def to_orthographic(
        x: float,
        y: float,
        cell_size: float = 24.0,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
    ) -> Tuple[float, float]:
        """Transform 2D grid coordinates (x, y) into 2D CAD Orthographic screen space."""
        return x * cell_size + origin_x, y * cell_size + origin_y

    @staticmethod
    def from_orthographic(
        screen_x: float,
        screen_y: float,
        cell_size: float = 24.0,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
    ) -> Tuple[float, float]:
        """Inverse orthographic projection from screen coordinates back to grid coordinates."""
        return (screen_x - origin_x) / cell_size, (screen_y - origin_y) / cell_size

    @staticmethod
    def get_depth_key(x: int, y: int) -> int:
        """Calculate isometric rendering depth order key (x + y)."""
        return x + y

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Export grid to dictionary for state serialization."""
        return {
            "width": self.width,
            "height": self.height,
            "parcels": [
                [self._grid[y][x].to_dict() for x in range(self.width)]
                for y in range(self.height)
            ],
            "agent_positions": {k: list(v) for k, v in self._agent_positions.items()},
            "building_parcels": {k: [list(pt) for pt in v] for k, v in self._building_parcels.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CityGrid:
        """Construct CityGrid from serialized dictionary."""
        grid = cls(width=data["width"], height=data["height"])
        for y, row in enumerate(data.get("parcels", [])):
            for x, p_data in enumerate(row):
                grid._grid[y][x] = Parcel.from_dict(p_data)

        grid._agent_positions = {
            k: (v[0], v[1]) for k, v in data.get("agent_positions", {}).items()
        }
        grid._building_parcels = {
            k: [(pt[0], pt[1]) for pt in v]
            for k, v in data.get("building_parcels", {}).items()
        }
        return grid
