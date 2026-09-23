# Network World Model API

[![CI](https://github.com/Phlosy/network-world-model-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Phlosy/network-world-model-api/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Phlosy/network-world-model-api)](https://github.com/Phlosy/network-world-model-api/releases)

Language-independent OpenAPI source of truth for the **Network World Model** (protocol-agnostic, scenario-agnostic Network World State data contracts) and official SDK distributions for **Go** and **Python**.

Modeled after modern OpenAPI monorepo engineering patterns (such as `astra-emu-api`), all language artifacts are generated deterministically from a single authoritative contract, versioned together, and guarded by anti-drift CI workflows.

---

## 📁 Repository Layout

- [`contracts/openapi/`](contracts/openapi/): Contains the authoritative OpenAPI 3.0.3 data contract (`network-world-state.openapi.json`).
- [`go/`](go/): The `github.com/Phlosy/network-world-model-api/go` Go module. Provides generated Go models, strict enums, validators, and JSON serialization.
- [`python/`](python/): The `network-world-model-api` Python package. Provides generated Pydantic v2 data models with PEP 561 typing support.
- [`.github/workflows/`](.github/workflows/): GitHub Actions CI (contract lint, unit tests, and `make verify` anti-drift gate) and Release pipelines.
- [`scripts/`](scripts/): Version management and multi-tag release automation (`release.sh`).
- [`tools/`](tools/): Normalization and OpenAPI maintenance utilities.
- [`VERSION`](VERSION): Plain `X.Y.Z` semantic version shared by all distributions.

---

## 📦 How to Consume

### 1. Go Projects

The Go module lives in the `go/` subdirectory and follows the Go standard for multi-module repositories with the `go/vX.Y.Z` tag scheme:

```bash
# Add or update the Go module
go get github.com/Phlosy/network-world-model-api/go@v0.1.0
```

Import in your Go code:

```go
package main

import (
    "encoding/json"
    "fmt"
    "github.com/Phlosy/network-world-model-api/go/worldstate"
)

func main() {
    state := worldstate.NetworkWorldState{
        SnapshotId: "snap-001",
        Schema: worldstate.SchemaMetadata{
            Name:    worldstate.SchemaMetadataNameNetworkWorldState,
            Version: "0.1.0",
        },
    }
    data, _ := json.Marshal(state)
    fmt.Println(string(data))
}
```

---

### 2. Python Projects

#### Option A: Direct Git Dependency (Recommended for Production & CI)

Install via `pip`:

```bash
pip install "network-world-model-api @ git+https://github.com/Phlosy/network-world-model-api.git@v0.1.0#subdirectory=python"
```

Or declare in your `pyproject.toml` (e.g. inside `network-world-model`):

```toml
dependencies = [
    "network-world-model-api @ git+https://github.com/Phlosy/network-world-model-api.git@v0.1.0#subdirectory=python",
    "pydantic>=2.6",
]
```

#### Option B: Editable Install for Local Development

When developing `network-world-model` alongside `network-world-model-api` on the same machine:

```bash
# Inside the network-world-model virtual environment
pip install -e /path/to/network-world-model-api/python
```

Changes regenerated in the API repo immediately reflect in the model framework without reinstalling!

Usage in Python:

```python
from network_world_model_api import NetworkWorldState, Node, NodeType

state = NetworkWorldState.model_validate(raw_dict)
print(f"Loaded snapshot {state.snapshot_id} with {len(state.nodes)} nodes")
```

---

## 🛠️ Development & Code Generation

### Prerequisites

- Node.js >= 18 (for Redocly linting)
- Go >= 1.24
- Python >= 3.10

Install the pinned code generators with:

```bash
make install-codegen-tools
make test-tooling-pins   # fails if the generators in use drifted from the pins
```

Version pins live in the [`Makefile`](Makefile) so CI and local runs cannot drift
apart. They matter because `make verify` only proves anything when the generator
that produced the committed output is the generator being run. The formatters are
pinned alongside the generator, since the generated file's layout comes from them.

### Make Commands

```bash
# Check OpenAPI contract validity
make lint

# Generate both Go and Python sources
make generate

# Run tests across all languages
make test

# Verify generated code matches the contract (CI anti-drift gate)
make verify
```

---

## 🚀 Release Workflow

1. Update version:
   ```bash
   scripts/release.sh set-version 0.1.0
   git commit -am "chore(release): prepare release 0.1.0"
   ```

2. Create annotated tags:
   ```bash
   scripts/release.sh tag 0.1.0
   # Automatically creates 'v0.1.0' (Repository/Python) and 'go/v0.1.0' (Go module)
   ```

3. Push to GitHub:
   ```bash
   git push origin main --tags
   ```

4. The GitHub Actions release workflow will automatically build the Python Wheel and create a GitHub Release with assets.
