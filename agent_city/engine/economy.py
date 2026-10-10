"""Tri-resource economy engine: Funds, Energy, Materials, Municipal Treasury, and Taxation."""

from __future__ import annotations

import time
import uuid
from collections import deque
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field

from agent_city.config import DEFAULT_CONFIG, SimulationConfig


class ResourceLedger(BaseModel):
    """Holds a tri-resource balance: funds, energy, materials."""
    funds: float = Field(default=0.0, description="Financial currency balance ($)")
    energy: float = Field(default=0.0, description="Operational vitality balance (⚡)")
    materials: float = Field(default=0.0, description="Physical construction resources (📦)")

    def has_sufficient(
        self,
        funds: float = 0.0,
        energy: float = 0.0,
        materials: float = 0.0,
    ) -> bool:
        """Check if ledger contains at least the requested amounts."""
        if funds < 0 or energy < 0 or materials < 0:
            return False
        return (
            self.funds >= funds - 1e-9
            and self.energy >= energy - 1e-9
            and self.materials >= materials - 1e-9
        )

    def deposit(
        self,
        funds: float = 0.0,
        energy: float = 0.0,
        materials: float = 0.0,
    ) -> bool:
        """Deposit resources into ledger. Rejects negative amounts."""
        if funds < 0 or energy < 0 or materials < 0:
            return False
        self.funds = round(self.funds + funds, 4)
        self.energy = round(self.energy + energy, 4)
        self.materials = round(self.materials + materials, 4)
        return True

    def withdraw(
        self,
        funds: float = 0.0,
        energy: float = 0.0,
        materials: float = 0.0,
    ) -> bool:
        """
        Atomically withdraw resources if balance is sufficient.
        Returns True on success, False with no state mutation if any resource is insufficient or negative.
        """
        if funds < 0 or energy < 0 or materials < 0:
            return False
        if not self.has_sufficient(funds=funds, energy=energy, materials=materials):
            return False
        self.funds = round(max(0.0, self.funds - funds), 4)
        self.energy = round(max(0.0, self.energy - energy), 4)
        self.materials = round(max(0.0, self.materials - materials), 4)
        return True

    def to_dict(self) -> Dict[str, float]:
        """Convert ledger to dictionary."""
        return {
            "funds": round(self.funds, 4),
            "energy": round(self.energy, 4),
            "materials": round(self.materials, 4),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> ResourceLedger:
        """Create ledger from dictionary."""
        return cls(
            funds=data.get("funds", 0.0),
            energy=data.get("energy", 0.0),
            materials=data.get("materials", 0.0),
        )


class Transaction(BaseModel):
    """Immutable record of an economic transfer between entities or city treasury."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    tick: int = Field(default=0)
    timestamp: float = Field(default_factory=time.time)
    sender_id: str
    recipient_id: str
    amount: float
    resource_type: str = Field(default="funds")  # "funds", "energy", "materials"
    category: str = Field(default="COMMERCIAL_TRADE")
    tax_collected: float = Field(default=0.0)
    net_amount: float = Field(default=0.0)
    description: str = Field(default="")

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary."""
        return self.model_dump(mode="json")


ALLOWED_RESOURCES = {"funds", "energy", "materials"}


class EconomySystem:
    """Manages the municipal treasury, citizen/business ledgers, taxation, and trade."""

    def __init__(self, config: Optional[SimulationConfig] = None):
        cfg = config or DEFAULT_CONFIG
        self.config = cfg
        self.treasury = ResourceLedger(
            funds=cfg.initial_treasury_funds,
            energy=cfg.initial_treasury_energy,
            materials=cfg.initial_treasury_materials,
        )
        self.accounts: Dict[str, ResourceLedger] = {}
        self.sales_tax_rate: float = cfg.default_sales_tax_rate
        self.property_tax_per_building: float = cfg.property_tax_per_building
        self.total_tax_collected: float = 0.0
        self.transaction_history: deque[Transaction] = deque(maxlen=500)

    def register_account(
        self,
        account_id: str,
        funds: Optional[float] = None,
        energy: Optional[float] = None,
        materials: Optional[float] = None,
    ) -> ResourceLedger:
        """Register a new citizen/subagent ledger with starting balances."""
        ledger = ResourceLedger(
            funds=funds if funds is not None else self.config.default_agent_funds,
            energy=energy if energy is not None else self.config.default_agent_energy,
            materials=materials if materials is not None else self.config.default_agent_materials,
        )
        self.accounts[account_id] = ledger
        return ledger

    def unregister_account(self, account_id: str) -> Optional[ResourceLedger]:
        """Unregister an account and return its final ledger."""
        return self.accounts.pop(account_id, None)

    def get_ledger(self, account_id: str) -> Optional[ResourceLedger]:
        """Retrieve ledger by account ID or None."""
        if account_id == "treasury":
            return self.treasury
        return self.accounts.get(account_id)

    def get_or_create_ledger(self, account_id: str) -> ResourceLedger:
        """Retrieve ledger or initialize with defaults if not found."""
        if account_id == "treasury":
            return self.treasury
        if account_id not in self.accounts:
            return self.register_account(account_id)
        return self.accounts[account_id]

    def transfer(
        self,
        sender_id: str,
        recipient_id: str,
        amount: float,
        resource: str = "funds",
        category: str = "COMMERCIAL_TRADE",
        tick: int = 0,
        description: str = "",
    ) -> Optional[Transaction]:
        """
        Transfer funds, energy, or materials between accounts or the treasury.
        Deducts sales tax into treasury for commercial transactions.
        """
        if resource not in ALLOWED_RESOURCES:
            return None
        if amount <= 0:
            return None

        sender = self.get_or_create_ledger(sender_id)
        recipient = self.get_or_create_ledger(recipient_id)

        # Check sufficiency on sender
        kwargs_sender = {resource: amount}
        if not sender.has_sufficient(**kwargs_sender):
            return None

        # Compute tax
        tax = 0.0
        if category == "COMMERCIAL_TRADE" and resource == "funds":
            tax = round(amount * self.sales_tax_rate, 4)

        net_amount = round(amount - tax, 4)

        # Execute balance update
        sender.withdraw(**kwargs_sender)
        recipient.deposit(**{resource: net_amount})

        if tax > 0:
            self.treasury.deposit(funds=tax)
            self.total_tax_collected = round(self.total_tax_collected + tax, 4)

        tx = Transaction(
            tick=tick,
            sender_id=sender_id,
            recipient_id=recipient_id,
            amount=amount,
            resource_type=resource,
            category=category,
            tax_collected=tax,
            net_amount=net_amount,
            description=description,
        )
        self.transaction_history.append(tx)
        return tx

    def disburse_grant(
        self,
        recipient_id: str,
        amount: float,
        resource: str = "funds",
        tick: int = 0,
        description: str = "Civic Grant",
    ) -> bool:
        """Disburse funds or resources directly from the municipal treasury."""
        if resource not in ALLOWED_RESOURCES:
            return False
        if amount <= 0:
            return False
        if not self.treasury.has_sufficient(**{resource: amount}):
            return False

        self.treasury.withdraw(**{resource: amount})
        recipient = self.get_or_create_ledger(recipient_id)
        recipient.deposit(**{resource: amount})

        tx = Transaction(
            tick=tick,
            sender_id="treasury",
            recipient_id=recipient_id,
            amount=amount,
            resource_type=resource,
            category="GRANT",
            tax_collected=0.0,
            net_amount=amount,
            description=description,
        )
        self.transaction_history.append(tx)
        return True

    def charge_maintenance(
        self,
        cost: float,
        tick: int = 0,
        description: str = "Infrastructure Maintenance",
    ) -> bool:
        """Deduct municipal infrastructure maintenance from treasury."""
        if cost <= 0:
            return True
        if not self.treasury.has_sufficient(funds=cost):
            # Treasury deficit / austerity warning
            actual = self.treasury.funds
            self.treasury.funds = 0.0
            tx = Transaction(
                tick=tick,
                sender_id="treasury",
                recipient_id="maintenance_depot",
                amount=actual,
                resource_type="funds",
                category="MAINTENANCE",
                tax_collected=0.0,
                net_amount=actual,
                description=f"{description} (Deficit: {round(cost - actual, 2)})",
            )
            self.transaction_history.append(tx)
            return False

        self.treasury.withdraw(funds=cost)
        tx = Transaction(
            tick=tick,
            sender_id="treasury",
            recipient_id="maintenance_depot",
            amount=cost,
            resource_type="funds",
            category="MAINTENANCE",
            tax_collected=0.0,
            net_amount=cost,
            description=description,
        )
        self.transaction_history.append(tx)
        return True

    def collect_property_taxes(
        self,
        parcels_with_buildings: List[Tuple[str, str]],
        tick: int = 0,
    ) -> float:
        """
        Assess and collect epoch property tax from building owners.
        parcels_with_buildings is a list of (owner_id, building_id).
        """
        total_collected = 0.0
        tax_rate = self.property_tax_per_building

        for owner_id, b_id in parcels_with_buildings:
            if not owner_id or owner_id == "public":
                continue
            owner_ledger = self.get_ledger(owner_id)
            if owner_ledger is None:
                continue

            # Pay up to tax_rate or whatever owner has
            assessed = min(tax_rate, owner_ledger.funds)
            if assessed > 0:
                owner_ledger.withdraw(funds=assessed)
                self.treasury.deposit(funds=assessed)
                self.total_tax_collected += assessed
                total_collected += assessed

                tx = Transaction(
                    tick=tick,
                    sender_id=owner_id,
                    recipient_id="treasury",
                    amount=assessed,
                    resource_type="funds",
                    category="PROPERTY_TAX",
                    tax_collected=assessed,
                    net_amount=assessed,
                    description=f"Property Tax for building {b_id}",
                )
                self.transaction_history.append(tx)

        return round(total_collected, 2)

    def consume_agent_energy(
        self,
        agent_id: str,
        burn_amount: float,
        tick: int = 0,
    ) -> float:
        """
        Deduct energy from an agent's ledger.
        Returns the remaining energy balance.
        """
        ledger = self.get_or_create_ledger(agent_id)
        if burn_amount <= 0:
            return ledger.energy
        ledger.energy = round(max(0.0, ledger.energy - burn_amount), 4)
        return ledger.energy

    def replenish_agent_energy(
        self,
        agent_id: str,
        amount: float,
        tick: int = 0,
    ) -> float:
        """Replenish agent energy (e.g. resting at Residential zone)."""
        ledger = self.get_or_create_ledger(agent_id)
        if amount <= 0:
            return ledger.energy
        ledger.energy = round(min(self.config.default_agent_energy, ledger.energy + amount), 4)
        return ledger.energy

    def get_metrics(self) -> Dict[str, Any]:
        """Aggregate high-level macroeconomic statistics."""
        circulating_funds = sum(acc.funds for acc in self.accounts.values())
        total_energy = sum(acc.energy for acc in self.accounts.values())
        total_materials = sum(acc.materials for acc in self.accounts.values())

        return {
            "treasury": self.treasury.to_dict(),
            "circulating_funds": round(circulating_funds, 2),
            "total_citizen_energy": round(total_energy, 2),
            "total_citizen_materials": round(total_materials, 2),
            "total_tax_collected": round(self.total_tax_collected, 2),
            "active_accounts_count": len(self.accounts),
            "recent_transactions_count": len(self.transaction_history),
        }

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize economy state for persistence."""
        return {
            "treasury": self.treasury.to_dict(),
            "accounts": {k: v.to_dict() for k, v in self.accounts.items()},
            "sales_tax_rate": self.sales_tax_rate,
            "property_tax_per_building": self.property_tax_per_building,
            "total_tax_collected": round(self.total_tax_collected, 2),
            "transactions": [tx.to_dict() for tx in self.transaction_history],
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        config: Optional[SimulationConfig] = None,
    ) -> EconomySystem:
        """Restore economy system from serialized dictionary."""
        eco = cls(config=config)
        eco.treasury = ResourceLedger.from_dict(data.get("treasury", {}))
        eco.sales_tax_rate = data.get("sales_tax_rate", eco.sales_tax_rate)
        eco.property_tax_per_building = data.get(
            "property_tax_per_building", eco.property_tax_per_building
        )
        eco.total_tax_collected = data.get("total_tax_collected", 0.0)

        eco.accounts = {
            k: ResourceLedger.from_dict(v)
            for k, v in data.get("accounts", {}).items()
        }
        eco.transaction_history = deque(
            [Transaction.model_validate(t) for t in data.get("transactions", [])],
            maxlen=500,
        )
        return eco
