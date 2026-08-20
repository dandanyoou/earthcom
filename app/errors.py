from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.envelope import ErrorBody, ErrorEnvelope


class ProductError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int,
        details: dict[str, object] | list[object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def error_content(
    code: str,
    message: str,
    details: dict[str, object] | list[object] | None = None,
) -> dict[str, Any]:
    envelope = ErrorEnvelope(error=ErrorBody(code=code, message=message, details=details))
    return envelope.model_dump(mode="json")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProductError)
    async def handle_product_error(_request: Request, exc: ProductError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_content(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {"location": list(error["loc"]), "message": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_content("VALIDATION_ERROR", "The request is invalid.", details),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=error_content("INTERNAL_ERROR", "An unexpected error occurred."),
        )
