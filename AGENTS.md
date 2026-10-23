# Coding standards

These standards apply to every change in this repository. Follow any more specific instructions in a subdirectory when they exist.

## Make focused changes

- Keep changes scoped to the requested behavior. Avoid unrelated cleanup, new dependencies, and speculative abstractions.
- Prefer the simplest design that fits the existing project. Follow the conventions already established in nearby code.
- Preserve existing public behavior unless the request calls for a change. Call out compatibility impact when relevant.

## Write clear code

- Use descriptive names and small functions with one clear responsibility.
- Do not use the ternary operator. Use a clear `if`/`else` branch instead, even for short conditions.
- Make control flow and important assumptions explicit. Avoid clever tricks, unnecessary indirection, and duplicated logic.
- Handle invalid input and failure paths deliberately; do not silently swallow errors.
- Add enough comments to explain non-obvious logic, important assumptions, and reasons behind decisions. Keep comments accurate and useful; do not add comments that merely restate the code.
- Update comments and documentation when behavior changes.
- Use the language's standard formatter and idioms. Do not introduce a formatter or style that conflicts with the project.

## Verify changes

- For behavior changes, run the most relevant existing checks, such as focused tests, type checks, or linting, when available.
- Add or update tests when a change introduces or fixes behavior, especially for edge cases and regressions.
- Do not claim a check passed unless it was actually run. If a check cannot be run, state why.

## Safety and dependencies

- Validate data at trust boundaries and avoid exposing secrets, personal data, or sensitive values in logs.
- Use parameterized APIs for queries and safe APIs for paths, processes, and rendered content.
- Add a dependency only when it is needed; prefer maintained, established packages and explain notable additions.

## Review and communication

- Before finishing, inspect the diff for accidental changes, generated files, and unrelated edits.
- Summarize what changed and why, and report relevant verification and any remaining limitation.
