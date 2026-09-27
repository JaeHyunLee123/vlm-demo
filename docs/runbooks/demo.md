# Refrigerant Nameplate Analysis demo runbook

This runbook is the account-specific handoff for the Refrigerant Nameplate Analysis POC. It deliberately keeps the Shared API Key out of Git, GitHub Actions, and the static frontend.

## One-time account setup

1. Create a Modal account and workspace. Add a payment method if Modal requires it for GPU access, then review the current billing page and configure every available spend limit or alert before deploying.
2. Install the approved backend dependencies in an isolated environment, authenticate the Modal CLI, and create a six-character random Shared API Key. Do not save that value in the repository or a checked-in `.env` file.

   ```sh
   .venv/bin/python -m pip install -r backend/requirements.txt
   .venv/bin/modal setup
   .venv/bin/modal secret create refrigerant-demo-secret ANALYSIS_API_KEY=ABC123
   ```

   Replace `ABC123` with the real six-character value only in the terminal or Modal dashboard. The secret name and environment-variable name must remain exactly `refrigerant-demo-secret` and `ANALYSIS_API_KEY`.

3. Deploy the API from the repository root and copy the public HTTPS URL printed for the ASGI endpoint.

   ```sh
   .venv/bin/modal deploy backend/modal_app.py --stream-logs
   ```

4. In GitHub, open **Settings → Pages** and select **GitHub Actions** as the source. Then open **Settings → Secrets and variables → Actions → Variables** and create the repository variable `VITE_API_BASE_URL` with the copied Modal HTTPS URL. It is public configuration, not a secret; do not add the Shared API Key there.
5. Push the `main` branch. The `Deploy GitHub Pages` workflow builds the frontend and publishes it. It stops before publishing if `VITE_API_BASE_URL` is absent. The resulting site URL appears in the workflow's deployment summary.

## Before the demo

1. Open the GitHub Pages URL and enter the Shared API Key manually.
2. Use one supplied Nameplate Image to make a prewarm request. Record its Analysis Time and note it as a Cold Analysis if Modal had no active worker.
3. Run a second request after the model has loaded. Record it as a Warm Analysis.
4. Keep the Modal dashboard open on the deployed application's logs and usage/billing view. The service has at most one T4 worker and a 120-second idle scale-down window, so a later request may become cold again.

## POC evidence sheet

Run each supplied Nameplate Image against the deployed API. Record a single returned Refrigerant Type even when it is marked unverified; do not replace an Analysis Failure with an inference from another label field.

| Nameplate Image | API status | Refrigerant Type or `분석 실패` | Analysis Time (s) | Cold / Warm | Modal observed usage |
| --- | --- | --- | ---: | --- | --- |
| `f8ce07effe0e5.jpg` | | | | | |
| `images (1).jpeg` | | | | | |
| `images (2).jpeg` | | | | | |
| `images (3).jpeg` | | | | | |
| `images.jpeg` | | | | | |

If the five-image result is inadequate in accuracy or latency, record the evidence and revisit the L4 fallback in ADR-0001. Do not change models merely to avoid an Analysis Failure.

## Operational checks and cleanup

- Check the deployed app's Modal dashboard logs for raw model output and server-side failure reasons. The UI should show a Refrigerant Type with its verification notice, or `분석 실패`.
- Record current Modal usage/cost from the dashboard after the run. Pricing and plan limits are account- and date-dependent, so treat the current dashboard as the source of truth.
- When the demo is finished, stop the deployed Modal app from the dashboard or with the Modal CLI to prevent new requests. Rotate the Shared API Key by replacing the Modal secret and redeploying before reusing the demo.
