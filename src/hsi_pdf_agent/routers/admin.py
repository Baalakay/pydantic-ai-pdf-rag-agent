from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
import jwt
import logfire

from hsi_pdf_agent.core.security import verify_password, create_access_token
from hsi_pdf_agent.core.config import settings
from hsi_pdf_agent.core.prompt_manager import PromptManager
from hsi_pdf_agent.models.prompt_config import PromptConfig, PromptConfigurations


router = APIRouter(prefix="/admin", tags=["admin"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="admin/token")


async def get_current_admin(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    """Validate the JWT token and return the admin username."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username != settings.ADMIN_USERNAME:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return username
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> dict:
    """Login endpoint for admin users."""
    # Log the exact values being used
    logfire.info(
        "login_attempt",
        submitted_username=form_data.username,
        expected_username=settings.ADMIN_USERNAME,
        username_match=form_data.username == settings.ADMIN_USERNAME
    )
    
    # First check username
    if form_data.username != settings.ADMIN_USERNAME:
        logfire.warning(
            "login_failed",
            reason="invalid_username",
            submitted_username=form_data.username
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Then verify password
    if not verify_password(form_data.password, settings.ADMIN_PASSWORD_HASH):
        logfire.warning(
            "login_failed",
            reason="invalid_password",
            username=form_data.username
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Success - create token
    logfire.info(
        "login_successful",
        username=form_data.username
    )
    return {
        "access_token": create_access_token(form_data.username),
        "token_type": "bearer"
    }


@router.get("/prompts", response_model=PromptConfigurations)
async def get_prompts(admin: Annotated[str, Depends(get_current_admin)]) -> PromptConfigurations:
    """Get all prompt configurations."""
    return PromptManager.load_prompts()


@router.put("/prompts/{prompt_name}")
async def update_prompt(
    prompt_name: str,
    prompt_config: PromptConfig,
    admin: Annotated[str, Depends(get_current_admin)]
) -> PromptConfigurations:
    """Update a specific prompt configuration."""
    try:
        return PromptManager.update_prompt(prompt_name, prompt_config, admin)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 