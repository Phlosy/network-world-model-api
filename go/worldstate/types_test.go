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
						Frame: "ECEF",
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
