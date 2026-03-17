LOB Public Endpoint Fix
=======================

STEP 1 — Backend (restart uvicorn after):
  Open Auth/routes_fixed.py
  Paste the function from lob_public_endpoint.py
  BEFORE the existing get_lob_config() function
  New endpoint: GET /api/v1/auth/lob-config/public (no auth)

STEP 2 — Frontend (no restart needed):
  Replace pages/monitoring/pre-login.html
  Now fetches from /lob-config/public on load
  Shows real LOBs from API_LOB_MASTER
  selectedLob stored in sessionStorage with name+tracks+database+icon
  All other pages continue to read sessionStorage.getItem('selectedLob')

WHAT selectedLob CONTAINS after this fix:
  { name: 'Digital Technology', tracks: ['CDV3','Track1','Track2'],
    database: 'CQE_NFT', icon: 'x1f4bb', id: 'Digital_Technology' }
