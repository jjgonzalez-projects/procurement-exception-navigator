# Procurement Exception Navigator
Independent portfolio demonstration by Juan José González. Synthetic transactions, no Nestlé affiliation.

## Run locally
Python 3.11 or 3.12 recommended.
```
pip install -r requirements.txt
streamlit run app.py
```

## Publish on Streamlit Community Cloud
1. Create a GitHub repository named procurement-exception-navigator.
2. Upload app.py, model.py, data.xlsx and requirements.txt at repository root. Include .streamlit/config.toml for the theme.
3. In Streamlit Community Cloud choose Create app, select the repository and branch, and set app.py as the main file.
4. Choose an available URL name and deploy. Use a public audience for recruiter access.
5. Open the resulting URL in a signed-out browser and check filters, an exception case and the capacity scenario before sharing.
Official guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

This package is not yet deployed. No GitHub or Streamlit account access was assumed.

## Demo narrative
A procurement team needs to understand which invoice exceptions need attention. The app links synthetic purchasing and invoice records, prioritizes open cases, proposes ownership and models the capacity benefit of a routing pilot. Human validation remains part of resolution.

## Status and limits
Implemented: country/category/supplier filters, analytics, unresolved case queue, owner proposals, session-only routing simulation, CSV export and adjustable capacity model.
Proposed only: Power Automate integration, notifications, ERP connectivity and production audit log.
No AI component is implemented. Exception types are seeded labels, not dynamically inferred three-way matches.
Sample baseline: 500 POs; $17,226,246.95 ordered; 483 invoices; 98 historical exceptions; 7 unresolved cases worth $237,337.19. Snapshot 30 Sep 2026.
Capacity defaults: 10,000 annual invoices × 20% exceptions × 80% eligible × 75% adoption × 15 minutes / 60 = 300 hours. This is a hypothetical scenario, not cash savings or measured Nestlé benefit.
