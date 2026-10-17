from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.users import DuplicateUserError, authenticate_user, create_user


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
	"/register",
	response_model=UserResponse,
	status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest) -> UserResponse:
	try:
		user = create_user(
			username=payload.name,
			password=payload.password,
			email=str(payload.email),
		)
	except DuplicateUserError as exc:
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail=str(exc),
		) from exc
	except ValueError as exc:
		raise HTTPException(
			status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
			detail=str(exc),
		) from exc

	return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
	user = authenticate_user(email=str(payload.email), password=payload.password)
	if user is None:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="E-mail ou senha incorretos.",
			headers={"WWW-Authenticate": "Bearer"},
		)

	return TokenResponse(
		access_token=create_access_token(str(user.id)),
		expires_in=settings.access_token_expire_minutes * 60,
	)
