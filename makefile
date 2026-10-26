NAME = Fly-in
VENV = .venv
EXCLUDES = $(VENV)

install:
	@uv sync

run: install
	@uv run python -m src $(ARGS)

debug: install
	@uv run python -m pdb -m src $(ARGS)

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -exec rm -f {} +
	@find . -type d -name "*.egg-info" -exec rm -rf {} +

lint: install
	@uv run flake8 . --exclude $(EXCLUDES)
	@uv run mypy . \
		--exclude "$(VENV)"\
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict: install
	@uv run flake8 . --exclude $(EXCLUDES)
	@uv run mypy . --strict --exclude "$(VENV)"

.PHONY: install run debug clean lint lint-strict
