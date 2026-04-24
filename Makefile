PYTHON := python3
VENV := .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
RUFF := $(VENV)/bin/ruff
CLI := $(VENV)/bin/earnings-call-sentiment

SMOKE_URL ?= https://www.youtube.com/watch?v=BaW_jenozKc
SMOKE_OUT := ./_smoke_out
SMOKE_CACHE := ./_smoke_cache

.PHONY: setup lint smoke clean pvh-proof docs-audit refresh-proof proof-freshness link-check portfolio-hygiene portfolio-ci

$(VENV_PY):
	$(PYTHON) -m venv $(VENV)

setup: $(VENV_PY)
	$(VENV_PIP) install -U pip
	$(VENV_PIP) install -r requirements.txt
	$(VENV_PIP) install -e .

lint: setup
	$(VENV_PIP) install ruff
	$(RUFF) check src
	$(VENV_PY) -m py_compile $$(find src -type f -name "*.py")

smoke: setup
	mkdir -p $(SMOKE_OUT) $(SMOKE_CACHE)
	$(CLI) \
		--youtube-url '$(SMOKE_URL)' \
		--cache-dir $(SMOKE_CACHE) \
		--out-dir $(SMOKE_OUT)
	@echo
	@echo "Smoke artifacts:"
	@ls -la $(SMOKE_OUT) $(SMOKE_CACHE)

pvh-proof:
	$(PYTHON) scripts/build_portfolio_proof.py

docs-audit:
	$(PYTHON) scripts/audit_portfolio_docs.py

refresh-proof:
	$(PYTHON) scripts/refresh_readme_proof.py

proof-freshness:
	$(PYTHON) scripts/check_proof_freshness.py

link-check:
	$(PYTHON) scripts/check_markdown_links.py

portfolio-hygiene: pvh-proof refresh-proof proof-freshness docs-audit link-check

portfolio-ci:
	@set -e; \
	echo "== build canonical proof =="; \
	$(PYTHON) scripts/build_portfolio_proof.py; \
	echo "== refresh README proof block =="; \
	$(PYTHON) scripts/refresh_readme_proof.py; \
	echo "== check proof freshness =="; \
	$(PYTHON) scripts/check_proof_freshness.py; \
	echo "== audit canonical portfolio docs =="; \
	$(PYTHON) scripts/audit_portfolio_docs.py; \
	echo "== verify canonical outputs =="; \
	$(PYTHON) scripts/verify_outputs.py --out-dir outputs/PVH_2025_Q1_call09 --require-run-meta; \
	echo "== check markdown links =="; \
	$(PYTHON) scripts/check_markdown_links.py; \
	echo "== compile portfolio scripts =="; \
	$(PYTHON) -m py_compile app/site_server.py scripts/build_portfolio_proof.py scripts/audit_portfolio_docs.py scripts/refresh_readme_proof.py scripts/check_markdown_links.py scripts/check_proof_freshness.py; \
	echo "PORTFOLIO CI PASS: canonical proof, README refresh, doc audit, output verification, link integrity, and syntax checks completed."

clean:
	rm -rf ./_smoke_out ./_smoke_cache build dist
