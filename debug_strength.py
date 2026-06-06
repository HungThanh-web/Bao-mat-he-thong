from backend.crypto.strength import password_strength

result = password_strength('Test1234')
print(f'Label: {result[0]}')
print(f'CSS: {result[1]}')
print(f'Details: {result[2]}')
print(f'Dictionary keys: {list(result[2].keys())}')
print(f'meets_policy value: {result[2].get("meets_policy", "KEY NOT FOUND")}')
