from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, verify_password
from app.db.session import SessionLocal
from app.models.user import User


class DuplicateUserError(ValueError):
    pass


def create_user(username: str, password: str, email: str) -> User:
    username = username.strip()
    email = email.strip().lower()

    if not username:
        raise ValueError("O nome de usuário não pode ficar vazio.")
    if len(username) > 120:
        raise ValueError("O nome de usuário deve ter no máximo 120 caracteres.")
    if not password:
        raise ValueError("A senha não pode ficar vazia.")
    if not email:
        raise ValueError("O e-mail não pode ficar vazio.")
    if len(email) > 255:
        raise ValueError("O e-mail deve ter no máximo 255 caracteres.")

    user = User(
        name=username,
        email=email,
        password_hash=hash_password(password),
    )

    try:
        with SessionLocal.begin() as session:
            session.add(user)
            session.flush()
    except IntegrityError as exc:
        raise DuplicateUserError("Já existe um usuário com este e-mail.") from exc

    return user


def authenticate_user(email: str, password: str) -> User | None:
    normalized_email = email.strip().lower()

    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == normalized_email))
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user