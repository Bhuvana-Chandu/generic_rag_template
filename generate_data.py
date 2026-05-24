import os
import pandas as pd

def create_synthetic_data():
    os.makedirs("data", exist_ok=True)
    
    # 1. Property Damage Repair Cost Table (CSV)
    repair_costs = pd.DataFrame([
        {"damage_type": "water damage", "property_category": "semi-detached", "min_cost": 2000, "max_cost": 8000, "currency": "GBP"},
        {"damage_type": "water damage", "property_category": "detached", "min_cost": 3000, "max_cost": 12000, "currency": "GBP"},
        {"damage_type": "water damage", "property_category": "flat", "min_cost": 1000, "max_cost": 5000, "currency": "GBP"},
        {"damage_type": "fire damage", "property_category": "semi-detached", "min_cost": 15000, "max_cost": 50000, "currency": "GBP"},
        {"damage_type": "fire damage", "property_category": "detached", "min_cost": 20000, "max_cost": 80000, "currency": "GBP"},
        {"damage_type": "fire damage", "property_category": "flat", "min_cost": 10000, "max_cost": 40000, "currency": "GBP"},
        {"damage_type": "storm damage", "property_category": "semi-detached", "min_cost": 500, "max_cost": 4000, "currency": "GBP"},
        {"damage_type": "storm damage", "property_category": "detached", "min_cost": 800, "max_cost": 6000, "currency": "GBP"},
        {"damage_type": "subsidence", "property_category": "semi-detached", "min_cost": 10000, "max_cost": 40000, "currency": "GBP"},
        {"damage_type": "subsidence", "property_category": "detached", "min_cost": 15000, "max_cost": 60000, "currency": "GBP"},
    ])
    repair_costs.to_csv("data/repair_cost_table.csv", index=False)

    # 2. Approved Contractor Network Directory (CSV)
    contractors = pd.DataFrame([
        {"contractor_name": "Rapid Repair Co.", "trade_type": "water damage", "coverage_area": "M", "tier_approval": "Standard", "contact": "0161 123 4567"},
        {"contractor_name": "Manchester Floods Ltd", "trade_type": "water damage", "coverage_area": "M", "tier_approval": "Comprehensive", "contact": "0161 987 6543"},
        {"contractor_name": "Safe & Dry Solutions", "trade_type": "water damage", "coverage_area": "L", "tier_approval": "Standard", "contact": "0151 444 5555"},
        {"contractor_name": "Blaze Restorations", "trade_type": "fire damage", "coverage_area": "M", "tier_approval": "Standard", "contact": "0161 222 3333"},
        {"contractor_name": "Peak Roofers", "trade_type": "storm damage", "coverage_area": "M", "tier_approval": "Comprehensive", "contact": "0161 777 8888"},
        {"contractor_name": "Foundation Fixers", "trade_type": "subsidence", "coverage_area": "M", "tier_approval": "Comprehensive", "contact": "0161 555 6666"},
    ])
    contractors.to_csv("data/contractor_network.csv", index=False)
    
    # 3. Claims Procedure & Evidence Guide (Markdown)
    with open("data/claims_procedure.md", "w") as f:
        f.write("""# Claims Procedure & Evidence Guide

## Filing a Claim
To file a claim, follow these steps:
1. Ensure your safety first.
2. Document the damage extensively with clear photographs and videos.
3. Prevent further damage if safe to do so (e.g., turn off mains water for a leak).
4. Contact the claims department immediately or use the online portal.
5. Provide your policy number and a detailed description of the incident.

## Required Documentation
*   Photographs of the damage.
*   Police report (if theft or malicious damage).
*   Receipts for emergency repairs.
*   Original purchase receipts for damaged contents (if claiming for contents).
""")

    # 4. Home Insurance Policy Document (Markdown)
    with open("data/policy_document.md", "w") as f:
        f.write("""# Home Insurance Policy Summary

## Covered Perils
*   **Fire:** Covered under all tiers (Standard, Comprehensive, Landlord).
*   **Storm:** Covered under all tiers. Excludes fences, gates, and hedges.
*   **Water Damage (Escape of Water):** Covered. Excludes damage occurring if the property is unoccupied for more than 30 consecutive days.
*   **Theft:** Covered. Requires signs of forced entry for Standard tier. Comprehensive covers unforced entry.
*   **Subsidence:** Covered under Comprehensive and Landlord tiers. Excludes coastal erosion.

## Exclusions
*   Gradual deterioration or wear and tear.
*   Damage caused by pets (unless Accidental Damage add-on is purchased).
*   Mould or damp not directly resulting from a covered peril.
""")

    # 5. Definitions and Glossary (Markdown)
    with open("data/glossary.md", "w") as f:
        f.write("""# Home Insurance Glossary

*   **Excess:** The amount you must pay towards any claim.
*   **Indemnity:** Putting you back in the same financial position you were in immediately before the loss.
*   **New-for-old:** Replacing damaged items with new items of equivalent specification.
*   **Subrogation:** The insurer's right to recover claim costs from a responsible third party.
""")

if __name__ == "__main__":
    create_synthetic_data()
    print("Synthetic data generated in data/ folder.")
