"""Loads and validates agents.yaml and infra.yaml at service startup."""

from __future__ import annotations

from pathlib import Path

import yaml

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _load_agents() -> dict:
    path = _CONFIG_DIR / "agents.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def _load_infra() -> dict:
    path = _CONFIG_DIR / "infra.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def validate_streams() -> None:
    """Raise ValueError if any agent references a stream not declared in infra.yaml."""
    agents_cfg = _load_agents()
    infra_cfg = _load_infra()

    declared_streams: list[str] = infra_cfg.get("redis", {}).get("streams", [])
    declared_streams_set = set(declared_streams)

    agents: dict = agents_cfg.get("agents", {}) or {}
    errors: list[str] = []

    for agent_name, agent_cfg in agents.items():
        agent_stream = (agent_cfg or {}).get("stream")
        if agent_stream is None:
            errors.append(f"Agent '{agent_name}' has no 'stream' defined in agents.yaml")
        elif agent_stream not in declared_streams_set:
            errors.append(
                f"Agent '{agent_name}' references stream '{agent_stream}' "
                f"which is not declared in infra.yaml. "
                f"Declared streams: {sorted(declared_streams_set)}"
            )

    if errors:
        raise ValueError("Stream configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
