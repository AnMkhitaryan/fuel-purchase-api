from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


def _format_validation_error(exc: RequestValidationError) -> str:
    first = exc.errors()[0]
    field = ".".join(part for part in first["loc"]
                     if isinstance(part, str) and part not in ("body", "query", "path"))
    message = first["msg"].removeprefix("Value error, ")
    return f"{field}: {message}" if field else message


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return _error_response(exc.status_code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        return _error_response(422, _format_validation_error(exc))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        return _error_response(exc.status_code, str(exc.detail))
