"""Job board API adapters."""

from app.adapters.base import JobBoardAdapter
from app.adapters.greenhouse import GreenhouseAdapter
from app.adapters.lever import LeverAdapter
from app.adapters.remoteok import RemoteOKAdapter

__all__ = ["JobBoardAdapter", "GreenhouseAdapter", "LeverAdapter", "RemoteOKAdapter"]
