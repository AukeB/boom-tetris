# Default project folder
PROJECT_NAME = src/boom_tetris

# Format and lint code with Ruff
ruff:
	uv run ruff check $(PROJECT_NAME) --fix
	uv run ruff format $(PROJECT_NAME)
	@echo "🔧 Successfully executed ruff."

# Type-check code with Mypy
# --disallow-untyped-calls: Error when calling functions without type hints
# --disallow-untyped-defs: Error on functions without type hints
# --ignore-missing-imports: Suppresses errors about external packages lacking type hints
# --follow-imports=skip: Skips checking imported modules to speed up analysis
mypy:
	uv run mypy $(PROJECT_NAME) \
		--disallow-untyped-calls \
		--disallow-untyped-defs \
		--ignore-missing-imports \
		--follow-imports=skip
	@echo "🔍 Successfully executed mypy."

# Remove caches and temporary files
clean:
	@find . -type d \( \
		-name '__pycache__' -o \
		-name '.ruff_cache' -o \
		-name '.mypy_cache' -o \
		-name '.pytest_cache' \
	\) -exec rm -rf {} +
	@rm -f .coverage .python-version
	@rm -rf artifacts
	@echo "🧹 Successfully cleaned project."


# Commit and push everything to git
git:
	git add -A
	git commit -m "Updated"
	git push
	@echo "📤 Successfully executed git."

# Run full workflow: format, type-check, test, clean, commit
all:
	make ruff
	make mypy
	make clean
	make git
	@echo "⚡ Successfully executed all tasks."