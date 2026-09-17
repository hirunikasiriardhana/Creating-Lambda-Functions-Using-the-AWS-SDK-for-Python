# Lab 7.1: Creating Lambda Functions Using the AWS SDK for Python

This repository documents the completion of **Lab 7.1** from an AWS cloud development course. The lab involves using **AWS SDK for Python (boto3)** to create AWS Lambda functions that connect a serverless café website (hosted on Amazon S3) to a DynamoDB database via Amazon API Gateway.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Lab Tasks Completed](#lab-tasks-completed)
- [Lambda Functions](#lambda-functions)
- [Issues Encountered & Fixes](#issues-encountered--fixes)
- [Testing & Verification](#testing--verification)
- [Screenshots](#screenshots)
- [Key Learnings](#key-learnings)

---

## Overview

The scenario follows **"Sofía"**, who is building a dynamic café website. Prior labs set up:
- An **Amazon S3** bucket hosting the static café website
- A **DynamoDB** table (`FoodProducts`) with a Global Secondary Index (`special_GSI`)
- A **REST API** (`ProductsApi`) in **API Gateway** with mock endpoints

This lab replaces the mock endpoints with real **Lambda functions** that read/write data from DynamoDB, making the website fully dynamic and serverless.

---

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐      ┌──────────────┐
│  S3 Website │─────▶│  API Gateway │─────▶│ Lambda Functions │─────▶│   DynamoDB   │
│ (index.html)│ HTTP │ (ProductsApi)│ Invoke│ get_all_products │ Scan │(FoodProducts)│
│             │      │              │      │  create_report   │      │ + special_GSI│
└─────────────┘      └──────────────┘      └──────────────────┘      └──────────────┘
```

**Endpoints:**
| Method | Path | Lambda Function | Purpose |
|--------|------|-----------------|---------|
| GET | `/products` | `get_all_products` | Full table scan — returns all menu items |
| GET | `/products/on_offer` | `get_all_products` | Index scan — returns only "on offer" items |
| POST | `/create_report` | `create_report` | Returns acknowledgment message (placeholder for future Cognito lab) |

**Invoke URL:** `https://mfg5sv6f03.execute-api.us-east-1.amazonaws.com/prod`

---

## Lab Tasks Completed

- [x] **Task 1** — Configured VS Code IDE, downloaded lab files, ran setup script (recreated S3 bucket, DynamoDB table, mock REST API from prior labs)
- [x] **Task 2** — Created `get_all_products` Lambda function to scan DynamoDB table/index
- [x] **Task 3** — Configured `/products` and `/products/on_offer` GET methods to invoke Lambda, enabled CORS, added mapping template, deployed API
- [x] **Task 4** — Created `create_report` Lambda function (placeholder report logic)
- [x] **Task 5** — Configured `/create_report` POST method to invoke `create_report` Lambda, deployed API
- [x] **Task 6** — Verified end-to-end integration via the live café website, including a live DynamoDB price update reflected on the site

---

## Lambda Functions

### 1. `get_all_products`
- **Runtime:** Python 3.10
- **Handler:** `get_all_products_code.lambda_handler`
- **Role:** `LambdaAccessToDynamoDB`
- **Logic:**
  - If invoked with `event['path']` present → runs `scan_index()` on the `special_GSI` index, filtering out "out of stock" items (used by `/products/on_offer`)
  - Otherwise → runs a full `scan()` on the `FoodProducts` table (used by `/products`)
  - Handles pagination via `LastEvaluatedKey`
  - Converts DynamoDB `Decimal` types to plain integers and renames fields to match the frontend's expected JSON shape (`price_in_cents_int`, `product_name_str`, etc.)

### 2. `create_report`
- **Runtime:** Python 3.10
- **Handler:** `create_report_code.lambda_handler`
- **Role:** `LambdaAccessToDynamoDB`
- **Logic:** Returns a static acknowledgment message:
  ```json
  {"msg_str": "Report processing, check your phone shortly"}
  ```
  (To be enhanced with real logic in a later Cognito authentication lab.)

---

## Issues Encountered & Fixes

This section documents every bug hit during the lab and how it was resolved — useful as a troubleshooting reference.

### 🐞 Issue 1 — `IndentationError` in wrapper script
**Symptom:**
```
File "get_all_products_wrapper.py", line 5
    ROLE = 'arn:aws:iam::...'
IndentationError: unexpected indent
```
**Cause:** An extra leading space/tab was accidentally introduced when pasting the IAM Role ARN into the `ROLE` variable.
**Fix:** Removed all leading whitespace so `ROLE = '...'` starts at column 0.

---

### 🐞 Issue 2 — `NoSuchKey` S3 error when creating Lambda function
**Symptom:**
```
InvalidParameterValueException: Error occurred while GetObject. S3 Error Code: NoSuchKey.
```
**Cause:** The Lambda deployment `.zip` package had not yet been uploaded to S3 before running `create_function`.
**Fix:**
```bash
zip get_all_products_code.zip get_all_products_code.py
aws s3 cp get_all_products_code.zip s3://<bucket-name>
python3 get_all_products_wrapper.py
```

---

### 🐞 Issue 3 — `ValidationException` on DynamoDB Scan (placeholder not replaced)
**Symptom:**
```
ValidationException: Value '<FMI_1>' at 'tableName' failed to satisfy constraint
```
**Cause:** The `<FMI_1>` (table name) and `<FMI_2>` (index name) placeholders in `get_all_products_code.py` were never replaced with actual values, **and** the deployed `.zip` still contained the old code even after edits — because the code wasn't re-zipped/re-uploaded/re-deployed to Lambda after editing.
**Fix:**
1. Replaced placeholders:
   ```python
   TABLE_NAME_STR = 'FoodProducts'
   INDEX_NAME_STR = 'special_GSI'
   ```
2. Commented out the local test line (critical — this line re-executes on **every** Lambda invocation if left active):
   ```python
   #print(lambda_handler({}, None))
   ```
3. Re-zipped, re-uploaded to S3, and updated the Lambda function code via **Update → Update from a file in Amazon S3** (using the `https://` S3 object URL format, not `s3://`).

---

### 🐞 Issue 4 — `Invalid Lambda function or Lambda function ARN`
**Symptom:** API Gateway's Integration Request page rejected the Lambda function name with a red validation error.
**Cause:** The Lambda function (`create_report`) had not actually been created yet — the wrapper script had not been run successfully at that point.
**Fix:** Verified via the Lambda **Functions** list that the function didn't exist, then re-ran the wrapper script after fixing Issue 1/2/5 for that function.

---

### 🐞 Issue 5 — Local test line not commented out (`create_report_code.py`)
**Symptom:** Same root cause as Issue 3 — the line `print(lambda_handler(None, None))` was still active and unindented.
**Fix:** Commented it out:
```python
#print(lambda_handler(None, None))
```

---

### 🐞 Issue 6 — CORS `Access-Control-Allow-Origin` set to literal string `*wildcard`
**Symptom:** Response header showed:
```
"Access-Control-Allow-Origin": "*wildcard"
```
instead of `"*"`.
**Cause:** The helper text in the "Enable CORS" form ("Use a wildcard '\*' to allow any origin...") was accidentally typed into the input field instead of just `*`.
**Fix:** Cleared the field and entered only `*`.

---

### 🐞 Issue 7 — `/products/on_offer` returning all 26 items instead of 6 "on offer" items
**Symptom:** Response returned the full table scan even when hitting the `/on_offer` endpoint.
**Cause:** API Gateway was not passing any `path` value to the Lambda function, so `event.get('path')` was always `None`, causing the function to always execute the full-table branch.
**Fix:** Added a **Mapping Template** in the Integration Request:
- Content-Type: `application/json`
- Template body:
  ```json
  {
  "path": "$context.resourcePath"
    }
  ```
  This correctly triggers the `scan_index()` branch, returning only the 6 "on offer" items.

---

### 🐞 Issue 8 — "Missing Authentication Token" error
**Symptom:**
```json
{"message":"Missing Authentication Token"}
```
**Cause:** This was **not a bug** — it appeared because the Invoke URL's root path (`/`) was accessed directly in the browser without a resource path or because a `GET` request (browser default) was sent to a `POST`-only resource (`/create_report`).
**Resolution:** Confirmed this is standard API Gateway behavior. Testing done correctly via full paths (`/prod/products`, `/prod/products/on_offer`) and via the console's built-in **Test** feature for POST methods.

---

### 🐞 Issue 9 — DynamoDB price update not reflected on the website
**Symptom:** After editing `price_in_cents` for an item directly in the DynamoDB console, the website continued to show the old price — even after a hard refresh and clearing browser cache.
**Root cause investigation:**
1. Confirmed via a direct API call (`/prod/products/on_offer`) that the **backend was correct** — the updated price (`1999`) was being returned properly by API Gateway → Lambda → DynamoDB.
2. Checked browser **Local Storage** / **Session Storage** via DevTools → Application tab — both were empty, ruling out client-side storage caching.
3. Narrowed the issue down to browser/CDN-level HTTP caching of the static site assets or the JS fetch response — being investigated further via the **Network** tab to inspect the raw API response the page's own JavaScript receives.

**Status:** 🔍 Backend fully verified working; frontend caching behavior under investigation.

---

## Testing & Verification

| Test | Result |
|------|--------|
| `get_all_products` Lambda — "Products" test event (full scan) | ✅ Returns 26 items |
| `get_all_products` Lambda — "onOffer" test event (`{"path": "on_offer"}`) | ✅ Returns 6 "on offer" items |
| `create_report` Lambda — "ReportTest" test event | ✅ Returns `{"msg_str": "Report processing, check your phone shortly"}` |
| API Gateway `GET /products` | ✅ 200 OK, 26 items, CORS header `*` present |
| API Gateway `GET /products/on_offer` | ✅ 200 OK, 6 items, CORS header `*` present |
| API Gateway `POST /create_report` | ✅ 200 OK, correct message with capital "R" |
| Café website — "on offer" view | ✅ Shows 6 items matching Lambda output |
| Café website — "view all" | ✅ Shows all 26 items |
| DynamoDB live price update reflected via API | ✅ Confirmed via direct API call |
| DynamoDB live price update reflected on website UI | 🔍 Under investigation (caching) |

---

## Screenshots

> Add your screenshots to a folder (e.g. `/screenshots`) and reference them below. Suggested set based on this lab session:

| # | Screenshot | Description |
|---|------------|--------------|
| 1 | `screenshots/01-vscode-boto3.png` | VS Code terminal confirming boto3 installation |
| 2 | `screenshots/02-dynamodb-table-details.png` | DynamoDB `FoodProducts` table & `special_GSI` index — Active |
| 3 | `screenshots/03-dynamodb-explore-items.png` | DynamoDB Explore Items — 26 menu items |
| 4 | `screenshots/04-apigateway-resources.png` | API Gateway resource tree (`/products`, `/on_offer`, `/create_report`) |
| 5 | `screenshots/05-lambda-get-all-products-code.png` | Final corrected `get_all_products_code.py` in Lambda console |
| 6 | `screenshots/06-lambda-test-products.png` | Lambda "Products" test event — 26 items |
| 7 | `screenshots/07-lambda-test-onoffer.png` | Lambda "onOffer" test event — 6 items |
| 8 | `screenshots/08-apigateway-cors-enabled.png` | "Successfully enabled CORS" confirmation |
| 9 | `screenshots/09-apigateway-products-test-200.png` | `/products` GET test — 200 OK with CORS headers |
| 10 | `screenshots/10-apigateway-onoffer-mapping-template.png` | Mapping template configuration for path passthrough |
| 11 | `screenshots/11-apigateway-onoffer-test-6items.png` | `/products/on_offer` GET test — 6 filtered items |
| 12 | `screenshots/12-lambda-create-report-test.png` | `create_report` Lambda test — succeeded |
| 13 | `screenshots/13-apigateway-createreport-test.png` | `/create_report` POST test — 200 OK |
| 14 | `screenshots/14-apigateway-deploy-success.png` | "Successfully created deployment" banner (prod stage) |
| 15 | `screenshots/15-website-view-all.png` | Café website — full menu (26 items) |
| 16 | `screenshots/16-website-on-offer.png` | Café website — "on offer" view (6 items) |
| 17 | `screenshots/17-dynamodb-price-edit.png` | DynamoDB item edit — price changed to 1999 |
| 18 | `screenshots/18-devtools-application-tab.png` | DevTools Application tab — Local/Session Storage inspection |

---

## Key Learnings

1. **Always comment out local test invocations** (`print(lambda_handler(...))`) before deploying to Lambda — an active call at module scope re-executes on every cold start/invocation and can throw errors that look like invocation failures.
2. **Editing a local `.py` file does nothing to a deployed Lambda function** until you re-zip, re-upload to S3, and explicitly update the function code (`Update from a file in Amazon S3` / `Update from a .zip file`) or redeploy via the wrapper script.
3. **API Gateway does not forward arbitrary context automatically** — if your Lambda function expects certain request metadata (like a resource path), you must explicitly pass it via a **Mapping Template** in the Integration Request.
4. **Switching an integration type from Mock to Lambda strips previously configured CORS headers** — CORS must be explicitly re-enabled per resource after changing the integration.
5. **"Missing Authentication Token"** from API Gateway usually means either an undefined path/method combination or a `POST`-only endpoint accessed via a browser `GET`, not necessarily an actual authentication problem.
6. **Client-side caching can mask a working backend.** Always verify directly against the API endpoint (bypassing the frontend) before assuming a backend fix hasn't worked.

---

## Tech Stack

- **AWS Lambda** (Python 3.10)
- **Amazon API Gateway** (REST API)
- **Amazon DynamoDB** (table + Global Secondary Index)
- **Amazon S3** (static website hosting)
- **AWS SDK for Python (boto3)**
- **VS Code (code-server)** in an AWS-hosted lab IDE

---

## License

This lab is based on AWS Training and Certification course material.
© Amazon Web Services, Inc. — used here for personal educational documentation purposes only.
