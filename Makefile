# Toolchain pins. `make verify` only means something when the generators in use
# are the pinned ones, so CI installs exactly these through
# `make install-codegen-tools` and `make test-tooling-pins` fails when the
# binaries drift from them. The datamodel-code-generator extras declare the
# formatters passed to --formatters below, which that project is turning into an
# opt-in dependency.
OAPI_CODEGEN_MODULE ?= github.com/oapi-codegen/oapi-codegen/v2/cmd/oapi-codegen
OAPI_CODEGEN_VERSION ?= v2.7.2
DATAMODEL_CODEGEN_PACKAGE ?= datamodel-code-generator[black,isort]==0.82.0
DATAMODEL_CODEGEN_VERSION ?= 0.82.0
# The formatters are pinned as well: the generated file's layout comes from them,
# so pinning only the generator would let a formatter release change line
# wrapping and make `make verify` report a contract mismatch that does not exist.
# `--formatters builtin` would remove the external dependency but reformats the
# whole file, so it is not an option here.
DATAMODEL_CODEGEN_FORMATTERS ?= black==26.5.1 isort==8.0.1

OAPI_CODEGEN ?= $(shell which oapi-codegen 2>/dev/null || echo "$(HOME)/go/bin/oapi-codegen")
DATAMODEL_CODEGEN ?= $(shell which datamodel-codegen 2>/dev/null || echo "pipx run '$(DATAMODEL_CODEGEN_PACKAGE)'")
NPM ?= npm
PYTHON ?= $(shell [ -f /home/xpk/workspace/network-world-model/.venv/bin/python3 ] && echo "/home/xpk/workspace/network-world-model/.venv/bin/python3" || echo "python3")
PYTEST ?= $(shell [ -f /home/xpk/workspace/network-world-model/.venv/bin/pytest ] && echo "/home/xpk/workspace/network-world-model/.venv/bin/pytest" || echo "pytest")

OPENAPI_SPEC := contracts/openapi/network-world-state.openapi.json

.PHONY: all
all: generate test

.PHONY: hooks-install
hooks-install:
	./scripts/install-git-hooks.sh

.PHONY: lint
lint:
	$(NPM) exec --yes --package @redocly/cli@1.25.15 -- redocly lint $(OPENAPI_SPEC)

.PHONY: install-codegen-tools
install-codegen-tools:
	go install $(OAPI_CODEGEN_MODULE)@$(OAPI_CODEGEN_VERSION)
	$(PYTHON) -m pip install --upgrade '$(DATAMODEL_CODEGEN_PACKAGE)' $(DATAMODEL_CODEGEN_FORMATTERS)

.PHONY: test-tooling-pins
test-tooling-pins:
	@$(OAPI_CODEGEN) --version | grep -qF "$(OAPI_CODEGEN_VERSION)" || { \
		echo "oapi-codegen is not $(OAPI_CODEGEN_VERSION); run 'make install-codegen-tools'"; exit 1; }
	@$(DATAMODEL_CODEGEN) --version | grep -qF "$(DATAMODEL_CODEGEN_VERSION)" || { \
		echo "datamodel-code-generator is not $(DATAMODEL_CODEGEN_VERSION); run 'make install-codegen-tools'"; exit 1; }
	@echo "toolchain pins ok: oapi-codegen $(OAPI_CODEGEN_VERSION), datamodel-code-generator $(DATAMODEL_CODEGEN_VERSION)"

.PHONY: clean-go
clean-go:
	rm -f go/worldstate/types.gen.go

.PHONY: generate-go
generate-go: clean-go
	cd go && $(OAPI_CODEGEN) --config oapi-codegen.yaml ../$(OPENAPI_SPEC)

.PHONY: clean-python
clean-python:
	rm -f python/network_world_model_api/models.py

.PHONY: generate-python
generate-python: clean-python
	$(DATAMODEL_CODEGEN) --input $(OPENAPI_SPEC) --output python/network_world_model_api/models.py --output-model-type pydantic_v2.BaseModel --disable-timestamp --formatters black isort

.PHONY: generate
generate: generate-go generate-python

.PHONY: test-go
test-go:
	cd go && go test -v ./...
	cd go && go vet ./...

.PHONY: test-python
test-python:
	PYTHONPATH=python $(PYTEST) python/tests

.PHONY: test
test: test-tooling-pins test-go test-python

.PHONY: verify
verify: generate
	@git diff --exit-code -- contracts go python || { \
		echo; \
		echo "生成物与契约真源不一致：contracts、go 或 python 下的生成结果存在差异或已被手工修改。"; \
		echo "正确流程：修改 contracts 下规范 -> make generate -> 与契约一同提交。"; \
		exit 1; \
	}

.PHONY: test-release
test-release:
	sh -n scripts/release.sh
	./scripts/release.sh set-version "$$(sed -n '1p' VERSION)"

.PHONY: clean
clean:
	rm -rf .pytest_cache python/.pytest_cache python/*.egg-info python/build python/dist
