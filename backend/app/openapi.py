import json

from backend.app.main import app


if __name__ == "__main__":
    print(json.dumps(app.openapi(), indent=2, sort_keys=True))
