# Instructions for this project

## Endpoint testing and validation

- Write automated tests for every API endpoint you create. When changing an existing endpoint, add or update its tests.
- Cover successful requests, input validation, and relevant error cases. Verify response status codes, response data, and database changes where applicable.
- Always run the endpoint tests and validate that the endpoints work correctly before marking the work complete. Fix failures and rerun the affected tests.
- Use a temporary SQLite database for tests so they do not change the user's saved tasks or notes.
- If validation cannot be completed, clearly report what was not verified and why. Do not claim an endpoint works without verification.

Run the project's current automated tests from this directory:

```powershell
.\.venv\Scripts\python.exe -m unittest test_app -v
```
