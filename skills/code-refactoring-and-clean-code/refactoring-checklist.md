# Clean Code & Refactoring Checklist

- [ ] All functions have descriptive, verb-based names (`calculate_total`, `fetch_user_by_id`).
- [ ] Guard clauses used to eliminate deep indentation:
  ```python
  if not user:
      return None
  if not user.is_active:
      return None
  # happy path starts here
  ```
- [ ] Exceptions handled specifically (`except FileNotFoundError:`, not bare `except:`).
- [ ] Type annotations added for all parameters and return types.
- [ ] 100% test pass rate maintained after refactoring.
