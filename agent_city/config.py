"""Global configuration settings, enums, and simulation constants for agent_city."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any
from pydantic import BaseModel, Field


class ZoneType(str, Enum):
    """City zoning types for spatial parcels."""
    WILDERNESS = "WILDERNESS"    # Natural undeveloped ground (passable, terrain cost 2.0)
    ROAD = "ROAD"                # Transit network (passable, terrain cost 1.0)
    RESIDENTIAL = "RESIDENTIAL"  # Housing and vitality regeneration
    COMMERCIAL = "COMMERCIAL"    # Trade and commercial activity
    INDUSTRIAL = "INDUSTRIAL"    # Resource generation and manufacturing
    CIVIC = "CIVIC"              # City Hall, Research Institute, Governance
    PARK = "PARK"                # Recreation and vitality (terrain cost 1.5)


class SimulationState(str, Enum):
    """Coordinator lifecycle execution state."""
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STEPPING = "STEPPING"


class MessageType(str, Enum):
    """Categorization for agent communication."""
    DIRECT = "DIRECT"
    BROADCAST = "BROADCAST"
    TOPIC = "TOPIC"
    PROPOSAL = "PROPOSAL"
    VOTE = "VOTE"
    TASK_ORDER = "TASK_ORDER"
    REPORT = "REPORT"


class VoteChoice(str, Enum):
    """Civic proposal ballot choices."""
    AYE = "AYE"
    NAY = "NAY"
    ABSTAIN = "ABSTAIN"


class ProposalStatus(str, Enum):
    """Status lifecycle for civic legislative proposals."""
    ACTIVE = "ACTIVE"
    PASSED = "PASSED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"


class SimulationConfig(BaseModel):
    """Simulation configuration parameters with defaults."""
    # Spatial Grid
    grid_width: int = Field(default=32, description="Horizontal tile count")
    grid_height: int = Field(default=32, description="Vertical tile count")
    iso_tile_width: float = Field(default=64.0, description="Isometric tile pixel width")
    iso_tile_height: float = Field(default=32.0, description="Isometric tile pixel height")
    ortho_cell_size: float = Field(default=24.0, description="Orthographic 2D cell pixel size")

    # Tick & Timing
    default_tps: float = Field(default=5.0, description="Default ticks per second (0.2s tick)")
    min_tps: float = Field(default=0.5, description="Minimum allowable TPS")
    max_tps: float = Field(default=25.0, description="Maximum allowable TPS")
    ticks_per_epoch: int = Field(default=100, description="Number of ticks in one simulation epoch")

    # Terrain Costs
    terrain_costs: Dict[ZoneType, float] = Field(
        default_factory=lambda: {
            ZoneType.ROAD: 1.0,
            ZoneType.PARK: 1.5,
            ZoneType.WILDERNESS: 2.0,
            ZoneType.RESIDENTIAL: 2.0,
            ZoneType.COMMERCIAL: 2.0,
            ZoneType.INDUSTRIAL: 2.5,
            ZoneType.CIVIC: 1.8,
        }
    )

    # Economy & Treasury
    initial_treasury_funds: float = Field(default=5000.0, description="Initial city treasury funds ($)")
    initial_treasury_energy: float = Field(default=1000.0, description="Initial city grid energy (⚡)")
    initial_treasury_materials: float = Field(default=500.0, description="Initial city materials stockpile (📦)")
    default_sales_tax_rate: float = Field(default=0.05, description="5% tax on commercial transactions")
    property_tax_per_building: float = Field(default=10.0, description="Property tax per building per epoch")
    zoning_permit_cost: float = Field(default=50.0, description="Base fee to rezone a wilderness parcel")

    # Agent Baseline Budgets & Consumption
    default_agent_funds: float = Field(default=150.0, description="Default starting agent funds")
    default_agent_energy: float = Field(default=100.0, description="Max/starting agent energy")
    default_agent_materials: float = Field(default=20.0, description="Default starting agent materials")
    energy_burn_idle: float = Field(default=0.2, description="Energy consumed per tick while idle")
    energy_burn_move: float = Field(default=0.5, description="Energy consumed per tick while moving")
    energy_burn_work: float = Field(default=1.0, description="Energy consumed per tick while constructing/laboring")
    energy_regen_residential: float = Field(default=2.5, description="Energy regenerated per tick resting at home")

    # Consensus Voting
    default_proposal_duration_ticks: int = Field(default=20, description="Ticks before a proposal expires")
    default_quorum_ratio: float = Field(default=0.50, description="Minimum ratio of voters required for quorum")
    default_pass_threshold: float = Field(default=0.50, description="Ratio of affirmative votes (>50%) to pass")

    def get_tick_interval(self, tps: float | None = None) -> float:
        """Return the tick interval in seconds for a given TPS."""
        rate = tps if tps is not None else self.default_tps
        rate = max(self.min_tps, min(self.max_tps, rate))
        return 1.0 / rate


# Default shared singleton instance
DEFAULT_CONFIG = SimulationConfig()
