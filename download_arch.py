import base64
import json
import urllib.request
import os

mermaid_code = """
graph TD
    A[User Query] -->|POST /chat| B(FastAPI Gateway)
    B --> C((Orchestrator))
    C --> D[Vision Agent]
    D --> E[Memory Extraction]
    E --> F[Intent Classifier]
    F --> G{Tool Dispatcher}
    
    G -->|POLICY_Q_A| T1[FAISS Vector DB]
    G -->|COST_ESTIMATION| T2[Repair Cost CSV]
    G -->|CONTRACTOR_LOOKUP| T3[Contractor CSV]
    G -->|CLAIM_STATUS| T4[Claim Tracker]
    G -->|OUT_OF_SCOPE| T5[Bypass Tools]

    T1 --> H
    T2 --> H
    T3 --> H
    T4 --> H
    T5 --> H

    H[Synthesis Agent] --> I[Guardrail Evaluator]
    I -->|Safe| J[Stream to User]
    I -->|Unsafe| K[Rewrite Answer]
    K --> J
"""

state = {
    "code": mermaid_code.strip(),
    "mermaid": '{"theme": "default"}',
    "autoSync": True,
    "updateDiagram": True
}

# Encode to base64 for the mermaid.ink API
json_str = json.dumps(state)
b64_str = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
url = "https://mermaid.ink/img/" + b64_str

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "architecture_flow.png")

try:
    print("Downloading architecture diagram...")
    urllib.request.urlretrieve(url, output_path)
    print(f"Successfully downloaded to {output_path}")
except Exception as e:
    print(f"Failed to download image: {e}")
