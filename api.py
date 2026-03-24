from fastapi import FastAPI

import model_v2

app = FastAPI()


@app.post("/emissions/dairy/lactating")
def calculate_emissions_dairy_lactating(
    dairy_lactating_params: model_v2.DairyLactatingParams
) -> model_v2.EmissionResults:
    return model_v2.calc_dairy_lactating(dairy_lactating_params)


@app.post("/emissions/beef/breeding")
def calculate_emissions_beef_breeding(beef_breeding_params: model_v2.BeefBreedingCowParams) -> model_v2.EmissionResults:
    return model_v2.calc_beef_breeding_cow(beef_breeding_params)
