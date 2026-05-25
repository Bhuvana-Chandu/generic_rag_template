from langchain_core.tools import tool
import os
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Global variables to cache loaded data
_vector_store = None
_repair_costs_df = None
_contractors_df = None

def preload_tools():
    """Load FAISS index and CSVs into memory."""
    global _vector_store, _repair_costs_df, _contractors_df
    
    faiss_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage", "faiss_index")
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    
    if os.path.exists(faiss_path):
        _vector_store = FAISS.load_local(faiss_path, OpenAIEmbeddings(), allow_dangerous_deserialization=True)
        
    try:
        _repair_costs_df = pd.read_csv(os.path.join(data_dir, "PropertyDamage_RepairCostTable.csv"))
    except Exception as e:
        print("Failed to load repair cost csv:", e)
        
    try:
        _contractors_df = pd.read_csv(os.path.join(data_dir, "ApprovedContractor_Network.csv"))
    except Exception as e:
        print("Failed to load contractor network csv:", e)

@tool
def policy_rag_retriever(query: str) -> str:
    """
    Search the policy documents and claims procedures for coverage, exclusions, and rules.
    """
    if _vector_store is None:
        return "Knowledge base not initialized."
    
    docs = _vector_store.similarity_search(query, k=4)
    result = []
    for d in docs:
        source = d.metadata.get('source_file', 'Unknown')
        result.append(f"[Source: {source}]\n{d.page_content}")
    
    return "\n\n---\n\n".join(result)

@tool
def damage_cost_estimator(damage_type: str, property_category: str) -> str:
    """
    Query the repair cost table to get indicative estimates.
    Requires damage_type (e.g., 'water damage', 'fire damage') and property_category (e.g., 'semi-detached', 'detached', 'flat').
    """
    if _repair_costs_df is None:
        return "Repair cost data not available."
        
    df = _repair_costs_df
    match = df[(df['damage_type'].str.lower() == damage_type.lower()) & 
               (df['property_category'].str.lower() == property_category.lower())]
               
    if match.empty:
        return f"No cost estimate found for {damage_type} on a {property_category} property."
        
    row = match.iloc[0]
    return f"Indicative estimate for {damage_type} on a {property_category}: {row['min_cost']} to {row['max_cost']} {row['currency']}."

@tool
def contractor_network_lookup(postcode: str, trade_type: str, policy_tier: str) -> str:
    """
    Query the contractor directory using postcode, trade_type, and policy_tier.
    Returns a shortlist of approved contractors.
    """
    if _contractors_df is None:
        return "Contractor data not available."
        
    df = _contractors_df
    # In a real system, postcode would do geographic matching. Here we mock it by just using the first letter if provided.
    area = postcode[0].upper() if postcode else ""
    
    # Filter by trade (Fuzzy match to handle "plumbing" vs "plumbing & heating")
    trade_search = trade_type.lower().replace(" and ", " & ")
    matches = df[df['trade_type'].str.lower().str.contains(trade_search, na=False) | df['trade_type'].str.lower().str.contains(trade_type.lower().split()[0], na=False)]
    
    if matches.empty:
        return f"No approved contractors found for the requested trade: '{trade_type}'. Please check directory."
        
    # Format the results
    results = []
    for _, row in matches.iterrows():
        results.append(f"- {row['company_name']} (Tier: {row['tier_approved']}, Area: {row['city_region']}, Phone: {row['phone']}, Email: {row['email']})")
        
    return f"Approved contractors for {trade_type}:\n" + "\n".join(results)

@tool
def claim_status_tracker(claim_id: str) -> str:
    """
    Simulate a claim lookup by claim ID.
    """
    if not claim_id or claim_id.lower() == "none":
        return "Please provide a valid Claim ID."
        
    # Mock data
    statuses = {
        "cl-12345": "Status: Under Review. Next Step: Awaiting surveyor report.",
        "cl-98765": "Status: Approved. Next Step: Payment processing.",
        "cl-55555": "Status: Awaiting Documents. Next Step: Please upload photo evidence."
    }
    
    return statuses.get(claim_id.lower(), f"Status: Processing. Next Step: Reviewing claim {claim_id}.")

def get_tools():
    return [policy_rag_retriever, damage_cost_estimator, contractor_network_lookup, claim_status_tracker]
