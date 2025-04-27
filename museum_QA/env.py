
import os

from dotenv import load_dotenv, dotenv_values

load_dotenv(".env", override=False)  # take environment variables from .env.
print(f"setting environment variables: {dotenv_values('.env')}")


def get_app_root():
    return os.getcwd()


def get_env_value(key):
    return os.environ.get(key)


if __name__ == '__main__':
    print(get_app_root())
    print(get_env_value('LLM_API_KEY'))
    print(get_env_value('MODEL_NAME'))
    # print(os.environ.get('PY_DEBUG'))
