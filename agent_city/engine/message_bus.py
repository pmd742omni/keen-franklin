"""Asynchronous Inter-Agent Message Bus, Topic Pub/Sub, and Democratic Consensus Voting."""

from __future__ import annotations

import inspect
import time
import uuid
from collections import deque
from typing import Callable, Dict, List, Optional, Set, Any
from pydantic import BaseModel, Field

from agent_city.config import DEFAULT_CONFIG, MessageType, ProposalStatus, VoteChoice


class AgentMessage(BaseModel):
    """Structured message transmitted across the city message bus."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    tick: int = Field(default=0)
    timestamp: float = Field(default_factory=time.time)
    sender_id: str
    sender_role: str = Field(default="CITIZEN")
    recipient_id: Optional[str] = Field(default=None)  # None for broadcast / topic
    topic: Optional[str] = Field(default=None)        # e.g., "governance", "trade"
    type: MessageType = Field(default=MessageType.BROADCAST)
    content: str = Field(default="")
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return self.model_dump(mode="json")


class CivicProposal(BaseModel):
    """Civic legislative proposal submitted to the municipal council for voting."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    creator_id: str
    title: str
    description: str
    action_type: str  # e.g., "REZONE", "ADJUST_TAX", "BUILD_PUBLIC_WORKS", "DISBURSE_GRANT"
    action_payload: Dict[str, Any] = Field(default_factory=dict)
    created_tick: int = Field(default=0)
    expires_tick: int = Field(default=20)
    votes: Dict[str, VoteChoice] = Field(default_factory=dict)  # voter_id -> choice
    status: ProposalStatus = Field(default=ProposalStatus.ACTIVE)
    quorum_required: int = Field(default=3)
    pass_threshold_ratio: float = Field(default=0.50)  # > 50% AYE to pass

    @property
    def aye_count(self) -> int:
        return sum(1 for v in self.votes.values() if v == VoteChoice.AYE)

    @property
    def nay_count(self) -> int:
        return sum(1 for v in self.votes.values() if v == VoteChoice.NAY)

    @property
    def abstain_count(self) -> int:
        return sum(1 for v in self.votes.values() if v == VoteChoice.ABSTAIN)

    @property
    def total_votes(self) -> int:
        return len(self.votes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert proposal to dictionary."""
        res = self.model_dump(mode="json")
        res["aye_count"] = self.aye_count
        res["nay_count"] = self.nay_count
        res["abstain_count"] = self.abstain_count
        res["total_votes"] = self.total_votes
        return res


class MessageBus:
    """In-memory asynchronous message broker supporting 1:1, broadcast, topics, and voting."""

    def __init__(self):
        # agent_id -> list of pending messages
        self.mailboxes: Dict[str, List[AgentMessage]] = {}
        # topic_name -> set of subscriber agent_ids
        self.subscriptions: Dict[str, Set[str]] = {
            "general": set(),
            "governance": set(),
            "trade": set(),
            "construction": set(),
            "research": set(),
        }
        # Rolling broadcast and speech bubble feed for UI streaming
        self.broadcast_log: deque[AgentMessage] = deque(maxlen=200)
        self.dialogue_feed: deque[AgentMessage] = deque(maxlen=100)

        # Consensus Proposals
        self.proposals: Dict[str, CivicProposal] = {}
        # action_type -> list of callback functions
        self.proposal_callbacks: Dict[str, List[Callable[[CivicProposal], Any]]] = {}

    def _normalize_topic(self, topic: str) -> str:
        """Strip leading '#' and convert to lowercase."""
        return topic.lstrip("#").lower().strip()

    def register_agent(self, agent_id: str) -> None:
        """Initialize mailbox and default subscriptions for a new agent."""
        if agent_id not in self.mailboxes:
            self.mailboxes[agent_id] = []
        # Auto-subscribe to general channel
        self.subscriptions["general"].add(agent_id)

    def unregister_agent(self, agent_id: str) -> None:
        """Remove agent mailbox and clean up topic subscriptions."""
        self.mailboxes.pop(agent_id, None)
        for sub_set in self.subscriptions.values():
            sub_set.discard(agent_id)

    def subscribe(self, agent_id: str, topic: str) -> bool:
        """Subscribe agent to a specific topic channel."""
        norm_topic = self._normalize_topic(topic)
        if norm_topic not in self.subscriptions:
            self.subscriptions[norm_topic] = set()
        self.subscriptions[norm_topic].add(agent_id)
        return True

    def unsubscribe(self, agent_id: str, topic: str) -> bool:
        """Unsubscribe agent from a topic channel."""
        norm_topic = self._normalize_topic(topic)
        if norm_topic in self.subscriptions:
            self.subscriptions[norm_topic].discard(agent_id)
            return True
        return False

    def get_subscriptions(self, agent_id: str) -> List[str]:
        """Return list of topic channels an agent is subscribed to."""
        return [
            topic for topic, subs in self.subscriptions.items()
            if agent_id in subs
        ]

    def send_direct(self, message: AgentMessage) -> bool:
        """Deliver a 1:1 message to a specific recipient agent."""
        if not message.recipient_id:
            return False
        message.type = MessageType.DIRECT
        if message.recipient_id not in self.mailboxes:
            self.register_agent(message.recipient_id)
        self.mailboxes[message.recipient_id].append(message)
        return True

    def broadcast(self, message: AgentMessage) -> int:
        """
        Broadcast a city-wide public announcement.
        Logs to broadcast and dialogue feed, and delivers to all active agent mailboxes.
        """
        message.type = MessageType.BROADCAST
        self.broadcast_log.append(message)
        if message.content:
            self.dialogue_feed.append(message)

        delivered = 0
        for agent_id, box in self.mailboxes.items():
            if agent_id != message.sender_id:
                box.append(message)
                delivered += 1
        return delivered

    def publish(self, topic: str, message: AgentMessage) -> int:
        """
        Publish a message to all subscribers of a topic channel.
        """
        norm_topic = self._normalize_topic(topic)
        message.type = MessageType.TOPIC
        message.topic = norm_topic

        # If general or governance with dialogue content, also mirror to dialogue feed
        if norm_topic in ("general", "governance") and message.content:
            self.dialogue_feed.append(message)

        if norm_topic not in self.subscriptions:
            self.subscriptions[norm_topic] = set()

        delivered = 0
        for agent_id in self.subscriptions[norm_topic]:
            if agent_id != message.sender_id and agent_id in self.mailboxes:
                self.mailboxes[agent_id].append(message)
                delivered += 1
        return delivered

    def drain_inbox(self, agent_id: str) -> List[AgentMessage]:
        """Drain and clear all queued messages for an agent."""
        if agent_id not in self.mailboxes:
            return []
        msgs = self.mailboxes[agent_id]
        self.mailboxes[agent_id] = []
        return msgs

    def get_recent_dialogues(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent speech bubble and dialogue events."""
        items = list(self.dialogue_feed)[-limit:]
        return [msg.to_dict() for msg in items]

    # =========================================================================
    # Democratic Consensus Voting & Proposals
    # =========================================================================

    def submit_proposal(self, proposal: CivicProposal) -> str:
        """Register a new civic proposal and announce it on the governance channel."""
        self.proposals[proposal.id] = proposal

        # Broadcast proposal announcement to #governance channel
        announcement = AgentMessage(
            tick=proposal.created_tick,
            sender_id=proposal.creator_id,
            sender_role="MAYOR" if "mayor" in proposal.creator_id.lower() else "COUNCIL",
            topic="governance",
            type=MessageType.PROPOSAL,
            content=f"Proposed bill: '{proposal.title}' ({proposal.action_type}). Quorum={proposal.quorum_required}.",
            payload={"proposal_id": proposal.id, "action_type": proposal.action_type},
        )
        self.publish("governance", announcement)
        return proposal.id

    def cast_vote(
        self,
        proposal_id: str,
        voter_id: str,
        vote: VoteChoice,
    ) -> bool:
        """Cast a ballot for an active proposal."""
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.status != ProposalStatus.ACTIVE:
            return False

        proposal.votes[voter_id] = vote
        return True

    def register_proposal_callback(
        self,
        action_type: str,
        callback: Callable[[CivicProposal], Any],
    ) -> None:
        """Register an execution handler triggered when a proposal passes."""
        if action_type not in self.proposal_callbacks:
            self.proposal_callbacks[action_type] = []
        self.proposal_callbacks[action_type].append(callback)

    async def _execute_proposal_callbacks(self, proposal: CivicProposal) -> None:
        """Invoke all registered callbacks for a passed proposal."""
        callbacks = self.proposal_callbacks.get(proposal.action_type, [])
        for cb in callbacks:
            try:
                res = cb(proposal)
                if inspect.isawaitable(res):
                    await res
            except Exception as e:
                print(f"[MessageBus] Error executing proposal callback for {proposal.id}: {e}")

    async def evaluate_proposals(self, current_tick: int) -> List[CivicProposal]:
        """
        Evaluate active proposals. Determines pass/fail on expiration or quorum reach.
        Returns list of newly resolved proposals.
        """
        resolved: List[CivicProposal] = []

        for p in list(self.proposals.values()):
            if p.status != ProposalStatus.ACTIVE:
                continue

            expired = current_tick >= p.expires_tick
            # If all active voters or sufficient quorum voted, can evaluate early
            quorum_met = p.total_votes >= p.quorum_required

            if expired or quorum_met:
                if p.total_votes < p.quorum_required:
                    # Expired without quorum
                    p.status = ProposalStatus.EXPIRED
                    resolved.append(p)
                else:
                    # Tally votes (excluding abstentions for ratio)
                    effective_votes = p.aye_count + p.nay_count
                    if effective_votes == 0:
                        p.status = ProposalStatus.REJECTED
                    else:
                        aye_ratio = p.aye_count / float(effective_votes)
                        if aye_ratio > p.pass_threshold_ratio:
                            p.status = ProposalStatus.PASSED
                            await self._execute_proposal_callbacks(p)
                            p.status = ProposalStatus.EXECUTED
                        else:
                            p.status = ProposalStatus.REJECTED
                    resolved.append(p)

                # Announce outcome to #governance
                outcome_msg = AgentMessage(
                    tick=current_tick,
                    sender_id="city_council",
                    sender_role="COUNCIL",
                    topic="governance",
                    type=MessageType.REPORT,
                    content=f"Proposal '{p.title}' resolved: {p.status.value} (AYE={p.aye_count}, NAY={p.nay_count}, ABSTAIN={p.abstain_count}).",
                    payload={"proposal_id": p.id, "status": p.status.value},
                )
                self.publish("governance", outcome_msg)

        return resolved

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize message bus state."""
        return {
            "subscriptions": {k: list(v) for k, v in self.subscriptions.items()},
            "proposals": {k: v.to_dict() for k, v in self.proposals.items()},
            "dialogue_feed": [m.to_dict() for m in self.dialogue_feed],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MessageBus:
        """Restore message bus from serialized dictionary."""
        bus = cls()
        bus.subscriptions = {
            k: set(v) for k, v in data.get("subscriptions", {}).items()
        }
        bus.proposals = {
            k: CivicProposal.model_validate(v)
            for k, v in data.get("proposals", {}).items()
        }
        bus.dialogue_feed = deque(
            [AgentMessage.model_validate(m) for m in data.get("dialogue_feed", [])],
            maxlen=100,
        )
        return bus
