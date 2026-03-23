"""
model_v2.py
========
Methane emissions estimation calculator — NZ livestock.

Implements IPCC Tier 1, Tier 2 Simplified, Tier 2 Advanced, and a
best-guess approximation of the MPI NZ Farm Emissions Method.

Species and sub-categories covered:
  Dairy cattle  — 1. Lactating cow  2. Dry cow  3. Replacement heifer
  Beef cattle   — 1. Breeding cow   2. Growing/finishing  3. Bull  4. Steer

Run:
    python model_v2.py

References:
  - IPCC 2006 Guidelines Vol.4 Ch.10
  - IPCC 2019 Refinement Vol.4 Ch.10
  - MPI Methodology 2025 / NZ Farm Emissions Method 2024
"""

from dataclasses import dataclass
import datetime
from typing import NamedTuple

from pydantic import BaseModel, Field

from defaults_v2 import ipcc_default, nz_default, DAIRY_SUBCATS, BEEF_SUBCATS


# =============================================================================
# SHARED HELPERS
# =============================================================================

def ask(prompt):
    """
    Prompt the user and return their input as a stripped string.
    Re-prompts until a non-empty answer is given.
    """
    while True:
        val = input(f'  {prompt}: ').strip()
        if val:
            return val
        print('  Please enter a value.')


def ask_float(prompt, hint=None):
    """Prompt for a float."""
    label = f'{prompt} [{hint}]' if hint is not None else prompt
    while True:
        raw = input(f'  {label}: ').strip()
        try:
            return float(raw)
        except ValueError:
            print('  Please enter a number.')


def ask_int(prompt, hint=None):
    """Prompt for an integer."""
    label = f'{prompt} [{hint}]' if hint is not None else prompt
    while True:
        raw = input(f'  {label}: ').strip()
        try:
            return int(raw)
        except ValueError:
            print('  Please enter a whole number.')


def ask_yn(prompt):
    """Prompt for yes/no. Returns True for 'y'."""
    while True:
        raw = input(f'  {prompt} (y/n): ').strip().lower()
        if raw in ('y', 'n'):
            return raw == 'y'
        print('  Please enter y or n.')


def choose_menu(title, options_dict):
    """
    Display a numbered menu and return the chosen key.

    Parameters
    ----------
    title        : str   Header printed above the options
    options_dict : dict  {key: {'label': ..., 'note': ...}, ...}
    """
    print(f'\n  {title}')
    print('  ' + '-' * 40)
    for key, val in options_dict.items():
        print(f'  {key}.  {val["label"]}')
        print(f'       {val["note"]}')
    print()
    while True:
        choice = input('  Select number: ').strip()
        if choice in options_dict:
            return choice
        print(f'  Please enter one of: {", ".join(options_dict.keys())}')


def rem_reg(DE):
    """
    Ratio of Energy for Maintenance (REM) and Growth (REG).
    IPCC 2006 Equations 10.14 and 10.15.

    Parameters
    ----------
    DE : float  Diet digestibility as a percentage (e.g. 65)

    Returns
    -------
    REM, REG : float, float
    """
    r   = DE / 100
    REM = 1.123 - (0.4092 * r) + (0.1126 * r**2) - (0.254 / r)
    REG = 1.164 - (0.516  * r) + (0.1308 * r**2) - (0.374 / r)
    return REM, REG


@dataclass
class ResultTier:
    """Container to hold data for an emission result tier."""
    EF: float
    CH4_kg: float
    GE: float | None = None
    DMI: float | None = None


class EmissionResults(BaseModel):
    """Container to hold all emission results for a calculation"""
    tier_1: ResultTier
    tier_2_simplified: ResultTier
    tier_2_advanced: ResultTier
    mpi_method: ResultTier
    NEm: float
    NEa: float
    NEl: float
    NEp: float
    ME_maint: float
    ME_lact: float
    ME_preg: float


def print_tier(name, EF, CH4_kg, GE=None, DMI=None):
    """Print one tier's results in a consistent format."""
    print(f'\n  --- {name} ---')
    if GE  is not None: print(f'  GE              : {GE:.2f} MJ/head/day')
    if DMI is not None: print(f'  DMI             : {DMI:.2f} kg DM/head/day')
    print(f'  Emission Factor : {EF:.2f} kg CH4/head/year')
    print(f'  Total Emissions : {CH4_kg:,.1f} kg CH4/year')


def print_results(results: EmissionResults):
    """Print all tiers' results for a calculation"""
    t1 = results.tier_1
    print_tier('Tier 1', t1.EF, t1.CH4_kg)
    t2s = results.tier_2_simplified
    print_tier('Tier 2 Simplified', t2s.EF, t2s.CH4_kg, GE=t2s.GE, DMI=t2s.DMI)
    t2a = results.tier_2_advanced
    print_tier('Tier 2 Advanced', t2a.EF, t2a.CH4_kg, GE=t2a.GE, DMI=t2a.DMI)
    print(f'       NEm={results.NEm:.1f}  NEa={results.NEa:.1f}  NEl={results.NEl:.1f}  NEp={results.NEp:.1f} MJ/day')
    mpi = results.mpi_method
    print_tier('MPI Method  ', mpi.EF, mpi.CH4, GE=mpi.GE, DMI=mpi.DMI)
    print(f'       ME maint={results.ME_maint:.1f}  ME lact={results.ME_lact:.1f}  ME preg={results.ME_preg:.1f} MJ/day')


def print_recap(label, N, D, BW, DE, Ym, extras=None):
    """Print the input recap block before results."""
    print(f'\n  ====== Recap — {label} ======')
    print(f'  Animals  : {N}  |  Period : {D} days  |  BW : {BW} kg')
    print(f'  DE : {DE}%  |  Ym : {Ym}%')
    if extras:
        for line in extras:
            print(f'  {line}')
    print()


# =============================================================================
# DAIRY — LACTATING COW
# =============================================================================
class DairyLactatingParams(BaseModel):
    """Input parameters for calcuating emissions of lactating dairy cows"""
    num_animals: int = Field(ge=0)
    reporting_period: int = Field(365, gt=0)
    body_weight: float = Field(nz_default['BW_Dairy_Cow'], gt=0.0)
    daily_milk_yield: float = Field(nz_default['Milk'], ge=0)
    milk_fat_percentage: float = Field(nz_default['Fat'], gt=0, le=100.0)
    milk_protein_percentage: float = Field(nz_default['Protein'], ge=0, le=100.0)
    herd_pregnant_percentage: float = Field(nz_default['preg_perc'], ge=0, le=100.0)
    diet_digestability_percentage: float = Field(nz_default['DE_NZ_Pasture'], gt=0, le=100.0)
    methane_conversion_factor_percentage: float = Field(ipcc_default['Ym'], ge=0, le=100.0)


def ask_and_calc_dairy_lactating():
    """Prompt for CLI input and calculate and print the emission results for lactating dairy cows"""
    print('\n  -- Inputs: Lactating Dairy Cow --')
    num_animals                            = ask_int  ('Number of animals')
    reporting_period                       = ask_int  ('Reporting period (days)',               hint=365)
    body_weight                            = ask_float('Body weight (kg)',                      hint=nz_default['BW_Dairy_Cow'])
    daily_milk_yield                       = ask_float('Daily milk yield (kg/head/day)',        hint=nz_default['Milk'])
    milk_fat_percentage                    = ask_float('Milk fat (%)',                          hint=nz_default['Fat'])
    milk_protein_percentage                = ask_float('Milk protein (%)',                      hint=nz_default['Protein'])
    herd_pregnant_percentage               = ask_float('Percentage of herd pregnant (%)',       hint=nz_default['preg_perc'])
    diet_digestability_percentage          = ask_float('Diet digestibility DE (%)',             hint=nz_default['DE_NZ_Pasture'])
    methane_conversion_factor_percentage   = ask_float('Methane conversion factor Ym (%)',      hint=ipcc_default['Ym'])

    params = DairyLactatingParams(num_animals, reporting_period, body_weight, daily_milk_yield, milk_fat_percentage,
                                  milk_protein_percentage, herd_pregnant_percentage, diet_digestability_percentage,
                                  methane_conversion_factor_percentage)
    results = calc_dairy_lactating(params)
    print_recap('Lactating Dairy Cow', num_animals, reporting_period, body_weight, diet_digestability_percentage, methane_conversion_factor_percentage,
                extras=[f'Milk {daily_milk_yield} kg/day  |  Fat {milk_fat_percentage}%  |  Protein {milk_protein_percentage}%',
                        f'Pregnant {herd_pregnant_percentage}%'])
    print_results(results)


def calc_dairy_lactating(params: DairyLactatingParams) -> EmissionResults:
    """
    IPCC Tier 1, Tier 2S, Tier 2 Advanced, and MPI method
    for a lactating dairy cow.

    NE components: NEm + NEa + NEl + NEp
    Cf = 0.386 (IPCC 2006 Table 10.4 — lactating)
    C  = 0.8   (female)
    """
    N = params.num_animals
    D = params.reporting_period
    BW = params.body_weight
    Milk = params.daily_milk_yield
    Fat = params.milk_fat_percentage
    Protein = params.milk_protein_percentage
    preg_perc = params.herd_pregnant_percentage
    DE = params.diet_digestability_percentage
    Ym = params.methane_conversion_factor_percentage

    # -- Tier 1 ---------------------------------------------------------------
    EF_T1  = ipcc_default['EF_T1_Dairy']
    CH4_T1 = N * (D / 365) * EF_T1

    # -- Tier 2 Simplified ----------------------------------------------------
    # IPCC 2006 Eq. 10.3: FCM-based DMI estimate
    FCM     = 0.4324 * Milk + 16.216 * (Fat / 100 * Milk)
    DMI_T2S = 0.0185 * BW + 0.305 * FCM
    GE_T2S  = DMI_T2S * 18.45
    EF_T2S  = GE_T2S * (Ym / 100) * D / 55.65
    CH4_T2S = N * EF_T2S

    # -- Tier 2 Advanced ------------------------------------------------------
    # IPCC 2006 Eqs. 10.4–10.15
    Cf  = 0.386                          # lactating — IPCC Table 10.4
    C   = ipcc_default['C_female']       # 0.8
    Ca  = ipcc_default['Ca_pasture']     # 0.17  NZ grazing
    Cp  = ipcc_default['Cp_cattle']      # 0.10
    MW  = BW

    NEm = Cf * (BW ** 0.75)
    NEa = Ca * NEm
    NEg = 0                              # mature cow — no growth
    NEl = Milk * (1.47 + 0.40 * Fat)
    NEp = Cp * NEm * (preg_perc / 100)

    REM, REG = rem_reg(DE)
    GE_T2A   = ((NEm + NEa + NEl + NEp) / REM + NEg / REG) / (DE / 100)
    DMI_T2A  = GE_T2A / 18.45
    EF_T2A   = GE_T2A * (Ym / 100) * D / 55.65
    CH4_T2A  = N * EF_T2A

    # -- MPI Method -----------------------------------------------------------
    # NZ Farm Emissions Method 2024 / MPI 2025 Section 4.2
    # ⚠  Best-guess approximation — verify with MPI tools before compliance use
    ME_p   = nz_default['ME_NZ_Dairy']
    Ym_NZ  = nz_default['Ym_NZ_Dairy']

    ME_maint = 0.28 * (BW ** 0.75)
    ME_lact  = Milk * (0.376 * Fat + 0.209 * Protein + 0.948)
    ME_preg  = 0.10 * ME_maint * (preg_perc / 100)
    ME_total = ME_maint + ME_lact + ME_preg

    DMI_MPI = ME_total / ME_p
    GE_MPI  = DMI_MPI * 18.45
    EF_MPI  = GE_MPI * (Ym_NZ / 100) * D / 55.65
    CH4_MPI = N * EF_MPI

    t1 = ResultTier(EF_T1, CH4_T1)
    t2s = ResultTier(EF_T2S, CH4_T2S, GE_T2S, DMI_T2S)
    t2a = ResultTier(EF_T2A, CH4_T2A, GE_T2A, DMI_T2A)
    mpi = ResultTier(EF_MPI, CH4_MPI, GE_MPI, DMI_MPI)

    return EmissionResults(tier_1=t1, tier_2_simplified=t2s, tier_2_advanced=t2a, mpi_method=mpi, NEm=NEm, NEa=NEa,
                           NEl=NEl, NEp=NEp, ME_maint=ME_maint, ME_lact=ME_lact, ME_preg=ME_preg)


# =============================================================================
# DAIRY — DRY COW
# =============================================================================
def ask_and_calc_dairy_dry():
    print('\n  -- Inputs: Dry / Non-Lactating Dairy Cow --')
    N         = ask_int  ('Number of animals')
    D         = ask_int  ('Reporting period (days)',              hint=365)
    BW        = ask_float('Body weight (kg)',                     hint=nz_default['BW_Dairy_Cow'])
    preg_perc = ask_float('Percentage of herd pregnant (%)',      hint=60)
    DE        = ask_float('Diet digestibility DE (%)',            hint=nz_default['DE_NZ_Pasture'])
    Ym        = ask_float('Methane conversion factor Ym (%)',     hint=ipcc_default['Ym'])
    calc_dairy_dry(N, D, BW, preg_perc, DE, Ym)

def calc_dairy_dry(N: int, D: int, BW: float, preg_perc: float, DE: float, Ym: float):
    """
    IPCC Tier 1, Tier 2S, Tier 2 Advanced, and MPI method
    for a dry / non-lactating dairy cow.

    NE components: NEm + NEa + NEp  (NEl = 0)
    Cf = 0.322 (IPCC Table 10.4 — non-lactating)
    C  = 0.8
    """
    # -- Tier 1 ---------------------------------------------------------------
    EF_T1  = ipcc_default['EF_T1_Dairy']
    CH4_T1 = N * (D / 365) * EF_T1

    # -- Tier 2 Simplified ----------------------------------------------------
    # No milk — DMI from BW only
    DMI_T2S = 0.0185 * BW
    GE_T2S  = DMI_T2S * 18.45
    EF_T2S  = GE_T2S * (Ym / 100) * D / 55.65
    CH4_T2S = N * EF_T2S

    # -- Tier 2 Advanced ------------------------------------------------------
    Cf  = 0.322                         # non-lactating — IPCC Table 10.4
    C   = ipcc_default['C_female']
    Ca  = ipcc_default['Ca_pasture']
    Cp  = ipcc_default['Cp_cattle']

    NEm = Cf * (BW ** 0.75)
    NEa = Ca * NEm
    NEg = 0                             # mature — no growth
    NEl = 0                             # not lactating
    NEp = Cp * NEm * (preg_perc / 100)

    REM, REG = rem_reg(DE)
    GE_T2A   = ((NEm + NEa + NEl + NEp) / REM) / (DE / 100)
    DMI_T2A  = GE_T2A / 18.45
    EF_T2A   = GE_T2A * (Ym / 100) * D / 55.65
    CH4_T2A  = N * EF_T2A

    # -- MPI Method -----------------------------------------------------------
    # Dry cow: ME_lact = 0, maintenance + pregnancy only
    ME_p     = nz_default['ME_NZ_Dairy']
    Ym_NZ    = nz_default['Ym_NZ_Dairy']

    ME_maint = 0.28 * (BW ** 0.75)
    ME_preg  = 0.10 * ME_maint * (preg_perc / 100)
    ME_total = ME_maint + ME_preg

    DMI_MPI = ME_total / ME_p
    GE_MPI  = DMI_MPI * 18.45
    EF_MPI  = GE_MPI * (Ym_NZ / 100) * D / 55.65
    CH4_MPI = N * EF_MPI

    # -- Output ---------------------------------------------------------------
    print_recap('Dry / Non-Lactating Dairy Cow', N, D, BW, DE, Ym,
                extras=[f'Pregnant {preg_perc}%  (NEl = 0)'])
    print_tier('Tier 1',              EF_T1,  CH4_T1)
    print_tier('Tier 2 Simplified',   EF_T2S, CH4_T2S, GE=GE_T2S, DMI=DMI_T2S)
    print_tier('Tier 2 Advanced',     EF_T2A, CH4_T2A, GE=GE_T2A, DMI=DMI_T2A)
    print(f'       NEm={NEm:.1f}  NEa={NEa:.1f}  NEl=0  NEp={NEp:.1f} MJ/day')
    print_tier('MPI Method ', EF_MPI, CH4_MPI, GE=GE_MPI, DMI=DMI_MPI)
    print(f'       ME maint={ME_maint:.1f}  ME preg={ME_preg:.1f} MJ/day')


# =============================================================================
# DAIRY — REPLACEMENT HEIFER
# =============================================================================

def ask_and_calc_dairy_heifer():
    print('\n  -- Inputs: Dairy Replacement Heifer --')
    N   = ask_int  ('Number of animals')
    D   = ask_int  ('Reporting period (days)',              hint=365)
    BW  = ask_float('Current body weight (kg)',             hint=nz_default['BW_Dairy_Heifer'])
    MW  = ask_float('Mature body weight (kg)',              hint=nz_default['BW_Dairy_Cow'])
    WG  = ask_float('Daily weight gain (kg/day)',           hint=nz_default['WG_Heifer'])
    DE  = ask_float('Diet digestibility DE (%)',            hint=nz_default['DE_NZ_Pasture'])
    Ym  = ask_float('Methane conversion factor Ym (%)',     hint=ipcc_default['Ym'])
    calc_dairy_heifer(N, D, BW, MW, WG, DE, Ym)


def calc_dairy_heifer(N: int, D: int, BW: float, MW: float, WG: float, DE: float, Ym: float):
    """
    IPCC Tier 1, Tier 2S, Tier 2 Advanced, and MPI method
    for a dairy replacement heifer.

    NE components: NEm + NEa + NEg  (NEl = NEp = 0)
    Cf = 0.322, C = 0.8
    """
    # -- Tier 1 ---------------------------------------------------------------
    EF_T1  = ipcc_default['EF_T1_Other']   # not yet a dairy cow
    CH4_T1 = N * (D / 365) * EF_T1

    # -- Tier 2 Simplified ----------------------------------------------------
    DMI_T2S = 0.022 * BW + 0.6 * WG
    GE_T2S  = DMI_T2S * 18.45
    EF_T2S  = GE_T2S * (Ym / 100) * D / 55.65
    CH4_T2S = N * EF_T2S

    # -- Tier 2 Advanced ------------------------------------------------------
    Cf  = 0.322
    C   = ipcc_default['C_female']          # 0.8
    Ca  = ipcc_default['Ca_pasture']

    NEm = Cf * (BW ** 0.75)
    NEa = Ca * NEm
    NEg = 22.02 * (BW / (C * MW)) * (WG ** 1.097)
    NEl = 0
    NEp = 0

    REM, REG = rem_reg(DE)
    GE_T2A   = (NEm + NEa) / REM / (DE / 100) + NEg / REG / (DE / 100)
    DMI_T2A  = GE_T2A / 18.45
    EF_T2A   = GE_T2A * (Ym / 100) * D / 55.65
    CH4_T2A  = N * EF_T2A

    # -- MPI Method -----------------------------------------------------------
    # Growing animal: ME_gain replaces NEl/NEp
    ME_p     = nz_default['ME_NZ_Dairy']
    Ym_NZ    = nz_default['Ym_NZ_Dairy']

    ME_maint = 0.28 * (BW ** 0.75)
    ME_gain  = (4.1 + 1.3 * WG) / 0.40
    ME_total = ME_maint + ME_gain

    DMI_MPI = ME_total / ME_p
    GE_MPI  = DMI_MPI * 18.45
    EF_MPI  = GE_MPI * (Ym_NZ / 100) * D / 55.65
    CH4_MPI = N * EF_MPI

    # -- Output ---------------------------------------------------------------
    print_recap('Dairy Replacement Heifer', N, D, BW, DE, Ym,
                extras=[f'Mature BW : {MW} kg  |  Weight gain : {WG} kg/day',
                        'NEl = 0  |  NEp = 0'])
    print_tier('Tier 1',              EF_T1,  CH4_T1)
    print_tier('Tier 2 Simplified',   EF_T2S, CH4_T2S, GE=GE_T2S, DMI=DMI_T2S)
    print_tier('Tier 2 Advanced',     EF_T2A, CH4_T2A, GE=GE_T2A, DMI=DMI_T2A)
    print(f'       NEm={NEm:.1f}  NEa={NEa:.1f}  NEg={NEg:.1f} MJ/day')
    print_tier('MPI Method ', EF_MPI, CH4_MPI, GE=GE_MPI, DMI=DMI_MPI)
    print(f'       ME maint={ME_maint:.1f}  ME gain={ME_gain:.1f} MJ/day')


# =============================================================================
# BEEF — BREEDING COW
# =============================================================================
def ask_and_calc_beef_breeding_cow():
    print('\n  -- Inputs: Beef Breeding Cow --')
    N         = ask_int  ('Number of animals')
    D         = ask_int  ('Reporting period (days)',              hint=365)
    BW        = ask_float('Body weight (kg)',                     hint=nz_default['BW_Beef_Cow'])
    preg_perc = ask_float('Percentage of herd pregnant (%)',      hint=80)
    DE        = ask_float('Diet digestibility DE (%)',            hint=nz_default['DE_NZ_Pasture'])
    Ym        = ask_float('Methane conversion factor Ym (%)',     hint=ipcc_default['Ym'])
    calc_beef_breeding_cow(N, D, BW, preg_perc, DE, Ym)


def calc_beef_breeding_cow(N: int, D: int, BW: float, preg_perc: float, DE: float, Ym: float):
    """
    IPCC Tier 1, Tier 2S, Tier 2 Advanced, and MPI method
    for a mature beef breeding cow.

    NE components: NEm + NEa + NEp  (NEl = NEg = 0)
    Cf = 0.322, C = 0.8
    """
    # -- Tier 1 ---------------------------------------------------------------
    EF_T1  = ipcc_default['EF_T1_Other']
    CH4_T1 = N * (D / 365) * EF_T1

    # -- Tier 2 Simplified ----------------------------------------------------
    DMI_T2S = 0.022 * BW
    GE_T2S  = DMI_T2S * 18.45
    EF_T2S  = GE_T2S * (Ym / 100) * D / 55.65
    CH4_T2S = N * EF_T2S

    # -- Tier 2 Advanced ------------------------------------------------------
    Cf  = 0.322
    C   = ipcc_default['C_female']
    Ca  = ipcc_default['Ca_pasture']
    Cp  = ipcc_default['Cp_cattle']
    MW  = BW

    NEm = Cf * (BW ** 0.75)
    NEa = Ca * NEm
    NEg = 0
    NEl = 0
    NEp = Cp * NEm * (preg_perc / 100)

    REM, REG = rem_reg(DE)
    GE_T2A   = ((NEm + NEa + NEp) / REM) / (DE / 100)
    DMI_T2A  = GE_T2A / 18.45
    EF_T2A   = GE_T2A * (Ym / 100) * D / 55.65
    CH4_T2A  = N * EF_T2A

    # -- MPI Method -----------------------------------------------------------
    ME_p     = nz_default['ME_NZ_Beef']
    Ym_NZ    = nz_default['Ym_NZ_Beef']

    ME_maint = 0.28 * (BW ** 0.75)
    ME_preg  = 0.10 * ME_maint * (preg_perc / 100)
    ME_total = ME_maint + ME_preg

    DMI_MPI = ME_total / ME_p
    GE_MPI  = DMI_MPI * 18.45
    EF_MPI  = GE_MPI * (Ym_NZ / 100) * D / 55.65
    CH4_MPI = N * EF_MPI

    # -- Output ---------------------------------------------------------------
    print_recap('Beef Breeding Cow', N, D, BW, DE, Ym,
                extras=[f'Pregnant {preg_perc}%  |  NEl = 0  |  NEg = 0'])
    print_tier('Tier 1',              EF_T1,  CH4_T1)
    print_tier('Tier 2 Simplified',   EF_T2S, CH4_T2S, GE=GE_T2S, DMI=DMI_T2S)
    print_tier('Tier 2 Advanced',     EF_T2A, CH4_T2A, GE=GE_T2A, DMI=DMI_T2A)
    print(f'       NEm={NEm:.1f}  NEa={NEa:.1f}  NEp={NEp:.1f} MJ/day')
    print_tier('MPI Method  ', EF_MPI, CH4_MPI, GE=GE_MPI, DMI=DMI_MPI)
    print(f'       ME maint={ME_maint:.1f}  ME preg={ME_preg:.1f} MJ/day')


# =============================================================================
# BEEF — GROWING / FINISHING
# =============================================================================
def ask_and_calc_beef_growing():
    print('\n  -- Inputs: Growing / Finishing Cattle --')
    N   = ask_int  ('Number of animals')
    D   = ask_int  ('Reporting period (days)',                   hint=365)
    BW  = ask_float('Current body weight (kg)',                  hint=nz_default['BW_Steer'])
    MW  = ask_float('Mature body weight (kg)',                   hint=nz_default['BW_Beef_Cow'])
    WG  = ask_float('Daily weight gain (kg/day)',                hint=nz_default['WG_Growing'])
    DE  = ask_float('Diet digestibility DE (%)',                 hint=nz_default['DE_NZ_Pasture'])
    Ym  = ask_float('Methane conversion factor Ym (%)',          hint=ipcc_default['Ym'])

    SEX_MENU = {
        '1': {'label': 'Female (heifer)',   'note': 'C = 0.8  — IPCC Eq. 10.6'},
        '2': {'label': 'Castrate (steer)',  'note': 'C = 1.0  — IPCC Eq. 10.6'},
        '3': {'label': 'Intact male',       'note': 'C = 1.2  — IPCC Eq. 10.6'},
    }
    sex_key = choose_menu('Sex of animals (affects C in NEg):', SEX_MENU)
    C_values    = {'1': 0.8, '2': 1.0, '3': 1.2}
    sex_labels  = {'1': 'Female (heifer)', '2': 'Castrate (steer)', '3': 'Intact male'}
    C           = C_values[sex_key]
    sex_label   = sex_labels[sex_key]
    calc_beef_growing(N, D, BW, MW, WG, DE, Ym, C)


def calc_beef_growing(N: int, D: int, BW: float, MW: float, WG: float, DE: float, Ym: float, C: float):
    """
    IPCC Tier 1, Tier 2S, Tier 2 Advanced, and MPI method
    for growing or finishing beef cattle (heifers, young bulls, or mixed sex).

    NE components: NEm + NEa + NEg  (NEl = NEp = 0)
    Cf = 0.322, C = 0.8  (female default — adjust C for intact males if needed)
    
    Sex matters here because NEg = 22.02 * (BW / C*MW) * WG^1.097 and C
    differs between sexes (IPCC 2006 Eq. 10.6):
        Female (heifer)  C = 0.8
        Castrate (steer) C = 1.0
        Intact male      C = 1.2

    A higher C means the animal is relatively heavier for its maturity stage,
    so NEg — and therefore GE and EF — are lower per kg of gain.
    Cf = 0.322 for all three sexes (non-lactating / growing).
    NEl = NEp = 0.
    
    """
    # -- Sex selection — sets C (maturity coefficient) ----------------------
    # C affects NEg directly: higher C → lower NEg for the same BW and gain.
    # IPCC 2006 Eq. 10.6 and Table 10.3.
    # -- Tier 1 ---------------------------------------------------------------
    EF_T1  = ipcc_default['EF_T1_Other']
    CH4_T1 = N * (D / 365) * EF_T1

    # -- Tier 2 Simplified ----------------------------------------------------
    DMI_T2S = 0.022 * BW + 0.6 * WG
    GE_T2S  = DMI_T2S * 18.45
    EF_T2S  = GE_T2S * (Ym / 100) * D / 55.65
    CH4_T2S = N * EF_T2S

    # -- Tier 2 Advanced ------------------------------------------------------
    Cf  = 0.322
    #C   = ipcc_default['C_female']      # 0.8 — use C_bull (1.2) for intact males
    Ca  = ipcc_default['Ca_pasture']

    NEm = Cf * (BW ** 0.75)
    NEa = Ca * NEm
    NEg = 22.02 * (BW / (C * MW)) * (WG ** 1.097)
    NEl = 0
    NEp = 0

    REM, REG = rem_reg(DE)
    GE_T2A   = (NEm + NEa) / REM / (DE / 100) + NEg / REG / (DE / 100)
    DMI_T2A  = GE_T2A / 18.45
    EF_T2A   = GE_T2A * (Ym / 100) * D / 55.65
    CH4_T2A  = N * EF_T2A

    # -- MPI Method -----------------------------------------------------------
    ME_p     = nz_default['ME_NZ_Beef']
    Ym_NZ    = nz_default['Ym_NZ_Beef']

    ME_maint = 0.28 * (BW ** 0.75)
    ME_gain  = (4.1 + 1.3 * WG) / 0.40
    ME_total = ME_maint + ME_gain

    DMI_MPI = ME_total / ME_p
    GE_MPI  = DMI_MPI * 18.45
    EF_MPI  = GE_MPI * (Ym_NZ / 100) * D / 55.65
    CH4_MPI = N * EF_MPI

    # -- Output ---------------------------------------------------------------
    print_recap('Growing / Finishing Cattle', N, D, BW, DE, Ym,
                extras=[f'Mature BW : {MW} kg  |  Weight gain : {WG} kg/day',
                        'NEl = 0  |  NEp = 0'])
    print_tier('Tier 1',              EF_T1,  CH4_T1)
    print_tier('Tier 2 Simplified',   EF_T2S, CH4_T2S, GE=GE_T2S, DMI=DMI_T2S)
    print(      '       (Tier 2S does not use C — same for all sexes)')
    print_tier('Tier 2 Advanced',     EF_T2A, CH4_T2A, GE=GE_T2A, DMI=DMI_T2A)
    print(f'       NEm={NEm:.1f}  NEa={NEa:.1f}  NEg={NEg:.1f} MJ/day  (C={C})')
    print_tier('MPI Method  ', EF_MPI, CH4_MPI, GE=GE_MPI, DMI=DMI_MPI)
    print(f'       ME maint={ME_maint:.1f}  ME gain={ME_gain:.1f} MJ/day')


# =============================================================================
# BEEF — BULL
# =============================================================================
def ask_and_calc_beef_bull():
    print('\n  -- Inputs: Bull (Breeding) --')
    N   = ask_int  ('Number of animals')
    D   = ask_int  ('Reporting period (days)',              hint=365)
    BW  = ask_float('Body weight (kg)',                     hint=nz_default['BW_Bull'])
    DE  = ask_float('Diet digestibility DE (%)',            hint=nz_default['DE_NZ_Pasture'])
    Ym  = ask_float('Methane conversion factor Ym (%)',     hint=ipcc_default['Ym'])
    calc_beef_bull(N, D, BW, DE, Ym)


def calc_beef_bull(N: int, D: int, BW: float, DE: float, Ym: float):
    """
    IPCC Tier 1, Tier 2S, Tier 2 Advanced, and MPI method
    for a breeding bull.

    NE components: NEm + NEa  (NEg = NEl = NEp = 0)
    Cf = 0.370  (IPCC Table 10.4 — bull)
    C  = 1.2    (IPCC Eq. 10.6  — bull)
    """
    # -- Tier 1 ---------------------------------------------------------------
    EF_T1  = ipcc_default['EF_T1_Other']
    CH4_T1 = N * (D / 365) * EF_T1

    # -- Tier 2 Simplified ----------------------------------------------------
    DMI_T2S = 0.022 * BW
    GE_T2S  = DMI_T2S * 18.45
    EF_T2S  = GE_T2S * (Ym / 100) * D / 55.65
    CH4_T2S = N * EF_T2S

    # -- Tier 2 Advanced ------------------------------------------------------
    Cf  = 0.370                         # bull — IPCC Table 10.4
    Ca  = ipcc_default['Ca_pasture']

    NEm = Cf * (BW ** 0.75)
    NEa = Ca * NEm
    # NEg = NEp = NEl = 0 for a mature breeding bull

    REM, REG = rem_reg(DE)
    GE_T2A   = (NEm + NEa) / REM / (DE / 100)
    DMI_T2A  = GE_T2A / 18.45
    EF_T2A   = GE_T2A * (Ym / 100) * D / 55.65
    CH4_T2A  = N * EF_T2A

    # -- MPI Method -----------------------------------------------------------
    ME_p     = nz_default['ME_NZ_Beef']
    Ym_NZ    = nz_default['Ym_NZ_Beef']

    ME_maint = 0.28 * (BW ** 0.75)     # maintenance only
    ME_total = ME_maint

    DMI_MPI = ME_total / ME_p
    GE_MPI  = DMI_MPI * 18.45
    EF_MPI  = GE_MPI * (Ym_NZ / 100) * D / 55.65
    CH4_MPI = N * EF_MPI

    # -- Output ---------------------------------------------------------------
    print_recap('Bull (Breeding)', N, D, BW, DE, Ym,
                extras=['Cf=0.370  C=1.2  |  NEg = NEl = NEp = 0'])
    print_tier('Tier 1',              EF_T1,  CH4_T1)
    print_tier('Tier 2 Simplified',   EF_T2S, CH4_T2S, GE=GE_T2S, DMI=DMI_T2S)
    print_tier('Tier 2 Advanced',     EF_T2A, CH4_T2A, GE=GE_T2A, DMI=DMI_T2A)
    print(f'       NEm={NEm:.1f}  NEa={NEa:.1f} MJ/day')
    print_tier('MPI Method  ', EF_MPI, CH4_MPI, GE=GE_MPI, DMI=DMI_MPI)
    print(f'       ME maint={ME_maint:.1f} MJ/day')


# =============================================================================
# BEEF — STEER
# =============================================================================

def ask_and_calc_beef_steer():
    print('\n  -- Inputs: Steer (Castrate, Growing) --')
    N   = ask_int  ('Number of animals')
    D   = ask_int  ('Reporting period (days)',                   hint=365)
    BW  = ask_float('Current body weight (kg)',                  hint=nz_default['BW_Steer'])
    MW  = ask_float('Mature body weight (kg)',                   hint=nz_default['BW_Beef_Cow'])
    WG  = ask_float('Daily weight gain (kg/day)',                hint=nz_default['WG_Growing'])
    DE  = ask_float('Diet digestibility DE (%)',                 hint=nz_default['DE_NZ_Pasture'])
    Ym  = ask_float('Methane conversion factor Ym (%)',          hint=ipcc_default['Ym'])
    calc_beef_steer(N, D, BW, MW, WG, DE, Ym)


def calc_beef_steer(N: int, D: int, BW: float, MW: float, WG: float, DE: float, Ym: float):
    """
    IPCC Tier 1, Tier 2S, Tier 2 Advanced, and MPI method
    for a growing steer (castrated male).

    NE components: NEm + NEa + NEg  (NEl = NEp = 0)
    Cf = 0.322, C = 1.0  (castrate — IPCC Eq. 10.6)
    """
    # -- Tier 1 ---------------------------------------------------------------
    EF_T1  = ipcc_default['EF_T1_Other']
    CH4_T1 = N * (D / 365) * EF_T1

    # -- Tier 2 Simplified ----------------------------------------------------
    DMI_T2S = 0.022 * BW + 0.6 * WG
    GE_T2S  = DMI_T2S * 18.45
    EF_T2S  = GE_T2S * (Ym / 100) * D / 55.65
    CH4_T2S = N * EF_T2S

    # -- Tier 2 Advanced ------------------------------------------------------
    Cf  = 0.322
    C   = ipcc_default['C_castrate']    # 1.0 — castrate, IPCC Eq. 10.6
    Ca  = ipcc_default['Ca_pasture']

    NEm = Cf * (BW ** 0.75)
    NEa = Ca * NEm
    NEg = 22.02 * (BW / (C * MW)) * (WG ** 1.097)
    NEl = 0
    NEp = 0

    REM, REG = rem_reg(DE)
    GE_T2A   = (NEm + NEa) / REM / (DE / 100) + NEg / REG / (DE / 100)
    DMI_T2A  = GE_T2A / 18.45
    EF_T2A   = GE_T2A * (Ym / 100) * D / 55.65
    CH4_T2A  = N * EF_T2A

    # -- MPI Method -----------------------------------------------------------
    ME_p     = nz_default['ME_NZ_Beef']
    Ym_NZ    = nz_default['Ym_NZ_Beef']

    ME_maint = 0.28 * (BW ** 0.75)
    ME_gain  = (4.1 + 1.3 * WG) / 0.40
    ME_total = ME_maint + ME_gain

    DMI_MPI = ME_total / ME_p
    GE_MPI  = DMI_MPI * 18.45
    EF_MPI  = GE_MPI * (Ym_NZ / 100) * D / 55.65
    CH4_MPI = N * EF_MPI

    # -- Output ---------------------------------------------------------------
    print_recap('Steer (Castrate)', N, D, BW, DE, Ym,
                extras=[f'Mature BW : {MW} kg  |  Weight gain : {WG} kg/day',
                        'C=1.0 (castrate)  |  NEl = NEp = 0'])
    print_tier('Tier 1',              EF_T1,  CH4_T1)
    print_tier('Tier 2 Simplified',   EF_T2S, CH4_T2S, GE=GE_T2S, DMI=DMI_T2S)
    print_tier('Tier 2 Advanced',     EF_T2A, CH4_T2A, GE=GE_T2A, DMI=DMI_T2A)
    print(f'       NEm={NEm:.1f}  NEa={NEa:.1f}  NEg={NEg:.1f} MJ/day')
    print_tier('MPI Method', EF_MPI, CH4_MPI, GE=GE_MPI, DMI=DMI_MPI)
    print(f'       ME maint={ME_maint:.1f}  ME gain={ME_gain:.1f} MJ/day')


# =============================================================================
# TOP-LEVEL MENUS
# =============================================================================

SPECIES_MENU = {
    '1': {'label': 'Dairy cattle',        'note': 'Lactating cow, dry cow, heifer'},
    '2': {'label': 'Beef / other cattle', 'note': 'Breeding cow, growing, bull, steer'},
}

DAIRY_MENU = {k: {'label': v['label'], 'note': v['note']} for k, v in DAIRY_SUBCATS.items()}
BEEF_MENU  = {k: {'label': v['label'], 'note': v['note']} for k, v in BEEF_SUBCATS.items()}

# Maps (species_key, subcat_key) → calc function
DISPATCH = {
    ('1', '1'): ask_and_calc_dairy_lactating,
    ('1', '2'): ask_and_calc_dairy_dry,
    ('1', '3'): ask_and_calc_dairy_heifer,
    ('2', '1'): ask_and_calc_beef_breeding_cow,
    ('2', '2'): ask_and_calc_beef_growing,
    ('2', '3'): ask_and_calc_beef_bull,
    ('2', '4'): ask_and_calc_beef_steer,
}


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':

    print('\n' + '=' * 50)
    print('  NZ Methane Emissions Calculator')
    print('  IPCC 2006 / 2019  +  MPI NZ Method')
    print('=' * 50)

    # -- Reporting period ---------------------------------------------------
    print('\n  -- Reporting Period --')
    print(f'  Analysis date : {datetime.datetime.now().strftime("%Y-%m-%d")}')

    while True:
        raw = ask('Start date (YYYY-MM-DD)')
        try:
            start = datetime.datetime.strptime(raw, '%Y-%m-%d')
            break
        except ValueError:
            print('  Invalid format — please use YYYY-MM-DD.')

    print(f'  Reporting start : {start.strftime("%d %b %Y")}')

    # -- Species ------------------------------------------------------------
    species_key = choose_menu('Select species:', SPECIES_MENU)

    # -- Sub-category -------------------------------------------------------
    if species_key == '1':
        subcat_key = choose_menu('Select dairy sub-category:', DAIRY_MENU)
    else:
        subcat_key = choose_menu('Select beef sub-category:', BEEF_MENU)

    # -- Run the matching function ------------------------------------------
    calc_fn = DISPATCH[(species_key, subcat_key)]
    calc_fn()

    # -- Footer -------------------------------------------------------------
    print('\n' + '=' * 50)
#    print('  ⚠  MPI results are best-guess approximations.')
#    print('     Verify with official MPI tools for')
#    print('     compliance / regulatory reporting.')
    print('=' * 50 + '\n')
