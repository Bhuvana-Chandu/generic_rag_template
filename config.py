import os

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# UI Aesthetics
APP_TITLE = "Property Insurance AI Copilot"
APP_SUBTITLE = "Your Claims & Coverage Assistant"

# Modern Minimal AI Workspace Theme
THEME_DARK = {
    "primary": "#6366F1",
    "primary_hover": "#4F46E5",
    "background": "#0F172A",
    "card_bg": "#111827",
    "sidebar": "#0B1220",
    "ai_bubble": "#1E293B",
    "text": "#F8FAFC",
    "text_dim": "#94A3B8",
    "border": "#243041",
    "shadow": "rgba(0,0,0,0.25)"
}

THEME_LIGHT = {
    "primary": "#4F46E5",
    "primary_hover": "#4338CA",
    "background": "#F5F7FB",
    "card_bg": "#FFFFFF",
    "sidebar": "#FFFFFF",
    "ai_bubble": "#EEF2FF",
    "text": "#111827",
    "text_dim": "#6B7280",
    "border": "#E5E7EB",
    "shadow": "rgba(0,0,0,0.06)"
}

# Example Queries
EXAMPLE_QUERIES = [
    "I have storm damage to my semi-detached house in M1.",
    "What is my coverage for subsidence?",
    "How much will it cost to repair water damage?",
    "Find approved contractors for fire damage.",
    "What is the status of claim ID CL-12345?",
]

# Intent Labels
INTENT_METADATA = {
    "POLICY_Q_A": {"color": "blue", "icon": "📄"},
    "COST_ESTIMATION": {"color": "orange", "icon": "💰"},
    "CONTRACTOR_LOOKUP": {"color": "green", "icon": "👷"},
    "CLAIM_STATUS": {"color": "purple", "icon": "📊"}
}
