from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class PredictionRequest(BaseModel):
    athlete: str = Field(min_length=1)
    bodyweight_kg: float = Field(gt=0)
    recent_totals_kg: list[int] = Field(min_length=1)

class PredictionResponse(BaseModel):
    predicted_total_kg: float 
    p10_kg: float
    p90_kg: float

@app.post("/predict")
def predict(history: PredictionRequest) -> PredictionResponse:
    guess = sum(history.recent_totals_kg) / len(history.recent_totals_kg)
    return PredictionResponse(
        predicted_total_kg=guess,
        p10_kg=guess - 12,
        p90_kg=guess + 12
    )
