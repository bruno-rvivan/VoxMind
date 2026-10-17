from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
	credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
	session: Session = Depends(get_db),
) -> User:
	unauthorized = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Token ausente, inválido ou expirado.",
		headers={"WWW-Authenticate": "Bearer"},
	)
	if credentials is None:
		raise unauthorized

	try:
		claims = jwt.decode(
			credentials.credentials,
			settings.jwt_secret_key,
			algorithms=[settings.jwt_algorithm],
		)
		user_id = UUID(claims["sub"])
	except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
		raise unauthorized from exc

	user = session.get(User, user_id)
	if user is None:
		raise unauthorized
	return user