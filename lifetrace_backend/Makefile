
# Default target executed when no arguments are given to make.
all: help

lint:
	ruff check
	ruff format --check

format:
	ruff check --fix
	ruff format

######################
# HELP
######################
help:
	@echo '----'
	@echo 'format                       - run code formatters'
	@echo 'lint                         - run linters'
