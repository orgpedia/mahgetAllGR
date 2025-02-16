.DEFAULT_GOAL := help

org_code := mahgetGR

tasks :=  # IMP: Write al the tasks here
tasks := $(foreach t,$(tasks),flow/$t)

DOCS = import/documents/
SRC = import/src
LOGS = import/logs
WEBSITE = import/websites/gr.maharashtra.gov.in


.PHONY: help install import flow export check readme lint format pre-commit $(tasks)

help:
	$(info Please use 'make <target>', where <target> is one of)
	$(info )
	$(info   install           install packages and prepare software environment)
	$(info )
	$(info   fetch_site        fetch the html pages for a date range.)
	$(info   merge_fetch       merge the new fetch(es) with earlier fetches.)
	$(info   link_wayback      link the wayback service to the the new urls.)
	$(info   upload_to_archive upload the downloaded pdfs to archive.org)

	$(info )
	$(info   lint              run the code linters)
	$(info   format            reformat code)
	$(info )
	$(info Check the makefile to know exactly what each target is doing.)
	@echo # dummy command



install: pyproject.toml
	uv venv
	uv sync

upload_all_to_archive:
	uv run python -u import/src/upload_all_to_archive.py import/documents/merged_fetch.json.gz import/documents/wayback.json.gz import/documents/archive.json import/documents | tee import/logs/upload_to_archive.log


lint:
	uv run ruff import/src flow/src

format:
	uv run ruff --fix . import/src flow/src
	uv run ruff format . import/src flow/src


# Use pre-commit if there are lots of edits,
# https://pre-commit.com/ for instructions
# Also set git hook `pre-commit install`
pre-commit:
	pre-commit run --all-files

