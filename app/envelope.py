from pydantic import BaseModel


class SuccessEnvelope[T](BaseModel):
    ok: bool = True
    data: T
    meta: dict[str, object] | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, object] | list[object] | None = None


class ErrorEnvelope(BaseModel):
    ok: bool = False
    error: ErrorBody


def ok[T](data: T, meta: dict[str, object] | None = None) -> SuccessEnvelope[T]:
    return SuccessEnvelope(data=data, meta=meta)
