"""
defaults.py
===========
Default values for the CH4 emissions calculator.

Sources:
  - IPCC 2006 Guidelines Vol.4 Ch.10 (Tables 10.2, 10.4, 10.5, 10.7, 10.11, 10.12)
  - IPCC 2019 Refinement Vol.4 Ch.10
  - MPI Methodology 2025 / NZ Farm Emissions Method 2024
"""

# ---------------------------------------------------------------------------
# IPCC constants
# ---------------------------------------------------------------------------

ipcc_default = {

    # -- Tier 1 emission factors (kg CH4 / head / year) ---------------------
    # IPCC 2006 Table 10.11 — Oceania region
    'EF_T1_Dairy':  100,   # dairy cows (~2 200 kg milk/head/yr)
    'EF_T1_Other':   60,   # beef cows, bulls, growing cattle
    'EF_T1_Sheep':    8,   # mature sheep

    # -- Methane conversion factor (Ym, %) ----------------------------------
    # IPCC 2006 Table 10.12
    'Ym':       6.5,
    'Ym_sheep': 6.5,

    # -- Net energy for maintenance coefficient (Cf, MJ / kg BW^0.75 / day)
    # IPCC 2006 Table 10.4
    'Cf_dairy':    0.386,   # lactating dairy cows
    'Cf_nondairy': 0.322,   # non-lactating cows, steers, heifers, growing cattle
    'Cf_bull':     0.370,   # bulls
    'Cf_sheep':    0.217,   # mature sheep
    'Cf_lamb':     0.236,   # lambs (multiply by 1.15 for intact males)

    # -- Maturity coefficient C ---------------------------------------------
    # IPCC 2006 Eq. 10.6: NEg = 22.02 * (BW / C*MW)^0.75 * WG^1.097
    'C_female':    0.8,
    'C_castrate':  1.0,
    'C_bull':      1.2,

    # -- Activity coefficient (Ca) ------------------------------------------
    # IPCC 2006 Table 10.5
    'Ca_stall':   0.00,
    'Ca_pasture': 0.17,    # typical NZ grazing
    'Ca_open':    0.36,    # extensive rangeland

    # -- Sheep activity coefficients (per kg BW^0.75) ----------------------
    'Ca_sheep_flat':  0.0107,
    'Ca_sheep_hilly': 0.0240,
    'Ca_sheep_housed': 0.0090,

    # -- Net energy for pregnancy coefficient (Cp) --------------------------
    # IPCC 2006 Table 10.7
    'Cp_cattle':         0.10,
    'Cp_sheep_single':   0.077,
    'Cp_sheep_twins':    0.126,
    'Cp_sheep_triplets': 0.150,

    # -- Diet digestibility (DE, %) -----------------------------------------
    # IPCC 2006 Table 10.2
    'DE_feedlot': 80,
    'DE_pasture': 65,
    'DE_low':     50,

    # -- Sheep growth energy coefficients -----------------------------------
    # IPCC 2006 Table 10.6  (MJ / kg BW / kg gain)
    'a_sheep_male':      2.5,
    'b_sheep_male':      0.35,
    'a_sheep_castrate':  4.4,
    'b_sheep_castrate':  0.32,
    'a_sheep_female':    2.1,
    'b_sheep_female':    0.45,
}


# ---------------------------------------------------------------------------
# NZ / MPI specific defaults
# ---------------------------------------------------------------------------

nz_default = {

    # -- Typical body weights (kg) ------------------------------------------
    'BW_Dairy_Cow':   500,
    'BW_Dairy_Heifer':350,
    'BW_Bull':        600,
    'BW_Beef_Cow':    450,
    'BW_Steer':       350,
    'BW_Sheep':        40,
    'BW_Lamb':         20,

    # -- Weight gains (kg/day) ----------------------------------------------
    'WG_Heifer':      0.41,
    'WG_Growing':     0.41,
    'WG_Mature':      0.0,

    # -- Dairy production ---------------------------------------------------
    'Milk':      12.1,   # kg/head/day
    'Fat':        4.8,   # %
    'Protein':    3.7,   # %
    'preg_perc': 92.0,   # % of herd pregnant

    # -- Pasture quality ----------------------------------------------------
    'DE_NZ_Pasture':  65,    # digestibility %
    'ME_NZ_Dairy':    11.0,  # MJ ME/kg DM
    'ME_NZ_Beef':     10.5,  # MJ ME/kg DM
    'ME_NZ_Sheep':    10.0,  # MJ ME/kg DM

    # -- NZ-specific Ym (%) ------------------------------------------------
    'Ym_NZ_Dairy': 6.5,
    'Ym_NZ_Beef':  6.5,
    'Ym_NZ_Sheep': 6.0,

    # -- Wool production (kg/head/year) ------------------------------------
    'WoolGrowth_Ewe':  4.0,
    'WoolGrowth_Ram':  5.0,
    'WoolGrowth_Lamb': 2.5,
}


# ---------------------------------------------------------------------------
# Sub-category coefficient tables
#
# Each entry pre-sets the IPCC coefficients that differ between sub-categories.
# Keys match what calc_* functions expect.  The calc functions then only need
# to ask the user for production/management parameters (BW, milk, WG, etc.).
#
# Fields per entry:
#   label       : display name shown in the menu
#   Cf          : net energy maintenance coefficient
#   C           : maturity coefficient (used in NEg)
#   has_NEg     : True if the animal is growing (WG input required)
#   has_NEl     : True if the animal is lactating (milk inputs required)
#   has_NEp     : True if the animal can be pregnant
#   EF_T1       : Tier 1 emission factor key in ipcc_default
#   BW_default  : default body weight key in nz_default
#   WG_default  : default weight gain key in nz_default (None if mature)
#   note        : short description printed under the menu option
# ---------------------------------------------------------------------------

DAIRY_SUBCATS = {
    '1': {
        'label':      'Lactating dairy cow',
        'Cf':         0.386,
        'C':          0.8,
        'has_NEg':    False,
        'has_NEl':    True,
        'has_NEp':    True,
        'EF_T1':      'EF_T1_Dairy',
        'BW_default': 'BW_Dairy_Cow',
        'WG_default': None,
        'note':       'Full NE build-up: NEm + NEa + NEl + NEp',
    },
    '2': {
        'label':      'Dry / non-lactating dairy cow',
        'Cf':         0.322,
        'C':          0.8,
        'has_NEg':    False,
        'has_NEl':    False,
        'has_NEp':    True,
        'EF_T1':      'EF_T1_Dairy',
        'BW_default': 'BW_Dairy_Cow',
        'WG_default': None,
        'note':       'NEl = 0 (no milk). Uses Cf_nondairy = 0.322',
    },
    '3': {
        'label':      'Dairy replacement heifer',
        'Cf':         0.322,
        'C':          0.8,
        'has_NEg':    True,
        'has_NEl':    False,
        'has_NEp':    False,
        'EF_T1':      'EF_T1_Other',
        'BW_default': 'BW_Dairy_Heifer',
        'WG_default': 'WG_Heifer',
        'note':       'Growing animal: NEg > 0. NEl = NEp = 0',
    },
}

BEEF_SUBCATS = {
    '1': {
        'label':      'Beef breeding cow',
        'Cf':         0.322,
        'C':          0.8,
        'has_NEg':    False,
        'has_NEl':    False,
        'has_NEp':    True,
        'EF_T1':      'EF_T1_Other',
        'BW_default': 'BW_Beef_Cow',
        'WG_default': None,
        'note':       'Mature female. NEp uses Cp_cattle = 0.10',
    },
    '2': {
        'label':      'Growing / finishing cattle',
        'Cf':         0.322,
        'C':          0.8,
        'has_NEg':    True,
        'has_NEl':    False,
        'has_NEp':    False,
        'EF_T1':      'EF_T1_Other',
        'BW_default': 'BW_Steer',
        'WG_default': 'WG_Growing',
        'note':       'Heifers, steers, or young bulls being finished',
    },
    '3': {
        'label':      'Bull (breeding)',
        'Cf':         0.370,
        'C':          1.2,
        'has_NEg':    False,
        'has_NEl':    False,
        'has_NEp':    False,
        'EF_T1':      'EF_T1_Other',
        'BW_default': 'BW_Bull',
        'WG_default': None,
        'note':       'Cf_bull = 0.370, C_bull = 1.2. NEg = NEl = NEp = 0',
    },
    '4': {
        'label':      'Steer (castrate, growing)',
        'Cf':         0.322,
        'C':          1.0,
        'has_NEg':    True,
        'has_NEl':    False,
        'has_NEp':    False,
        'EF_T1':      'EF_T1_Other',
        'BW_default': 'BW_Steer',
        'WG_default': 'WG_Growing',
        'note':       'C_castrate = 1.0. Growing: NEg > 0',
    },
}
