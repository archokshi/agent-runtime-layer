from datetime import datetime, timezone

from fastapi import APIRouter

from app.db import get_conn
from app.schemas import MeasuredValidationExperiment, MeasuredValidationExperimentCreate
from app.storage.repositories import list_measured_validation_experiments, save_measured_validation_experiment

router = APIRouter()


def _projection_error(projected: float | None, measured: float | None) -> float | None:
    if projected is None or measured is None:
        return None
    return round(abs(projected - measured), 2)


@router.post("/validation/experiments", response_model=MeasuredValidationExperiment)
def create_validation_experiment(payload: MeasuredValidationExperimentCreate) -> MeasuredValidationExperiment:
    experiment = MeasuredValidationExperiment(
        **payload.model_dump(),
        projection_error_percent=_projection_error(
            payload.projected_input_token_reduction_percent,
            payload.measured_input_token_reduction_percent,
        ),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    with get_conn() as conn:
        return save_measured_validation_experiment(conn, experiment)


@router.get("/validation/experiments", response_model=list[MeasuredValidationExperiment])
def list_validation_experiments() -> list[MeasuredValidationExperiment]:
    with get_conn() as conn:
        return list_measured_validation_experiments(conn)
