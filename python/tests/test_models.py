import pytest
from pydantic import ValidationError

from network_world_model_api import (
    CommunicationTerminalCapability,
    FrameRef,
    L2Link,
    NamedFrameRef,
    NetworkWorldState,
    Node,
    NodeBodyFrameRef,
    NodeState,
    NodeType,
    Position,
    RequirementSatisfactionState,
    SatisfactionState,
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
        frame=NamedFrameRef(type="NamedFrame", name="ECEF"),
        x={"value": 6371000.0, "unit": "m"},
        y={"value": 0.0, "unit": "m"},
        z={"value": 0.0, "unit": "m"},
    )
    assert pos.frame.root.name == "ECEF"
    assert pos.x.value == 6371000.0

    # Bare string must be rejected
    with pytest.raises(ValidationError):
        Position(
            frame="ECEF",
            x={"value": 6371000.0, "unit": "m"},
            y={"value": 0.0, "unit": "m"},
            z={"value": 0.0, "unit": "m"},
        )


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
                "default_reference_frame": {"type": "NamedFrame", "name": "ECEF"},
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
                        "frame": {"type": "NamedFrame", "name": "ECEF"},
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


# --------------------------------------------------------------------------- #
# P1 additive revision: vendored time/frame/environment components plus the
# NWM-native TimeBase / ObservationStamp / Provenance / Availability.
# --------------------------------------------------------------------------- #
from network_world_model_api import (  # noqa: E402
    Availability,
    BodyShape,
    CartesianObservationFormat,
    EnvironmentBody,
    FrameRef,
    GeodeticObservationFormat,
    Instant,
    NamedFrameRef,
    NodeBodyFrameRef,
    ObservationPositionFormat,
    ObservationStamp,
    OblateEllipsoidBodyShape,
    Provenance,
    ReferenceFrame,
    SphereBodyShape,
    TimeBase,
    UniformRotationFrameTransform,
    Vec3,
)


def test_instant_rejects_timezone_suffix_and_unknown_scale():
    instant = Instant(value="2026-01-01T00:00:00", scale="UTC")
    assert instant.scale.value == "UTC"

    # A timezone suffix must be rejected: the scale carries that meaning.
    with pytest.raises(ValidationError):
        Instant(value="2026-01-01T00:00:00Z", scale="UTC")

    with pytest.raises(ValidationError):
        Instant(value="2026-01-01T00:00:00", scale="LOCAL")


def test_time_base_requires_both_anchors():
    epoch = Instant(value="2026-01-01T00:00:00", scale="UTC")
    base = TimeBase(scenario_epoch=epoch, simulation_start=epoch, tick_s=0.1)
    assert base.tick_s == pytest.approx(0.1)

    with pytest.raises(ValidationError):
        TimeBase(scenario_epoch=epoch)

    with pytest.raises(ValidationError):
        TimeBase(scenario_epoch=epoch, simulation_start=epoch, tick_s=0)


def test_availability_requires_state_and_bounds_coverage():
    availability = Availability(state="unavailable", coverage_ratio=0.5, partial=True)
    assert availability.state.value == "unavailable"

    with pytest.raises(ValidationError):
        Availability(state="maybe")

    with pytest.raises(ValidationError):
        Availability(state="observed", coverage_ratio=1.5)


def test_observation_stamp_rejects_unknown_sampling():
    stamp = ObservationStamp(source_system="generic-gse", sampling="Previous")
    assert stamp.sampling.value == "Previous"

    with pytest.raises(ValidationError):
        ObservationStamp()

    with pytest.raises(ValidationError):
        ObservationStamp(source_system="generic-gse", sampling="Nearestish")


def test_provenance_requires_source_system():
    provenance = Provenance(source_system="kubenet", adapter="generic_gse_v1")
    assert provenance.adapter == "generic_gse_v1"

    with pytest.raises(ValidationError):
        Provenance()


def test_frame_ref_discriminated_union_selects_branch():
    named = FrameRef.model_validate({"type": "NamedFrame", "name": "ecef"})
    assert isinstance(named.root, NamedFrameRef)
    assert named.root.name == "ecef"

    body = FrameRef.model_validate({"type": "NodeBodyFrame", "node": "sat-01"})
    assert isinstance(body.root, NodeBodyFrameRef)
    assert body.root.node == "sat-01"

    with pytest.raises(ValidationError):
        FrameRef.model_validate({"type": "Relative", "name": "ecef"})


def test_position_format_union_keeps_geodetic_body_mandatory():
    cartesian = ObservationPositionFormat.model_validate({"type": "Cartesian"})
    assert isinstance(cartesian.root, CartesianObservationFormat)

    geodetic = ObservationPositionFormat.model_validate({"type": "Geodetic", "body": "earth"})
    assert isinstance(geodetic.root, GeodeticObservationFormat)
    assert geodetic.root.body == "earth"

    with pytest.raises(ValidationError):
        ObservationPositionFormat.model_validate({"type": "Geodetic"})


def test_body_shape_union_and_environment_body_projection():
    sphere = BodyShape.model_validate({"type": "Sphere", "radius_m": 6371000.0})
    assert isinstance(sphere.root, SphereBodyShape)

    ellipsoid = BodyShape.model_validate(
        {
            "type": "OblateEllipsoid",
            "semi_major_axis_m": 6378137.0,
            "inverse_flattening": 298.257223563,
        }
    )
    assert isinstance(ellipsoid.root, OblateEllipsoidBodyShape)

    body = EnvironmentBody.model_validate(
        {
            "name": "earth",
            "shape": ellipsoid.model_dump(),
            "inertial_frame": {"type": "NamedFrame", "name": "earth-inertial"},
            "fixed_frame": {"type": "NamedFrame", "name": "ecef"},
        }
    )
    assert body.name == "earth"
    assert body.fixed_frame.root.name == "ecef"


def test_reference_frame_with_parent_and_transform_union():
    frame = ReferenceFrame.model_validate(
        {
            "name": "ecef",
            "parent": {"type": "NamedFrame", "name": "earth-inertial"},
            "transform": {
                "type": "UniformRotation",
                "epoch": {"value": "2026-01-01T00:00:00", "scale": "UTC"},
                "origin_parent_m": [0.0, 0.0, 0.0],
                "axis_parent": [0.0, 0.0, 1.0],
                "rate_rad_s": 7.292115e-5,
                "phase_at_epoch_rad": 0.0,
            },
        }
    )
    assert isinstance(frame.transform.root, UniformRotationFrameTransform)
    assert frame.transform.root.rate_rad_s == pytest.approx(7.292115e-5)


def test_vec3_and_quaternion_are_length_checked():
    assert Vec3.model_validate([1.0, 2.0, 3.0]).root == [1.0, 2.0, 3.0]
    with pytest.raises(ValidationError):
        Vec3.model_validate([1.0, 2.0])


def test_additive_observability_fields_round_trip():
    state_dict = {
        "schema": {"name": "network-world-state", "version": "0.1.0"},
        "world_id": "world-p1",
        "snapshot_id": "snapshot-p1",
        "scenario_time": {"value": 12.5, "unit": "s"},
        "time_base": {
            "scenario_epoch": {"value": "2026-01-01T00:00:00", "scale": "UTC"},
            "simulation_start": {"value": "2026-01-01T00:00:00", "scale": "UTC"},
            "tick_s": 0.1,
        },
        "availability": {"state": "observed", "coverage_ratio": 1.0},
        "provenance": {"source_system": "generic-gse", "adapter_version": "generic_gse_v1@1"},
        "physical_world": {
            "environment_type": "SPACE",
            "spatial_environment": {
                "default_reference_frame": {"type": "NamedFrame", "name": "ecef"},
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
                "capabilities": {"communication_terminals": []},
                "state": {
                    "operational": True,
                    "communication_terminals": [],
                    "position": {
                        "frame": {"type": "NamedFrame", "name": "ECEF"},
                        "x": {"value": 6371000.0, "unit": "m"},
                        "y": {"value": 0.0, "unit": "m"},
                        "z": {"value": 0.0, "unit": "m"},
                    },
                    "velocity": {
                        "vx": {"value": 0.0, "unit": "m/s"},
                        "vy": {"value": 7500.0, "unit": "m/s"},
                        "vz": {"value": 0.0, "unit": "m/s"},
                    },
                    "stamp": {
                        "source_system": "generic-gse",
                        "observed_at_instant": {"value": "2026-01-01T00:00:00", "scale": "TAI"},
                        "sampling": "Exact",
                    },
                },
            }
        ],
        "l2_network": {
            "links": [
                {
                    "link_id": "l1",
                    "enabled": True,
                    "endpoint_a": {"node_id": "sat-01", "terminal_id": "t1"},
                    "endpoint_b": {"node_id": "sat-02", "terminal_id": "t2"},
                    "link_class": "ISL",
                    "medium": "LASER",
                    "max_capacity": {"value": 1e9, "unit": "bps"},
                    "operational": True,
                    "status": "UP",
                    "capacity": {"value": 1e9, "unit": "bps"},
                    "available_bandwidth": {"value": 1e9, "unit": "bps"},
                    "utilization": 0.0,
                    "propagation_delay": {"value": 0.005, "unit": "s"},
                    "jitter": {"value": 0.0001, "unit": "s"},
                    "packet_loss_rate": 0.0,
                    "availability": {"state": "unavailable", "reason": "queue_metrics_not_streamed"},
                }
            ]
        },
        "l3_network": {"interfaces": [], "logical_links": [], "forwarding_entries": []},
        "traffic_resource": {"demands": [], "flows": [], "allocations": []},
        "tasks": [],
        "network_intent": {
            "connectivity": {"enabled": True, "preserve_global_connectivity": True},
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
    assert state.time_base.scenario_epoch.scale.value == "UTC"
    assert state.availability.state.value == "observed"
    assert state.provenance.adapter_version == "generic_gse_v1@1"
    assert state.nodes[0].state.stamp.sampling.value == "Exact"
    assert state.l2_network.links[0].availability.reason == "queue_metrics_not_streamed"

    reconstructed = NetworkWorldState.model_validate_json(state.model_dump_json(by_alias=True))
    assert reconstructed.time_base.tick_s == pytest.approx(0.1)
    assert reconstructed.nodes[0].state.stamp.source_system == "generic-gse"
    assert reconstructed.l2_network.links[0].availability.state.value == "unavailable"


def test_every_contract_schema_is_exported_from_the_package():
    """Guard against the hand-maintained export list drifting from the contract.

    `__init__.py` is not generated, so a new contract schema silently stays
    unreachable until someone updates it. That happened for every P1 addition.
    """
    import json
    import pathlib

    import network_world_model_api

    spec_path = pathlib.Path(__file__).resolve().parents[2] / "contracts/openapi/network-world-state.openapi.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    schema_names = set(spec["components"]["schemas"])

    missing = sorted(name for name in schema_names if not hasattr(network_world_model_api, name))
    assert missing == [], f"contract schemas missing from the package: {missing}"

    unexported = sorted(schema_names - set(network_world_model_api.__all__))
    assert unexported == [], f"contract schemas not listed in __all__: {unexported}"


def test_b2_angular_velocity_and_link_throughput():
    pos = Position(
        frame=NamedFrameRef(type="NamedFrame", name="ECEF"),
        x={"value": 6371000.0, "unit": "m"},
        y={"value": 0.0, "unit": "m"},
        z={"value": 0.0, "unit": "m"},
    )
    vel = Velocity(
        vx={"value": 0.0, "unit": "m/s"},
        vy={"value": 7500.0, "unit": "m/s"},
        vz={"value": 0.0, "unit": "m/s"},
    )
    node_state = NodeState(
        operational=True,
        communication_terminals=[],
        position=pos,
        velocity=vel,
        angular_velocity_body_rad_s=[0.01, 0.02, 0.03],
    )
    assert node_state.angular_velocity_body_rad_s.root == [0.01, 0.02, 0.03]

    with pytest.raises(ValidationError):
        NodeState(
            operational=True,
            communication_terminals=[],
            position=pos,
            velocity=vel,
            angular_velocity_body_rad_s=[0.01, 0.02],
        )

    link_data = {
        "link_id": "link-isl-01",
        "enabled": True,
        "endpoint_a": {"node_id": "sat-01", "terminal_id": "term-01"},
        "endpoint_b": {"node_id": "sat-02", "terminal_id": "term-02"},
        "link_class": "ISL",
        "medium": "LASER",
        "max_capacity": {"value": 10e9, "unit": "bps"},
        "operational": True,
        "status": "UP",
        "capacity": {"value": 10e9, "unit": "bps"},
        "available_bandwidth": {"value": 8e9, "unit": "bps"},
        "utilization": 0.2,
        "propagation_delay": {"value": 0.01, "unit": "s"},
        "jitter": {"value": 0.001, "unit": "s"},
        "packet_loss_rate": 0.0,
        "throughput_bps": 2e9,
    }
    link = L2Link.model_validate(link_data)
    assert link.throughput_bps == 2e9

    invalid_link_data = dict(link_data, throughput_bps=-1.0)
    with pytest.raises(ValidationError):
        L2Link.model_validate(invalid_link_data)


def test_b2_tri_state_requirement_satisfaction():
    sat = RequirementSatisfactionState(
        overall_satisfied=SatisfactionState.SatisfactionStateSatisfied,
        latency_satisfied=SatisfactionState.SatisfactionStateSatisfied,
        reliability_satisfied=SatisfactionState.SatisfactionStateInProgress,
        throughput_satisfied=SatisfactionState.SatisfactionStateViolated,
        deadline_satisfied=SatisfactionState.SatisfactionStateUnknown,
    )
    assert sat.overall_satisfied == SatisfactionState.SatisfactionStateSatisfied
    assert sat.reliability_satisfied.value == "IN_PROGRESS"
    assert sat.throughput_satisfied.value == "VIOLATED"

    data = sat.model_dump_json()
    reconstructed = RequirementSatisfactionState.model_validate_json(data)
    assert reconstructed.reliability_satisfied == SatisfactionState.SatisfactionStateInProgress
    assert reconstructed.throughput_satisfied == SatisfactionState.SatisfactionStateViolated
