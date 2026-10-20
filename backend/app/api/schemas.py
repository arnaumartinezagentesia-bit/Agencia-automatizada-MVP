from typing import Annotated, Literal, Self

from pydantic import Field, StrictBool, StrictInt, model_validator

from app.domain.analysis import MarketAnalysis
from app.domain.base import ContractModel
from app.domain.errors import ErrorDetail
from app.domain.run import AnalysisSummary
from app.domain.types import Uuid4


class ResponseMeta(ContractModel):
    request_id: Uuid4


class SuccessEnvelope[T: ContractModel](ContractModel):
    data: T
    meta: ResponseMeta


class ErrorEnvelope(ContractModel):
    error: ErrorDetail
    meta: ResponseMeta


class CreateAnalysisData(ContractModel):
    analysis_id: Uuid4
    status: Literal["completed"]


class GetAnalysisPendingData(ContractModel):
    analysis_id: Uuid4
    status: Literal["pending"]
    analysis: None = None
    error: None = None


class GetAnalysisRunningData(ContractModel):
    analysis_id: Uuid4
    status: Literal["running"]
    analysis: None = None
    error: None = None


class GetAnalysisCompletedData(ContractModel):
    analysis_id: Uuid4
    status: Literal["completed"]
    analysis: MarketAnalysis
    error: None = None

    @model_validator(mode="after")
    def _ids_match(self) -> Self:
        if self.analysis_id != self.analysis.analysis_id:
            raise ValueError("analysis_id must match analysis.analysis_id")
        return self


class GetAnalysisFailedData(ContractModel):
    analysis_id: Uuid4
    status: Literal["failed"]
    analysis: None = None
    error: ErrorDetail


# Validate with pydantic.TypeAdapter(GetAnalysisData).
GetAnalysisData = Annotated[
    GetAnalysisPendingData
    | GetAnalysisRunningData
    | GetAnalysisCompletedData
    | GetAnalysisFailedData,
    Field(discriminator="status"),
]


class Pagination(ContractModel):
    limit: Annotated[StrictInt, Field(ge=1)]
    offset: Annotated[StrictInt, Field(ge=0)]
    has_more: StrictBool


class ListAnalysesData(ContractModel):
    items: list[AnalysisSummary]
    pagination: Pagination
