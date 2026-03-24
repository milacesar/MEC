# Methane Emissions Calculator

Python framework to calculate the methane (CH4) estimates from livestock using equations provided by the IPCC Guidelines (2006 and 2019 refinements) and the NZ-specific equations from MPI.

IPCC consists of 3 tiers with increasing complexity and needing farm-specific metrics. MPI consists of an advanced calculation using NZ-specific equations and needing farm metrics as well.

### Supported Categories
Currently only Cattle (Dairy and Other) is supported. Eventually Sheep, Deer may be added if useful.

| Category | Description |
|---|---|
| Dairy | Lactating cows/heifers |
| Beef | Cow, bulls |
| Growing | Juveniles, steers, heifers |

### Calculation Methods

| Method | Approach | Description | Requirements | Reference |
|---|---|---|---|---|
| IPCC | Tier 1 | Using Default Emission Factor (EF)|  Animal count & days|[2006](https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_10_Ch10_Livestock.pdf) & [2019](https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/4_Volume4/19R_V4_Ch10_Livestock.pdf)|
|  | Tier 2-S | Using production metrics to calculate DMI | T1 + Animal specifications & Milk metrics (yield / fat)| |
|  | Tier 2-A | Using Net Energies (NE) component for Gross Energy (GE)| T2-S + NE | |
| MPI | FEM | Using Metabolisable Energies (ME)| | [Methodology](https://www.mpi.govt.nz/dmsdocument/13906-detailed-methodologies-for-agricultural-greenhouse-gas-emission-calculation) & [FEM](https://www.mpi.govt.nz/dmsdocument/66654-New-Zealand-Farm-Emissions-Method-A-farm-level-approach-for-estimating-biogenic-emissions) |

### Scripts 

- defaults_v2.py : contains (1) IPCC defaults, (2) MPI defaults, and (3) NZ defaults. (1) and (2) should only be modified if official changes have been made to the relevant documentations.
- model_v2.py : contains all equations and printing outputs.
- api.py : contains HTTP endpoints for a REST API access to the calculations

### Running

1. Install dependencies 
```bash
python -m venv venv

source venv/bin/activate # Linux
# or
venv\Scripts\activate # Windows

pip install -r requirements.txt
```

2. Run CLI prompt mode
```bash
python model_v2.py
```

### Run API Dev Server
Install dependencies as above then:

```bash
fastapi dev api:app
```