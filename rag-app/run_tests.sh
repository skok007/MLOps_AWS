#!/bin/bash

# Add the project root to the Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run the tests
poetry run pytest tests/ -v --junitxml=test-results.xml 