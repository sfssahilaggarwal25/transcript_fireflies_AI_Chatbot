"""
_tool_utils.py — Backward-compatibility shim.

All implementation has moved to utils/:
  utils/constants.py   signal maps, thresholds, formatters
  utils/presets.py     RETRIEVAL_PRESETS, select_preset
  utils/accumulator.py per-request doc collection
  utils/expansion.py   neighbor chunk expansion
  utils/search.py      speaker resolver, exhaustive scan, diversity cap

New code should import from .utils directly.
"""
from .utils import *  # noqa: F401, F403