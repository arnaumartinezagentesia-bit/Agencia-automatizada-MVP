from app.domain.base import ContractModel
from app.domain.enums import ErrorCode
from app.domain.types import JsonObject, NonEmptyStr


class ErrorDetail(ContractModel):
    code: ErrorCode
    message: NonEmptyStr
    details: JsonObject | None = None
