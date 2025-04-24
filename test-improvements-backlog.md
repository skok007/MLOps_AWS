# Test Improvements Backlog

## High Priority

### Fix Artifact Sharing in CI Pipeline
- [x] Rename artifact from "workspace" to "poetry-workspace" for clarity
- [x] Add debug steps to verify artifact upload and download
- [ ] Consider using GitHub's cache action instead of artifacts for better performance
- [ ] Add error handling for artifact download failures

### Expand Retrieval Service Tests
- [ ] Add tests for different top_k values
- [ ] Add tests for different query types
- [ ] Mock the embedding model to avoid actual API calls
- [ ] Add tests for database connection errors
- [ ] Test edge cases like empty results

### Add Query Expansion Service Tests
- [ ] Create a new test file for this service
- [ ] Test the main functionality
- [ ] Test edge cases and error handling

## Medium Priority

### Improve Error Handling Tests
- [ ] Add tests for LLM API errors
- [ ] Add tests for database connection failures
- [ ] Add tests for invalid input parameters
- [ ] Add tests for timeout scenarios

### Add Integration Tests
- [ ] Test the flow from retrieval to generation
- [ ] Test the complete RAG pipeline
- [ ] Test with real-world queries

### Refactor Test Structure
- [ ] Consider using test classes for better organization
- [ ] Add parameterized tests for testing multiple scenarios
- [ ] Improve the database fixture to handle errors better
- [ ] Add more detailed docstrings explaining test scenarios

## Low Priority

### Add Performance Tests
- [ ] Test response times for different query lengths
- [ ] Test memory usage with large document sets
- [ ] Benchmark different embedding models

### Add Tests for Configuration
- [ ] Test different model configurations
- [ ] Test environment variable handling
- [ ] Test configuration validation

### Improve Test Documentation
- [ ] Add more detailed docstrings explaining test scenarios
- [ ] Document expected behavior for edge cases
- [ ] Add examples of how to run specific tests

## Notes

- The current test suite has good coverage of the generation service but limited coverage of other services
- The database setup in conftest.py is complex and could be simplified
- Consider using a test database container for more reliable testing
- Add more assertions to verify the quality of generated responses 