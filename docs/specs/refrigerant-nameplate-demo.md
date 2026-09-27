# Refrigerant Nameplate Analysis demo

## Problem Statement

For tomorrow's demonstration, an operator needs a small, credible way to upload an air-conditioner outdoor-unit **Nameplate Image** and learn its **Refrigerant Type**. The proof of concept must run the VLM directly so the team can measure realistic **Analysis Time** and operating cost. A result must never be inferred: only an explicitly and confidently readable refrigerant designation is an **Analysis Success**; all other outcomes are an **Analysis Failure**.

## Solution

Provide a React and TypeScript single-page demo, deployable to GitHub Pages, backed by a Python API on Modal. The API accepts one **Supported Image** and a **Shared API Key**, runs Qwen2.5-VL-3B-Instruct directly on a scale-to-zero T4 GPU worker, and returns one clearly read **Refrigerant Type** plus **Analysis Time**. A known-type list is returned as verification metadata only; a single, legible designation outside that list is still displayed. An unreadable or ambiguous result returns the Korean message `분석 실패` plus **Analysis Time**. The application has no database, user accounts, background jobs, or custom CSS.

## User Stories

1. As a demo presenter, I want to choose a Nameplate Image with a standard file picker, so that I can demonstrate the flow without drag-and-drop complexity.
2. As a demo presenter, I want to enter the Shared API Key, so that only people given the demo secret can invoke analysis.
3. As a demo presenter, I want to submit one selected Nameplate Image for analysis, so that I can show the direct VLM result.
4. As a demo presenter, I want to see a clearly read Refrigerant Type after an Analysis Success, including a visible warning when it is outside the known-type list, so that I can communicate the result clearly without hiding the model reading.
5. As a demo presenter, I want to see `분석 실패` rather than a guessed refrigerant when the image is unreadable, unsupported, lacks a visible refrigerant, or is not a nameplate, so that the demo does not make false claims.
6. As a demo presenter, I want to see Analysis Time for both an Analysis Success and an Analysis Failure, so that latency can be discussed honestly.
7. As a POC evaluator, I want Cold Analysis and Warm Analysis to be distinguishable from observed timing and Modal logs, so that I can estimate the effect of scale-to-zero behavior.
8. As a POC evaluator, I want the Inference Model to run directly on a GPU worker rather than through a hosted VLM API, so that measured cost and latency describe model operation.
9. As a backend caller, I want exactly one analysis endpoint, so that the integration surface stays small.
10. As a backend caller, I want to send the Shared API Key in the `X-API-Key` header and the Nameplate Image as the `image` multipart field, so that the API contract is unambiguous.
11. As a backend caller, I want an invalid or missing Shared API Key to receive a 401 response, so that the API rejects unauthorised requests.
12. As a backend caller, I want invalid input to receive a 400 response, so that I can correct the request without mistaking it for an Analysis Failure.
13. As a backend caller, I want a successful response to contain `status: "success"`, `refrigerant_type`, `is_verified`, and `analysis_time_seconds`, so that I can consume a clearly read result and its known-type-list status consistently.
14. As a backend caller, I want a non-confirmed analysis to contain `status: "failure"`, `message: "분석 실패"`, and `analysis_time_seconds`, so that I receive no invented Refrigerant Type.
15. As an operator, I want JPEG, PNG, and WebP Nameplate Images up to 10 MB supported, so that common camera and saved image formats work in the demo.
16. As an operator, I want oversized Supported Images normalized to a 1,920-pixel maximum edge before inference, so that analysis is bounded and repeatable.
17. As an operator, I want images outside the supported formats or size limit rejected before model execution, so that GPU time is not spent on unusable input.
18. As a safety-conscious stakeholder, I want the model prompted to return one strict structured Candidate Refrigerant Type or no candidate, so that server-side confirmation can reject ambiguous output.
19. As a safety-conscious stakeholder, I want the service to normalize and validate exactly one refrigerant designation before declaring Analysis Success, so that prose, multiple values, and malformed model output do not leak through as results.
20. As an operator, I want raw model output and failure reasons recorded only in server logs, so that the UI remains simple while troubleshooting remains possible.
21. As an operator, I want Modal real-time logs and usage visible during the demo, so that I can observe requests and later record usage manually.
22. As a cost-conscious operator, I want one T4 GPU worker at most and scale-to-zero after idle time, so that the POC avoids unnecessary GPU spend.
23. As a demo presenter, I want a prewarm request before the presentation, so that the live demo is less likely to begin with cold-start latency.
24. As a frontend maintainer, I want the frontend built with React, TypeScript, Axios, and Water CSS only, so that the requested stack stays lightweight.
25. As a frontend maintainer, I want no separately authored CSS rules, so that Water CSS supplies the visual baseline without an additional styling system.
26. As a frontend maintainer, I want the GitHub Pages deployment to be produced by GitHub Actions from the main branch, so that deployment is repeatable.
27. As an infrastructure maintainer, I want the Python service deployable with Modal's Python workflow and no Dockerfile or Docker CLI workflow, so that backend deployment remains simple.
28. As a future evaluator, I want all five supplied sample images exercised against the initial model, so that the model choice is supported by POC evidence.
29. As a future evaluator, I want a larger GPU/model option considered only when those sample results are inadequate, so that cost increases are justified by evidence.

## Implementation Decisions

- The system consists of a static React/TypeScript frontend and a Python backend; it has no database or persistent application records.
- The frontend uses Axios for requests and Water CSS for baseline styling. It provides a basic file input, Shared API Key input, submit control, and analysis-result display. It does not implement drag-and-drop or authored CSS rules.
- The frontend is configured for GitHub Pages and deployed from the main branch through a GitHub Actions Pages workflow. The backend URL is supplied to the build as a public frontend configuration value; no Shared API Key is stored in source, the workflow, or the UI.
- The backend exposes only `POST /analyze`. Interactive API documentation endpoints are disabled.
- Requests use multipart form data with exactly the image field named `image`; the Shared API Key is supplied in the `X-API-Key` header.
- The Shared API Key is one six-character random secret held in the backend deployment environment. A missing or mismatched key receives HTTP 401.
- JPEG, PNG, and WebP uploads no larger than 10 MB are accepted. Unsupported, malformed, missing, or oversize uploads receive HTTP 400 before inference. Valid images are normalized to a longest edge of 1,920 pixels.
- Analysis Time starts after a valid image has been received and covers inference and result validation; it excludes client upload time. Total request timing is retained only as operational logging.
- Qwen2.5-VL-3B-Instruct is the fixed initial Inference Model. It runs directly on a Modal T4 GPU worker. This follows ADR-0001; an L4 GPU remains a fallback only if the sample-image evaluation shows T4 accuracy or latency is inadequate.
- The GPU worker permits a maximum concurrency of one and scales to zero after idle time. The model is loaded once per warm worker. A deliberate prewarm call is part of the demo runbook.
- The model must produce strict structured output containing either one Candidate Refrigerant Type or no candidate. The backend accepts Analysis Success only after parsing, normalizing, and validating one explicitly readable refrigerant designation. Ambiguous, missing, malformed, multiple, or unverified candidates are Analysis Failure.
- Normal analysis responses are HTTP 200 and use exactly one of these contracts:

  ```json
  {"status":"success","refrigerant_type":"R-410A","is_verified":true,"analysis_time_seconds":2.31}
  ```

  ```json
  {"status":"failure","message":"분석 실패","analysis_time_seconds":2.31}
  ```

- Raw model output and diagnostic failure reasons are logged server-side only. The UI never displays model reasoning; it displays a single syntactically valid Candidate Refrigerant Type even when `is_verified` is false.
- Modal dashboard logs and usage are the monitoring source. The operator records POC cost and observed Cold/Warm Analysis timing manually after the demo.
- The backend dependency set is Modal, FastAPI, python-multipart, Transformers, PyTorch, qwen-vl-utils, and Pillow. The frontend dependency set is React, React DOM, TypeScript, Vite, Axios, and Water CSS, with normal Vite TypeScript/React development tooling. No Docker tooling is used.

## Testing Decisions

- The principal and highest test seam is the public `POST /analyze` behavior. Tests assert observable request/response behavior and must not assert model implementation details, private prompts, or component internals.
- Backend contract tests cover the supported multipart request, valid and invalid Shared API Key handling, rejected upload types and sizes, normalized successful output, malformed/ambiguous/no candidate output yielding Analysis Failure, and Analysis Time on both normal result states.
- Model execution is isolated behind the analysis boundary so contract tests can use deterministic Candidate Refrigerant Type fixtures rather than downloading or running the VLM.
- Frontend tests, where present, verify the visible flow: entering a key, selecting a file, submitting the request, showing success data, showing the Korean Analysis Failure message, and showing request/input errors. They do not verify Water CSS implementation details.
- A production build of the frontend and Python import/contract checks of the backend are required before handoff.
- The five supplied Nameplate Images are exercised manually against the deployed initial model. Results, Analysis Time, worker temperature, and observed Modal usage are recorded as POC evidence; this is an acceptance evaluation rather than a mocked unit test.
- There is no existing implementation test suite to copy. New tests should retain the single public analysis seam rather than introduce lower-level model seams.

## Out of Scope

- Fine-tuning, additional training, OCR-model substitution, and automatic model selection.
- Database storage, user accounts, per-user API keys, uploaded-image retention, analytics storage, and audit history.
- Inferring a refrigerant designation from equipment model, regional convention, incomplete text, or visual context.
- Batch processing, queueing, asynchronous callbacks, multiple API endpoints, and drag-and-drop upload.
- Custom visual design, authored CSS, mobile-native applications, and Vercel deployment.
- Automatic cost enforcement or persistent monitoring dashboards beyond Modal's available dashboard telemetry and manual POC recording.
- A production SLA, high availability, or deployment to AWS EC2.

## Further Notes

- The developer will later perform the account-specific actions: creating and billing the Modal account, configuring any available spend safeguards, creating the Modal secret with the Shared API Key, choosing the GitHub Pages source, and setting the public backend URL configuration. These actions cannot be completed safely without the developer's accounts and credentials.
- Modal's free/low-cost plan and hardware pricing must be rechecked during account setup because service terms and limits can change. Use the current Modal dashboard and billing documentation as the authority.
- The demo should include a cold-start measurement and at least one prewarmed measurement. A prewarm call uses the normal endpoint and therefore requires a valid Supported Image and Shared API Key.
