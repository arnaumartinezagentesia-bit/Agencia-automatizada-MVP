from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    """Base for every contract model: unknown fields are rejected (DATA_CONTRACTS §15, §18)."""

    model_config = ConfigDict(extra="forbid")
