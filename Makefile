.PHONY: run-migration generate-migration

run-migration:
	python migrate.py run

generate-migration:
	@if [ -z "$(DESC)" ]; then \
		echo "Usage: make generate-migration DESC=\"description\" [QUERY=\"query\"]"; \
		exit 1; \
	fi
	python migrate.py generate "$(DESC)" "$(QUERY)"
