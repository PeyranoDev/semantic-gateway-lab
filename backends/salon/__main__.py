"""Run a disposable corrected API: python -m backends.salon --db salon.db --fixture."""
import argparse
import os
from pathlib import Path
import uvicorn
from .app import create_app

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    key = os.environ.get("SALON_SIGNING_KEY")
    if not key:
        parser.error("set SALON_SIGNING_KEY (at least 32 characters)")
    if args.fixture and Path(args.db).exists():
        parser.error("--fixture requires a new disposable database path")
    app = create_app(args.db, key)
    if args.fixture:
        app.state.database.provision_fixture()
    uvicorn.run(app, host="127.0.0.1", port=args.port)

if __name__ == "__main__":
    main()
