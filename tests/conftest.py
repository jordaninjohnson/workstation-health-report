"""Small deterministic inventory fixture; no personal host probing."""

from __future__ import annotations

import copy

import pytest

from workstation_health.demo import synthetic_observation


@pytest.fixture
def inventory() -> dict:
    return copy.deepcopy(synthetic_observation("healthy")["inventory"])
