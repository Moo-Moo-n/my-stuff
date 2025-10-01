"""Core data structures that power the Blackjack counting UI.

This module keeps the bookkeeping responsibilities that the UI relies on so
that the real card counting algorithms can be dropped in later without touching
any of the view code.  The current implementation includes simple default
strategies so the interface behaves sensibly while the final maths are being
implemented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional


class CountingMode(str, Enum):
    """Supported card counting systems."""

    HILO = "HiLo"
    WONG_HALVES = "Wong Halves"


@dataclass
class CountEvent:
    """A single action recorded during a counting session."""

    action: str
    label: str
    running_delta: float

    @property
    def display_text(self) -> str:
        delta = f"{self.running_delta:+g}" if self.running_delta else "0"
        return f"{self.label} ({delta})"


class CountingStrategy:
    """Defines how user interactions translate into count changes."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    def score_action(self, action: str) -> Optional[CountEvent]:
        raise NotImplementedError

    def reset(self) -> None:
        """Hook for strategies that keep internal state."""

    def true_count(self, running_count: float, decks_remaining: float) -> float:
        if decks_remaining <= 0:
            return 0.0
        return running_count / decks_remaining


class MappingStrategy(CountingStrategy):
    """Simple strategy that maps actions directly to running count deltas."""

    def __init__(self, name: str, mapping: Dict[str, float]) -> None:
        super().__init__(name)
        self._mapping = mapping

    def score_action(self, action: str) -> Optional[CountEvent]:
        if action not in self._mapping:
            return None
        delta = self._mapping[action]
        label = action.title()
        return CountEvent(action=action, label=label, running_delta=delta)

    def reset(self) -> None:
        # Stateless strategy.
        return None


class HiLoStrategy(MappingStrategy):
    def __init__(self) -> None:
        super().__init__(
            name=CountingMode.HILO.value,
            mapping={
                "low": 1.0,
                "hi": -1.0,
                "neutral": 0.0,
            },
        )


class WongHalvesStrategy(MappingStrategy):
    def __init__(self) -> None:
        # Values sourced from the traditional Wong Halves system.
        mapping = {
            "low": 0.0,  # Placeholder hook – the final algorithm can customise this.
            "hi": 0.0,
            "2": 0.5,
            "3": 1.0,
            "4": 1.0,
            "5": 1.5,
            "6": 1.0,
            "7": 0.5,
            "8": 0.0,
            "9": -0.5,
            "10": -1.0,
            "j": -1.0,
            "q": -1.0,
            "k": -1.0,
            "a": -1.0,
        }
        super().__init__(name=CountingMode.WONG_HALVES.value, mapping=mapping)


STRATEGY_MAP: Dict[CountingMode, CountingStrategy] = {
    CountingMode.HILO: HiLoStrategy(),
    CountingMode.WONG_HALVES: WongHalvesStrategy(),
}


@dataclass
class CountingSession:
    """Tracks the running state of a counting session."""

    mode: CountingMode
    decks_remaining: float = 1.0
    _strategy: CountingStrategy = field(init=False, repr=False)
    running_count: float = 0.0
    true_count: float = 0.0
    history: List[CountEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._strategy = STRATEGY_MAP[self.mode]

    def reset(self) -> None:
        self.running_count = 0.0
        self.true_count = 0.0
        self.history.clear()
        self._strategy.reset()

    def record_action(self, action: str) -> Optional[CountEvent]:
        event = self._strategy.score_action(action)
        if event is None:
            return None
        self.history.append(event)
        self.running_count += event.running_delta
        self.true_count = self._strategy.true_count(self.running_count, self.decks_remaining)
        return event

    def undo_last(self) -> Optional[CountEvent]:
        if not self.history:
            return None
        event = self.history.pop()
        self.running_count -= event.running_delta
        self.true_count = self._strategy.true_count(self.running_count, self.decks_remaining)
        return event

    def set_decks_remaining(self, decks: float) -> None:
        self.decks_remaining = max(decks, 0.0)
        self.true_count = self._strategy.true_count(self.running_count, self.decks_remaining)

    def iter_history(self) -> Iterable[CountEvent]:
        return iter(self.history)
