import os
import json
from datetime import datetime

def generate_neotec_application():
    """
    Generates a placeholder for the NEOTEC grant application.
    In a real implementation, this would involve using templates (e.g., Jinja2)
    and pulling data from various project sources.
    """
    print("--- Generating NEOTEC Grant Application ---")

    # Environment variables set by the VS Code task
    deadline_str = os.getenv('DEADLINE', '2025-06-12')
    amount_str = os.getenv('AMOUNT', '325000')
    project_name = os.getenv('PROJECT', 'Phoenix Hydra')

    try:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
        amount = int(amount_str)
    except (ValueError, TypeError) as e:
        print(f"Error parsing environment variables: {e}")
        return

    application = {
        "grant_program": "NEOTEC 2025",
        "project_name": project_name,
        "submission_deadline": deadline.isoformat(),
        "requested_amount_eur": amount,
        "trl_level": "6-9",
        "project_summary": {
            "title": "Phoenix Hydra: Self-Derived AI and Multimedia Automation",
            "description": "A self-hosted automation stack using NCA Toolkit for multimedia processing and AI workflows, designed for enterprise-readiness and open-source flexibility.",
            "market_size_eur": "2.5B (Multimedia Automation Market)",
            "competitive_advantage": "Self-hosted, open-source, enterprise-ready, and modular cellular architecture."
        },
        "team": {
            "cto": "Principal Systems Architect",
            "tech_stack": "n8n, Windmill, NCA Toolkit, Podman, systemd",
            "location": "Barcelona, Spain"
        },
        "financials_projection": {
            "2025_revenue_eur": 400000,
            "2026_revenue_eur": 835000,
            "2027_revenue_eur": 3480000
        },
        "generated_at": datetime.now().isoformat()
    }

    output_filename = f"NEOTEC_application_{datetime.now().strftime('%Y%m%d')}.json"
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(application, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated NEOTEC application draft: {output_filename}")
    print("Next steps: Review the generated JSON, complete the full proposal document, and submit before the deadline.")

if __name__ == "__main__":
    generate_neotec_application()
