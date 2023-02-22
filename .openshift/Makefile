.ONESHELL:
SHELL = /bin/bash

.PHONY: all test

test:
	apt-get update && apt-get install -y openjdk-17-jdk-headless && apt-get clean;
	export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64/
	export PATH=$JAVA_HOME/bin:$PATH
	pip install -r requirements.txt --extra-index-url http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-all/simple --trusted-host do-prd-mvn-01.do.viaa.be
	pip install -r requirements-dev.txt
	export $(shell grep -v '^#' .env.example | xargs)
	python -m  pytest -vvv --cov=./app --junit-xml=./tests/test_results.xml