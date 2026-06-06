from backend.crypto import strength
import inspect

print(f"strength module file: {strength.__file__}")
print(f"password_strength function source file: {inspect.getsourcefile(strength.password_strength)}")

# Read the source
source = inspect.getsource(strength.password_strength)
print("\nFunction source (first 500 chars):")
print(source[:500])
