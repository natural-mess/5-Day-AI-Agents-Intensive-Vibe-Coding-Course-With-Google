# Code Review Report: [demo_bad_code.py](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Getting%20Started%20with%20Google%20Antigravity/my-skills-project/demo_bad_code.py)

Here is a review of the code in [demo_bad_code.py](file:///d:/EmbeddedSystem/OnlineCourses/5-Day%20AI%20Agents%20Intensive%20Vibe%20Coding%20Course%20With%20Google/Day1/Codelabs/Getting%20Started%20with%20Google%20Antigravity/my-skills-project/demo_bad_code.py) based on correctness, edge cases, style, and performance.

---

## 1. Correctness

### Potential Crash on Missing User
In `run_batch()`, the function queries a user with ID `3`:
```python
u = get_user_data(users, 3)
print("User found: " + u['name']) # Will crash if None
```
Because the `users` list only contains IDs `1` and `2`, `get_user_data` returns `None`. Accessing `u['name']` will immediately raise:
> `TypeError: 'NoneType' object is not subscriptable`

#### Recommendation
Check if the user exists before accessing attributes:
```python
u = get_user_data(users, 3)
if u:
    print(f"User found: {u['name']}")
else:
    print("User not found")
```

---

## 2. Edge Cases

### Missing Keys in Dictionaries
If any dictionary inside `items` does not contain the key `'price'`, or if `users` dictionaries lack `'id'`, the code will raise a `KeyError`.

#### Recommendation
Use `.get()` with defaults:
```python
tax = i.get('price', 0) * 0.1
```

---

## 3. Style and Conventions

### Shadowing Built-in Name `id`
In `get_user_data(users, id)`, the parameter name `id` shadows Python's built-in `id()` function.
* **Recommendation**: Rename the parameter to `user_id`.

### Indentation and Formatting
* Line 7 (`return u`) is indented with 13 spaces, violating consistent spacing rules.
* Line 17 contains trailing spaces.
* **Recommendation**: Format the file using a formatter like `black` or follow standard 4-space indentation.

---

## 4. Performance

### Sequential Blocking Delays
In `process_payments()`, there is a `time.sleep(0.1)` inside the loop:
```python
for i in items:
    # ...
    time.sleep(0.1) # Simulate slow network call
```
If the number of items grows large, this sequential sleep will block execution synchronously for a long time.
* **Recommendation**: If simulating network calls, consider using asynchronous processing (`asyncio`) or batching requests instead of sleeping per item.
