import argparse
import sys

from sqlalchemy import select

from app import models
from app.database import Base, SessionLocal, engine
from app.security import generate_api_key, hash_api_key


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an administrator.")
    parser.add_argument("username", help="Unique administrator username (max 50 chars)")
    username = parser.parse_args().username.strip()

    if not username or len(username) > 50:
        print("Username must be between 1 and 50 characters.", file=sys.stderr)
        return 1

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if db.scalar(select(models.Admin).where(models.Admin.username == username)):
            print(f"Admin '{username}' already exists.", file=sys.stderr)
            return 1
        api_key = generate_api_key()
        db.add(models.Admin(username=username, api_key_hash=hash_api_key(api_key)))
        db.commit()

    print(f"Admin '{username}' created.")
    print(f"API key (shown only once, save it now): {api_key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
