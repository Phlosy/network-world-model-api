import pytest
from pydantic import ValidationError

from network_world_model_api import (
    CommunicationTerminalCapability,
    NetworkWorldState,
    Node,
    NodeType,
    Position,
    ScenarioTime,
    SchemaMetadata,
    Velocity,
)


def test_scenario_time_validation():
    st = ScenarioTime(value=12.5, unit="s")
    assert st.value == 12.5
    assert st.unit.value == "s"

    # Value cannot be negative
    with pytest.raises(ValidationError):
        ScenarioTime(value=-1.0, unit="s")


def test_node_enum_validation():
    assert NodeType.SATELLITE.value == "SATELLITE"
    assert NodeType.ROUTER.value == "ROUTER"


def test_submodels():
    pos = Position(
        frame="ECEF",
        x={"value": 6371000.0, "unit": "m"},
        y={"value": 0.0, "unit": "m"},
        z={"value": 0.0, "unit": "m"},
    )
    assert pos.frame == "ECEF"
    assert pos.x.value == 6371000.0


def test_network_world_state_minimal_valid():
    state_dict = {
        "schema": {
            "name": "network-world-state",
            "version": "0.1.0",
        },
        "world_id": "world-test-01",
        "snapshot_id": "snap-12345",
        "scenario_time": {
            "value": 100.0,
            "unit": "s",
        },
        "physical_world": {
            "environment_type": "SPACE",
            "spatial_environment": {
                "default_reference_frame": "ECEF",
            },
            "electromagnetic_environment": {
                "background_noise": {
                    "value": -100.0,
                    "unit": "dBm",
                },
                "interference_regions": [],
            },
        },
        "nodes": [
            {
                "node_id": "sat-01",
                "node_type": "SATELLITE",
                "enabled": True,
                "capabilities": {
                    "communication_terminals": [
                        {
                            "terminal_id": "term-laser-01",
                            "terminal_type": "LASER",
                            "enabled": True,
                            "duplex": "FULL",
                            "max_data_rate": {"value": 10000000000.0, "unit": "bps"},
                        }
                    ]
                },
                "state": {
                    "operational": True,
                    "communication_terminals": [],
                    "position": {
                        "frame": "ECEF",
                        "x": {"value": 6371000.0, "unit": "m"},
                        "y": {"value": 0.0, "unit": "m"},
                        "z": {"value": 0.0, "unit": "m"},
                    },
                    "velocity": {
                        "vx": {"value": 0.0, "unit": "m/s"},
                        "vy": {"value": 7500.0, "unit": "m/s"},
                        "vz": {"value": 0.0, "unit": "m/s"},
                    },
                },
            }
        ],
        "l2_network": {
            "links": [],
        },
        "l3_network": {
            "interfaces": [],
            "logical_links": [],
            "forwarding_entries": [],
        },
        "traffic_resource": {
            "demands": [],
            "flows": [],
            "allocations": [],
        },
        "tasks": [],
        "network_intent": {
            "connectivity": {
                "enabled": True,
                "preserve_global_connectivity": True,
            },
            "task_assurance": {
                "enabled": True,
                "priority_aware": True,
                "preemption_allowed": False,
                "respect_task_qos": True,
            },
            "resource_efficiency": {
                "enabled": True,
                "avoid_congestion": True,
                "load_balance": True,
            },
        },
        "events": [],
        "external_actions": [],
    }

    state = NetworkWorldState.model_validate(state_dict)
    assert state.world_id == "world-test-01"
    assert state.snapshot_id == "snap-12345"
    assert state.schema_.version == "0.1.0"
    assert state.scenario_time.value == 100.0
    assert len(state.nodes) == 1
    assert state.nodes[0].node_id == "sat-01"
    assert state.nodes[0].node_type == NodeType.SATELLITE

    # JSON roundtrip
    json_str = state.model_dump_json(by_alias=True)
    reconstructed = NetworkWorldState.model_validate_json(json_str)
    assert reconstructed.snapshot_id == state.snapshot_id
    assert reconstructed.nodes[0].node_id == "sat-01"
