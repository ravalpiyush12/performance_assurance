LOB Config + AppD Config Complete Build
=========================================

FRONTEND (no restart):
  admin/lob-config.html
    - List all LOBs from API_LOB_MASTER grouped by LOB name
    - Add new LOB with multiple tracks (chip input)
    - Edit existing LOB (track list editable)
    - Add track to existing LOB
    - Delete individual track
    - Enable/Disable entire LOB

  admin/appd-config.html
    - LOB + Track selector at top (pre-fills from session)
    - 4 sub-tabs: Connection / Applications / Saved Configs / Discovery Results
    - Auth: Client ID+Secret (OAuth2) / Username+Password / API Token
      All credentials as env var NAMES only - never stored
    - Test Connection: calls POST /appd/test-connection
    - Save Connection: calls POST /nft/config/appd
    - Applications: add/save/remove apps with name, ID, frequency
    - Saved Configs: list/delete existing discovery configs
    - Discovery Results: run now + view discovered tiers/nodes
      Edit 'expected active nodes' per tier with Save button

BACKEND (restart uvicorn after):
  backend/lob_config_endpoints.py
    Add to Auth/routes_fixed.py:
    - POST   /auth/lob-config              (add/update LOB+Track)
    - DELETE /auth/lob-config/{lob}/{track} (remove track)
    - PUT    /auth/lob-config/{lob}/status  (enable/disable LOB)

  backend/appd_oauth2_endpoint.py
    Add to monitoring/appd/routes.py:
    - POST   /appd/test-connection   (OAuth2/basic/token test)
    - POST   /appd/applications      (save app to APPD_APPLICATIONS_MASTER)
    - DELETE /appd/config/{name}     (soft delete config)

SQL — Add column if not exists in APPD_APPLICATIONS_MASTER:
  ALTER TABLE APPD_APPLICATIONS_MASTER ADD (
    APPLICATION_ID_APPD VARCHAR2(50),
    DISCOVERY_FREQUENCY VARCHAR2(20) DEFAULT 'daily'
  );
  COMMIT;

ENV VARS to set on server (example for Digital Technology):
  APPD_CLIENT_ID_DIGTECH=<your client id>
  APPD_CLIENT_SECRET_DIGTECH=<your client secret>
