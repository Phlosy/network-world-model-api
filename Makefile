OAPI_CODEGEN ?= $(shell which oapi-codegen 2>/dev/null || echo "/home/xpk/go/bin/oapi-codegen")
DATAMODEL_CODEGEN ?= $(shell which datamodel-codegen 2>/dev/null || echo "pipx run datamodel-code-generator")
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
	$(DATAMODEL_CODEGEN) --input $(OPENAPI_SPEC) --output python/network_world_model_api/models.py --output-model-type pydantic_v2.BaseModel --disable-timestamp

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
test: test-go test-python

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
