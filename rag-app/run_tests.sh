#!/bin/bash

# Run tests with exclusions for non-existent test files
poetry run pytest tests/services/test_generation_service.py tests/services/test_retrieval_service.py -v 