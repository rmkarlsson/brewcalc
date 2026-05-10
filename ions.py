'''
1. Molar massor
- Ca: 40.08 g/mol
- Cl: 35.45 g/mol (och det finns två stycken)
2. Molar massa för CaCl₂
M_{CaCl_2}=40.08+2\times 35.45=110.98\  \mathrm{g/mol}
3. Molar massa för klorid (två Cl⁻)
M_{Cl^-}=2\times 35.45=70.90\  \mathrm{g/mol}
4. Massprocent klorid
\mathrm{Cl\% }=\frac{70.90}{110.98}\times 100\approx 63.9\% 



📐 Beräkning av massprocent sulfat i CaSO₄
1. Molar massor
- Ca: 40.08 g/mol
- S: 32.06 g/mol
- O₄: 4 × 16.00 = 64.00 g/mol
2. Molar massa för CaSO₄
M_{CaSO_4}=40.08+32.06+64.00=136.14\  \mathrm{g/mol}
3. Molar massa för sulfatdelen (SO₄²⁻)
M_{SO_4}=32.06+64.00=96.06\  \mathrm{g/mol}
4. Massprocent sulfat
\mathrm{Sulfat\% }=\frac{96.06}{136.14}\times 100\approx 70.6\% 
'''


from pydantic import BaseModel


SALT_DB = {
    "Calcium chloride": {
        "Ca": 38,
        "Cl": 64
    },
    "Calcium sulfate": {
        "Ca": 30,
        "S": 70
    }
}

class ion_estimator:
    def __init__(self, salt_db: dict[str, dict[str, float]]):
        self.salt_db = salt_db

    def estimate_salt_amount(self, salt_name: str, amount_ppm: float) -> float:
        if salt_name not in self.salt_db:
            raise ValueError(f"Salt '{salt_name}' not found in database.")
        
        ion_percentages = self.salt_db[salt_name]
        ion_contributions = {ion: (percentage / 100) * amount_ppm for ion, percentage in ion_percentages.items()}
        return ion_contributions
