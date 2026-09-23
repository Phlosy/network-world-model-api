package worldstate_test

import (
	"encoding/json"
	"testing"

	"github.com/Phlosy/network-world-model-api/go/worldstate"
)

func TestEnumValidation(t *testing.T) {
	if !worldstate.CommunicationTerminalCapabilityTerminalTypeLASER.Valid() {
		t.Fatal("expected LASER terminal type to be valid")
	}
	if worldstate.CommunicationTerminalCapabilityTerminalType("INVALID").Valid() {
		t.Fatal("expected INVALID terminal type to be invalid")
	}
	if !worldstate.NodeNodeTypeSATELLITE.Valid() {
		t.Fatal("expected SATELLITE node type to be valid")
	}
}

func TestNetworkWorldStateJSONRoundtrip(t *testing.T) {
	var frame worldstate.FrameRef
	if err := frame.FromNamedFrameRef(worldstate.NamedFrameRef{Name: "ECEF"}); err != nil {
		t.Fatalf("failed to create FrameRef: %v", err)
	}

	timeVal := float32(125.5)
	state := worldstate.NetworkWorldState{
		SnapshotId: "snapshot-001",
		Schema: worldstate.SchemaMetadata{
			Name:    worldstate.SchemaMetadataNameNetworkWorldState,
			Version: "0.1.0",
		},
		ScenarioTime: worldstate.ScenarioTime{
			Value: timeVal,
			Unit:  worldstate.S,
		},
		Nodes: []worldstate.Node{
			{
				NodeId:   "sat-01",
				NodeType: worldstate.NodeNodeTypeSATELLITE,
				Enabled:  true,
				Capabilities: worldstate.NodeCapabilities{
					CommunicationTerminals: []worldstate.CommunicationTerminalCapability{
						{
							TerminalId:   "term-01",
							TerminalType: worldstate.CommunicationTerminalCapabilityTerminalTypeLASER,
							Enabled:      true,
						},
					},
				},
				State: worldstate.NodeState{
					Operational:            true,
					CommunicationTerminals: []worldstate.CommunicationTerminalState{},
					Position: worldstate.Position{
						Frame: frame,
						X: struct {
							Unit  string  `json:"unit"`
							Value float32 `json:"value"`
						}{
							Value: 6371000,
							Unit:  "m",
						},
						Y: struct {
							Unit  string  `json:"unit"`
							Value float32 `json:"value"`
						}{
							Value: 0,
							Unit:  "m",
						},
						Z: struct {
							Unit  string  `json:"unit"`
							Value float32 `json:"value"`
						}{
							Value: 0,
							Unit:  "m",
						},
					},
					Velocity: worldstate.Velocity{
						Vx: struct {
							Unit  string  `json:"unit"`
							Value float32 `json:"value"`
						}{
							Value: 0,
							Unit:  "m/s",
						},
						Vy: struct {
							Unit  string  `json:"unit"`
							Value float32 `json:"value"`
						}{
							Value: 7500,
							Unit:  "m/s",
						},
						Vz: struct {
							Unit  string  `json:"unit"`
							Value float32 `json:"value"`
						}{
							Value: 0,
							Unit:  "m/s",
						},
					},
				},
			},
		},
	}

	data, err := json.Marshal(state)
	if err != nil {
		t.Fatalf("failed to marshal NetworkWorldState: %v", err)
	}

	var decoded worldstate.NetworkWorldState
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("failed to unmarshal NetworkWorldState: %v", err)
	}

	if decoded.SnapshotId != "snapshot-001" {
		t.Fatalf("expected snapshot-001, got %s", decoded.SnapshotId)
	}
	if decoded.Schema.Version != "0.1.0" {
		t.Fatalf("expected version 0.1.0, got %s", decoded.Schema.Version)
	}
	if decoded.ScenarioTime.Value != timeVal {
		t.Fatalf("expected scenario time %f, got %f", timeVal, decoded.ScenarioTime.Value)
	}
	if len(decoded.Nodes) != 1 {
		t.Fatalf("expected 1 node, got %d", len(decoded.Nodes))
	}
	if decoded.Nodes[0].NodeId != "sat-01" {
		t.Fatalf("expected node_id sat-01, got %s", decoded.Nodes[0].NodeId)
	}
	if len(decoded.Nodes[0].Capabilities.CommunicationTerminals) != 1 {
		t.Fatalf("expected 1 terminal capability")
	}
}

// P1 additive revision: vendored time/frame/environment components plus the
// NWM-native TimeBase / ObservationStamp / Provenance / Availability.
func TestVendoredTimeAndFrameComponents(t *testing.T) {
	if !worldstate.TimeScaleUTC.Valid() {
		t.Fatal("expected UTC to be a valid time scale")
	}
	if worldstate.InstantScale("LOCAL").Valid() {
		t.Fatal("expected LOCAL to be an invalid time scale")
	}
	if !worldstate.AvailabilityObserved.Valid() {
		t.Fatal("expected observed to be a valid availability state")
	}
	if worldstate.AvailabilityState("maybe").Valid() {
		t.Fatal("expected maybe to be an invalid availability state")
	}

	epoch := worldstate.Instant{Value: "2026-01-01T00:00:00", Scale: worldstate.TimeScaleUTC}
	base := worldstate.TimeBase{ScenarioEpoch: epoch, SimulationStart: epoch}
	if data, err := json.Marshal(base); err != nil {
		t.Fatalf("marshal TimeBase: %v", err)
	} else {
		var back worldstate.TimeBase
		if err := json.Unmarshal(data, &back); err != nil {
			t.Fatalf("unmarshal TimeBase: %v", err)
		}
		if back.ScenarioEpoch.Scale != worldstate.TimeScaleUTC {
			t.Fatalf("expected UTC scale, got %s", back.ScenarioEpoch.Scale)
		}
		if back.ScenarioEpoch.Value != "2026-01-01T00:00:00" {
			t.Fatalf("unexpected instant value %s", back.ScenarioEpoch.Value)
		}
	}

	// FrameRef is a discriminated union: the discriminator must round-trip and
	// select the right branch.
	var named worldstate.FrameRef
	if err := named.FromNamedFrameRef(worldstate.NamedFrameRef{Name: "ecef"}); err != nil {
		t.Fatalf("FromNamedFrameRef: %v", err)
	}
	if disc, err := named.Discriminator(); err != nil || disc != "NamedFrame" {
		t.Fatalf("expected NamedFrame discriminator, got %q err=%v", disc, err)
	}
	namedData, err := json.Marshal(named)
	if err != nil {
		t.Fatalf("marshal FrameRef: %v", err)
	}
	var decoded worldstate.FrameRef
	if err := json.Unmarshal(namedData, &decoded); err != nil {
		t.Fatalf("unmarshal FrameRef: %v", err)
	}
	resolved, err := decoded.AsNamedFrameRef()
	if err != nil {
		t.Fatalf("AsNamedFrameRef: %v", err)
	}
	if resolved.Name != "ecef" {
		t.Fatalf("expected frame name ecef, got %s", resolved.Name)
	}

	var body worldstate.FrameRef
	if err := body.FromNodeBodyFrameRef(worldstate.NodeBodyFrameRef{Node: "sat-01"}); err != nil {
		t.Fatalf("FromNodeBodyFrameRef: %v", err)
	}
	if disc, err := body.Discriminator(); err != nil || disc != "NodeBodyFrame" {
		t.Fatalf("expected NodeBodyFrame discriminator, got %q err=%v", disc, err)
	}

	// BodyShape carries the geodetic datum.
	var shape worldstate.BodyShape
	if err := shape.FromOblateEllipsoidBodyShape(worldstate.OblateEllipsoidBodyShape{
		SemiMajorAxisM:    6378137,
		InverseFlattening: 298.257223563,
	}); err != nil {
		t.Fatalf("FromOblateEllipsoidBodyShape: %v", err)
	}
	if disc, err := shape.Discriminator(); err != nil || disc != "OblateEllipsoid" {
		t.Fatalf("expected OblateEllipsoid discriminator, got %q err=%v", disc, err)
	}

	// Position format must stay explicit; geodetic requires an environment body.
	var format worldstate.ObservationPositionFormat
	if err := format.FromGeodeticObservationFormat(
		worldstate.GeodeticObservationFormat{Body: "earth"},
	); err != nil {
		t.Fatalf("FromGeodeticObservationFormat: %v", err)
	}
	if disc, err := format.Discriminator(); err != nil || disc != "Geodetic" {
		t.Fatalf("expected Geodetic discriminator, got %q err=%v", disc, err)
	}
}

func TestAdditiveObservabilityFieldsRoundTrip(t *testing.T) {
	coverage := float32(0.75)
	state := worldstate.NetworkWorldState{
		Schema: worldstate.SchemaMetadata{
			Name:    worldstate.SchemaMetadataNameNetworkWorldState,
			Version: "0.1.0",
		},
		WorldId:    "world-p1",
		SnapshotId: "snapshot-p1",
		ScenarioTime: worldstate.ScenarioTime{
			Value: float32(12.5),
			Unit:  worldstate.S,
		},
		TimeBase: &worldstate.TimeBase{
			ScenarioEpoch:   worldstate.Instant{Value: "2026-01-01T00:00:00", Scale: worldstate.TimeScaleUTC},
			SimulationStart: worldstate.Instant{Value: "2026-01-01T00:00:00", Scale: worldstate.TimeScaleUTC},
		},
		Availability: &worldstate.Availability{
			State:         worldstate.AvailabilityUnavailable,
			CoverageRatio: &coverage,
			Partial:       boolPtr(true),
			Reason:        strPtr("source_unsupported"),
		},
		Provenance: &worldstate.Provenance{
			SourceSystem: "generic-gse",
			Adapter:      strPtr("generic_gse_v1"),
		},
		Nodes: []worldstate.Node{
			{
				NodeId:   "sat-01",
				NodeType: worldstate.NodeNodeTypeSATELLITE,
				Enabled:  true,
				State: worldstate.NodeState{
					Operational: true,
					Stamp: &worldstate.ObservationStamp{
						SourceSystem: "generic-gse",
						Sampling:     samplingPtr(worldstate.SamplingPrevious),
					},
				},
			},
		},
	}

	data, err := json.Marshal(state)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	var decoded worldstate.NetworkWorldState
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}
	if decoded.TimeBase == nil || decoded.TimeBase.ScenarioEpoch.Scale != worldstate.TimeScaleUTC {
		t.Fatal("time_base did not round-trip")
	}
	if decoded.Availability == nil || decoded.Availability.State != worldstate.AvailabilityUnavailable {
		t.Fatal("root availability did not round-trip")
	}
	if decoded.Provenance == nil || decoded.Provenance.SourceSystem != "generic-gse" {
		t.Fatal("provenance did not round-trip")
	}
	if decoded.Nodes[0].State.Stamp == nil {
		t.Fatal("node state stamp did not round-trip")
	}
	if *decoded.Nodes[0].State.Stamp.Sampling != worldstate.SamplingPrevious {
		t.Fatal("sampling policy did not round-trip")
	}
}

func boolPtr(v bool) *bool { return &v }

func strPtr(v string) *string { return &v }

func samplingPtr(v worldstate.ObservationStampSampling) *worldstate.ObservationStampSampling {
	return &v
}

func TestB2AdditionsAndModifications(t *testing.T) {
	// 1. AngularVelocityBodyRadS and ThroughputBps
	angVel := worldstate.Vec3{0.01, 0.02, 0.03}
	throughput := float32(2.5e9)
	link := worldstate.L2Link{
		LinkId:        "link-1",
		Enabled:       true,
		EndpointA:     worldstate.L2Endpoint{NodeId: "sat-01", TerminalId: "t1"},
		EndpointB:     worldstate.L2Endpoint{NodeId: "sat-02", TerminalId: "t2"},
		LinkClass:     worldstate.L2LinkLinkClassISL,
		Medium:        worldstate.L2LinkMediumLASER,
		Operational:   true,
		Status:        worldstate.L2LinkStatusUP,
		ThroughputBps: &throughput,
	}
	if link.ThroughputBps == nil || *link.ThroughputBps != throughput {
		t.Fatalf("expected throughput %f, got %v", throughput, link.ThroughputBps)
	}

	nodeState := worldstate.NodeState{
		Operational:             true,
		CommunicationTerminals:  []worldstate.CommunicationTerminalState{},
		AngularVelocityBodyRadS: &angVel,
	}
	if nodeState.AngularVelocityBodyRadS == nil || (*nodeState.AngularVelocityBodyRadS)[0] != 0.01 {
		t.Fatalf("expected angular velocity 0.01, got %v", nodeState.AngularVelocityBodyRadS)
	}

	// 2. RequirementSatisfactionState & SatisfactionState enum
	sat := worldstate.SatisfactionStateSatisfied
	inProg := worldstate.SatisfactionStateInProgress
	viol := worldstate.SatisfactionStateViolated
	unknown := worldstate.SatisfactionStateUnknown

	if !sat.Valid() || !inProg.Valid() || !viol.Valid() || !unknown.Valid() {
		t.Fatal("expected satisfaction state enum values to be valid")
	}

	reqSat := worldstate.RequirementSatisfactionState{
		OverallSatisfied:     &sat,
		LatencySatisfied:     &sat,
		ReliabilitySatisfied: &inProg,
		ThroughputSatisfied:  &viol,
		DeadlineSatisfied:    &unknown,
	}

	data, err := json.Marshal(reqSat)
	if err != nil {
		t.Fatalf("marshal reqSat: %v", err)
	}

	var decoded worldstate.RequirementSatisfactionState
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal reqSat: %v", err)
	}

	if *decoded.OverallSatisfied != worldstate.SatisfactionStateSatisfied {
		t.Fatalf("expected SATISFIED, got %v", *decoded.OverallSatisfied)
	}
	if *decoded.ReliabilitySatisfied != worldstate.SatisfactionStateInProgress {
		t.Fatalf("expected IN_PROGRESS, got %v", *decoded.ReliabilitySatisfied)
	}
	if *decoded.ThroughputSatisfied != worldstate.SatisfactionStateViolated {
		t.Fatalf("expected VIOLATED, got %v", *decoded.ThroughputSatisfied)
	}
}
