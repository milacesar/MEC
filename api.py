from fastapi import FastAPI

from model_v2 import calc_dairy_lactating, DairyLactatingParams, EmissionResults

app = FastAPI()





@app.post("/emissions/dairy/lactating")
def calculate_emissions_dairy_lactating(dairy_lactating_params: DairyLactatingParams) -> EmissionResults:
    return calc_dairy_lactating(dairy_lactating_params)