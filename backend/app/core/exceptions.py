from fastapi.responses import JSONResponse
from fastapi.requests import Request


class AppError(Exception):
    """Base application error with HTTP status and user-facing message."""

    def __init__(
        self,
        message: str | int = "An error occurred",
        *args,
        status_code: int = 500,
        error_code: str | None = None,
        error: str | None = None,
        **kwargs,
    ):
        if isinstance(message, int):
            self.status_code = message
            self.error = str(args[0]) if args else (error or error_code or "ERROR")
            self.message = str(args[1]) if len(args) > 1 else (kwargs.get("message") or "An error occurred")
        else:
            self.message = str(message)
            self.status_code = status_code
            self.error = error_code or error or "INTERNAL_ERROR"
        self.error_code = self.error
        super().__init__(self.message)


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(400, "VALIDATION_ERROR", message)


class NotFoundError(AppError):
    def __init__(self, message: str):
        super().__init__(404, "NOT_FOUND", message)


class ProcessingError(AppError):
    def __init__(self, message: str):
        super().__init__(422, "PROCESSING_ERROR", message)


class ServiceError(AppError):
    def __init__(self, message: str):
        super().__init__(503, "SERVICE_ERROR", message)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error, "message": exc.message},
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
    )
