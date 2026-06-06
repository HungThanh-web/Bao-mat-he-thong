from backend.crypto.strength import password_strength

# Test weak password (no special chars)
r = password_strength('Test1234')
print(f"Password: Test1234")
print(f"Label: {r[0]}")
print(f"meets_policy: {r[2].get('meets_policy')}")
print(f"Details: {r[2]}")
