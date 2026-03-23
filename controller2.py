# controller.py
from model2 import calculate_tier1, calculate_tier2_simplified, calculate_tier2_advanced

class MethaneController:
    def compute_ch4(self, row_values):
        species, category, stage, N, BW, Milk = row_values[:6]
        try: N = int(N)
        except: N=None
        try: BW = float(BW)
        except: BW=None
        try: Milk = float(Milk)
        except: Milk=None

        t1 = calculate_tier1(species, category, stage, N)
        t2s = calculate_tier2_simplified(species, category, stage, N, BW)
        t2a = calculate_tier2_advanced(species, category, stage, N, BW, Milk)
        return [round(t1,3), round(t2s,3), round(t2a,3)]
