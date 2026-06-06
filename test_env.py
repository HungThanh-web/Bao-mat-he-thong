from dotenv import load_dotenv
import os

print("Testing load_dotenv...")
result = load_dotenv('.env', override=True)
print(f'load_dotenv result: {result}')
print(f'DB_HOST: {os.environ.get("DB_HOST")}')
print(f'DB_PORT: {os.environ.get("DB_PORT")}')
print(f'DB_USER: {os.environ.get("DB_USER")}')
