# model.py
"""
Methane emissions calculations following IPCC 2019 guidelines.
Includes Tier 1, Tier 2 Simplified, and Tier 2 Advanced
"""

# --- Default emission factors and parameters ---
DEFAULTS = {
    "Cattle": {
        "Mature dairy": {"EF": 100, "Ym": 6.5, "BW": 600, "Milk": 2200},
        "Mature beef": {"EF": 60, "Ym": 6.5, "BW": 500, "Milk": 0},
        "Heifer": {"EF": 50, "Ym": 6.5, "BW": 400, "Milk": 0},
        "Steer": {"EF": 50, "Ym": 6.5, "BW": 350, "Milk": 0},
        "Calf": {"EF": 20, "Ym": 6.5, "BW": 100, "Milk": 0}
    },
    "Sheep": {
        "Lamb": {"EF": 4.5, "Ym": 4.5, "BW": 35, "Milk": 0},
        "Mature sheep": {"EF": 8, "Ym": 6.0, "BW": 70, "Milk": 0},
        "Ewe": {"EF": 10, "Ym": 6.0, "BW": 70, "Milk": 120}  # annual milk
    }
}

FEED_EN_DENSITY = 18.45  # MJ/kg DM

# --- Tier 1 ---
def calculate_tier1(species, category, stage=None, N=None, days=365):
    """
    Tier 1: Uses default emission factor (EF) per head
    """
    try:
        ef = DEFAULTS[species][category]["EF"]
    except KeyError:
        ef = 50  # fallback
    if N is None: N = 1
    ch4 = ef * N * (days/365) / 1e6  # Gg CH4/year
    return ch4

# --- Tier 2 Simplified ---
def calculate_tier2_simplified(species, category, stage=None, N=None, BW=None, days=365):
    """
    Tier 2 Simplified: Computes DMI based on BW & stage, uses Ym to calculate CH4
    """
    if N is None: N=1
    if BW is None:
        BW = DEFAULTS.get(species, {}).get(category, {}).get("BW", 100)

    # Default Ym
    Ym = DEFAULTS.get(species, {}).get(category, {}).get("Ym", 6.5)

    # Simplified DMI formulas (IPCC 2019, Table 10.4)
    if species=="Cattle":
        if stage in ["growing","finishing"]:
            DMI = BW**0.75 * 0.025
        elif stage=="mature dairy":
            DMI = BW**0.75 * 0.026
        else:
            DMI = BW**0.75 * 0.024
    elif species=="Sheep":
        if stage=="lamb":
            DMI = BW**0.75 * 0.03
        else:
            DMI = BW**0.75 * 0.025
    else:
        DMI = BW**0.75 * 0.025  # fallback

    # CH4 emission: EF = DMI * Ym * days / 55.65
    ef_per_animal = DMI * (Ym/100) * days / 55.65
    ch4 = ef_per_animal * N / 1e3  # convert to Gg/year (adjusted)
    return max(ch4, 0)

# --- Tier 2 Advanced ---
def calculate_tier2_advanced(species, category, stage=None, N=None, BW=None, Milk=None, WG=None, Preg=None, days=365):
    """
    Tier 2 Advanced: Uses IPCC energy requirement method
    """
    if N is None: N=1
    if BW is None: BW = DEFAULTS.get(species, {}).get(category, {}).get("BW", 100)
    if Milk is None: Milk = DEFAULTS.get(species, {}).get(category, {}).get("Milk", 0)
    if WG is None: WG=0
    if Preg is None: Preg=0

    # Set Ym
    Ym = DEFAULTS.get(species, {}).get(category, {}).get("Ym", 6.5)

    # Maintenance energy (MJ/day)
    NEm = 0.386 * BW**0.75  # typical for cattle/sheep

    # Lactation energy
    NEl = Milk * 4.6  # MJ/kg milk

    # Growth energy
    NEg = WG * 22  # MJ/kg gain

    # Pregnancy energy
    NEp = Preg/100 * 7  # MJ/day approximation

    # Total energy
    NE_total = NEm + NEl + NEg + NEp

    # Gross energy intake (GE)
    GE = NE_total / 0.82  # efficiency factor

    # DMI
    DMI = GE / FEED_EN_DENSITY

    # EF per animal
    EF_animal = DMI * (Ym/100) * days / 55.65  # kg CH4 per animal
    ch4 = EF_animal * N / 1e3  # Gg/year
    return max(ch4,0)
