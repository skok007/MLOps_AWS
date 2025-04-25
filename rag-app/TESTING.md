# Testing in the RAG Application

## Overview

This document explains the testing setup for the RAG application and how to run the tests.

## Test Files

The application has the following test files:

- `tests/services/test_generation_service.py`: Tests for the generation service
- `tests/services/test_retrieval_service.py`: Tests for the retrieval service

## Running Tests

You can run the tests using the following methods:

1. Using the Makefile:
   ```bash
   make test
   ```

2. Using the run_tests.sh script:
   ```bash
   ./run_tests.sh
   ```

3. Using pytest directly:
   ```bash
   poetry run pytest tests/services/test_generation_service.py tests/services/test_retrieval_service.py -v
   ```

## Test Configuration

The test configuration is defined in:

1. `pyproject.toml`: Contains the pytest configuration
2. `pytest.ini`: Contains additional pytest configuration
3. `tests/conftest.py`: Contains fixtures and setup for the tests

## Excluded Tests

The following test files are excluded from the test suite as they reference modules that don't exist in the codebase:

- `tests/services/test_embedding_service.py`
- `tests/services/test_llm_service.py`
- `tests/services/test_rag_service.py`

These files were incorrectly generated in a previous chat and are not needed for the current codebase. 