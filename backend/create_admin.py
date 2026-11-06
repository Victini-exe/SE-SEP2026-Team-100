from getpass import getpass

from app.api.v1.endpoints.auth import get_password_hash
from app.config import get_settings
from app.db.session import SessionLocal
from app.models import User


def main() -> None:
    settings = get_settings()
    name = input("Administrator name: ").strip()
    if not 2 <= len(name) <= 150:
        raise SystemExit("Name must contain 2-150 characters.")
    email = input("Administrator institute email: ").strip().lower()
    if "@" not in email or email.rpartition("@")[2] not in settings.allowed_domains:
        raise SystemExit("Use an email address from an allowed institute domain.")
    password = getpass("Password (8-128 characters): ")
    if not 8 <= len(password) <= 128:
        raise SystemExit("Password must contain 8-128 characters.")

    with SessionLocal() as db:
        if db.query(User).filter(User.institute_email == email).first():
            raise SystemExit("A user with that email already exists.")
        db.add(User(
            name=name,
            institute_email=email,
            password_hash=get_password_hash(password),
            role="admin",
            account_status="active",
        ))
        db.commit()
    print("Administrator account created.")


if __name__ == "__main__":
    main()
