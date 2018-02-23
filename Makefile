all: help

-include config.mk

define HELP_TEXT

  Makefile commands

	make deps         - (Not done yet) Install dependent programs and libraries
	make clean        - (Not done yet) Delete all build artifacts

	make build        - (Not done yet) Build the code

	make lint         - Run the Go linters
	make lint-ci      - Run the Go tests with circleci locally (Linux based)

  Administrative commands

	changelog         - Update the CHANGELOG.md

endef

help:
	$(info $(HELP_TEXT))

lint:
	flake8

lint-ci:
	circleci build

changelog:
	docker run -it --rm -v "$(shell pwd)":/usr/local/src/your-app \
	clburlison/github-changelog-generator \
	-u clburlison -p vendored \
	-t ${CHANGELOG_GITHUB_TOKEN}
