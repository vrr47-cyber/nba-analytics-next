from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str
    details: dict[str, Any] | None = None


class ApplicationError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


async def application_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ApplicationError):
        return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": "Internal server error."}})
    body = ErrorBody(
        code=exc.code,
        message=exc.message,
        request_id=str(request.scope.get("nba_request_id", "unknown")),
        details=exc.details,
    )
    return JSONResponse(status_code=400, content={"error": body.model_dump()})
