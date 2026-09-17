# ☕ Creating Lambda Functions Using the AWS SDK for Python

> A serverless café ordering website — built on **DynamoDB**, **Lambda**, and **API Gateway**, hosted on **S3** — including a real bug I found and fixed along the way. 🐛➡️✅

![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20DynamoDB%20%7C%20API%20Gateway%20%7C%20S3-orange?logo=amazonaws)
![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)
![Status](https://img.shields.io/badge/status-completed-brightgreen)

---

## ☕ The Story

Meet **Frank's Café** — a small business trying to go serverless. This project plays out in three acts:

1. **The Database** — Menu items and "on offer" specials live in a DynamoDB table, queryable by a Global Secondary Index.
2. **The API** — An API Gateway REST API exposes `/products`, `/products/on_offer`, and `/create_report` — first as mock endpoints, then wired to real logic.
3. **The Brain** — Two AWS Lambda functions (in Python, via `boto3`) sit between the API and the database: one reads menu data from DynamoDB, the other handles report requests.

By the end, a static HTML/CSS/JS site on S3 talks to a fully serverless backend — no servers managed, ever.

---

## 🏗️ Architecture

```
   Browser (S3-hosted website)
          │
          │  fetch("prod/products/on_offer")
          ▼
   Amazon API Gateway  ──▶  AWS Lambda (get_all_products)
          │                         │
          │                         ▼
          │                 Amazon DynamoDB
          │                 (FoodProducts table
          │                  + special_GSI index)
          ▼
   AWS Lambda (create_report)
```

| Component | Role |
|---|---|
| **DynamoDB** (`FoodProducts` table) | Stores menu items; `special_GSI` index filters "on offer" items |
| **Lambda — `get_all_products`** | Scans the table (or the index) and returns menu JSON |
| **Lambda — `create_report`** | Returns a report-processing acknowledgment |
| **API Gateway** (`ProductsApi`) | Exposes `GET /products`, `GET /products/on_offer`, `POST /create_report`, with CORS enabled |
| **S3** | Hosts the static café website (`index.html`, `config.js`, JS/CSS assets) |

**Endpoints:**

| Method | Path | Lambda Function | Purpose |
|--------|------|-----------------|---------|
| GET | `/products` | `get_all_products` | Full table scan — returns all menu items |
| GET | `/products/on_offer` | `get_all_products` | Index scan — returns only "on offer" items |
| POST | `/create_report` | `create_report` | Returns acknowledgment message (placeholder for a future Cognito lab) |

**Invoke URL:** `https://mfg5sv6f03.execute-api.us-east-1.amazonaws.com/prod`

---

## ✅ Lab Tasks Completed

- [x] **Task 1** — Configured the VS Code IDE, downloaded lab files, ran the setup script (recreated the S3 bucket, DynamoDB table, and mock REST API from prior labs)
- [x] **Task 2** — Created the `get_all_products` Lambda function to scan the DynamoDB table/index
- [x] **Task 3** — Wired `/products` and `/products/on_offer` GET methods to Lambda, enabled CORS, added a mapping template, deployed the API
- [x] **Task 4** — Created the `create_report` Lambda function (placeholder report logic)
- [x] **Task 5** — Wired the `/create_report` POST method to Lambda, deployed the API
- [x] **Task 6** — Verified the full integration on the live café website, including tracking down and fixing a real bug where a DynamoDB price update wasn't reflected on the site (see below 👇)

---

## 🧩 Lambda Functions

### 1. `get_all_products`
- **Runtime:** Python 3.10
- **Handler:** `get_all_products_code.lambda_handler`
- **Role:** `LambdaAccessToDynamoDB`
- **Logic:**
  - If invoked with `event['path']` present → runs `scan_index()` on the `special_GSI` index, filtering out "out of stock" items (used by `/products/on_offer`)
  - Otherwise → runs a full `scan()` on the `FoodProducts` table (used by `/products`)
  - Handles pagination via `LastEvaluatedKey`
  - Converts DynamoDB `Decimal` types to plain integers and renames fields to match the frontend's expected JSON shape (`price_in_cents_int`, `product_name_str`, etc.)
<img width="1568" height="676" alt="05-lambda-code-placeholders" src="https://github.com/user-attachments/assets/4be8fbf8-b332-45ce-a074-5e7cda7ea31a" />

<img width="1568" height="647" alt="07-lambda-code-fixed-tablename-index" src="https://github.com/user-attachments/assets/432ee633-68fd-4890-8610-3287b3844d97" />

### 2. `create_report`
- **Runtime:** Python 3.10
- **Handler:** `create_report_code.lambda_handler`
- **Role:** `LambdaAccessToDynamoDB`
- **Logic:** Returns a static acknowledgment message:
  ```json
  {"msg_str": "Report processing, check your phone shortly"}
  ```
  (To be enhanced with real logic in a later Cognito authentication lab.)

<img width="1568" height="607" alt="18-createreport-test-succeeded" src="https://github.com/user-attachments/assets/5f8aa865-4fd8-4b52-b721-b3e5196b5eee" />

---

## 🔧 Building & Wiring the Lambda Functions

| Step | Screenshot |
|---|---|
| Confirming `boto3` (AWS SDK for Python) is installed in the VS Code IDE | <img width="1568" height="709" alt="01-vscode-boto3-installed" src="https://github.com/user-attachments/assets/6183be99-853d-47d4-8e63-ce5bae9c5501" />|
| DynamoDB `FoodProducts` table + `special_GSI` index — both **Active** |<img width="1568" height="643" alt="02-dynamodb-table-active" src="https://github.com/user-attachments/assets/f63b3213-ef1d-4b26-b110-524eb7af6b77" />|
| First attempt to wire API Gateway to Lambda — function not found yet | <img width="1030" height="155" alt="03-lambda-invalid-arn-error" src="https://github.com/user-attachments/assets/24a6de28-291f-4145-a1cf-ec06bc22c416" />|
| Selecting the function correctly from the ARN dropdown |<img width="1568" height="588" alt="04-lambda-arn-dropdown-selected" src="https://github.com/user-attachments/assets/2655aa8d-b212-4b10-a22d-c8829e8c8fca" />|
| Updating deployed Lambda code directly from an S3 object | <img width="998" height="681" alt="06-lambda-update-from-s3-dialog" src="https://github.com/user-attachments/assets/48047aac-a9ab-4549-b55c-e9fa6c062605" />|
| Creating the `onOffer` test event | ![Create test event 1](screenshots/08-lambda-create-test-event-onoffer-1.png) ![Create test event 2](screenshots/09-lambda-create-test-event-onoffer-2.png)|
| Enabling CORS on `/products` |<img width="1568" height="673" alt="10-apigateway-cors-enabled-products" src="https://github.com/user-attachments/assets/639c0ec8-fc58-45eb-a2e5-eda35d482505" />|
| Correcting the CORS `Access-Control-Allow-Origin` value to a plain `*` |<img width="1568" height="659" alt="11-apigateway-cors-settings-correct-wildcard" src="https://github.com/user-attachments/assets/23bbf729-ec55-485a-a2fe-f1c10c3b8242" />|
| Adding a Mapping Template so API Gateway passes `$context.resourcePath` into the Lambda event | <img width="1568" height="583" alt="12-apigateway-mapping-template" src="https://github.com/user-attachments/assets/c48f162b-4d76-41d4-b851-f58a1ae91c3b" />|
| `/products/on_offer` resource wired to Lambda |<img width="1568" height="674" alt="13-apigateway-on-offer-resource-methods" src="https://github.com/user-attachments/assets/34a79868-b5ba-4112-8b1f-912ffba71900" />|
| Deploying the API to the `prod` stage |<img width="1568" height="666" alt="14-apigateway-deploy-success-prod" src="https://github.com/user-attachments/assets/dbc14b64-7424-4f57-ab57-dc8e8a04edc2" />|
| First attempt to wire `/create_report` — function didn't exist yet | <img width="1045" height="188" alt="15-createreport-invalid-arn-error" src="https://github.com/user-attachments/assets/30513d39-5a8a-41eb-9ddc-37f34a260142" />|
| Lambda function list before `create_report` was created |<img width="1568" height="706" alt="16-lambda-functions-list-before-createreport" src="https://github.com/user-attachments/assets/1702a2b3-94a5-4610-a66c-d533b04adfd9" />|
| `create_report` test event configuration |<img width="1568" height="618" alt="17-createreport-test-event-json" src="https://github.com/user-attachments/assets/ab086e3f-9722-4c51-b2b3-618425607a71" />|
| Full menu ("view all") on the live website — 26 items |<img width="1568" height="717" alt="19-website-view-all-26-items" src="https://github.com/user-attachments/assets/f091da1c-9ece-40fb-a57d-424d2a754414" />|
| Default "on offer" view on the live website — 6 items |<img width="1568" height="713" alt="20-website-on-offer-6-items" src="https://github.com/user-attachments/assets/98a7409d-13f3-4d1b-a990-3bc5aad7a3ca" />|

---

## 🐛 The Bug Hunt: "Why isn't my price updating?"

Everything looked done — until the price on the website *refused* to update, no matter how many times DynamoDB said otherwise.

### 🔍 Symptom
In DynamoDB, the "Apple Pie Slice" item was edited and its price changed from **595** cents ($5.95) to **1999** cents ($19.99).

<img width="1568" height="675" alt="21-dynamodb-edit-item-before-price-change" src="https://github.com/user-attachments/assets/736cff2c-fb3d-4429-966b-e8b2e13de7b3" />

The website, however, kept showing **$5.95** — even after a normal refresh:

<img width="1568" height="723" alt="22-website-price-not-updated-attempt1" src="https://github.com/user-attachments/assets/2cf2734e-c12e-41ff-8c41-ed8bc1aec5a4" />

### Step 1 — Confirm DynamoDB actually saved the new price
Went back into **DynamoDB → Explore items** and confirmed the table itself was correct — `apple pie slice` now shows `1999` in the `price_in_cents` column:

<img width="1568" height="628" alt="23-dynamodb-confirms-price-updated-1999" src="https://github.com/user-attachments/assets/282e6647-aa5a-4b9d-a372-8e75d9c0da2b" />


So the data layer was fine. The problem was somewhere between DynamoDB and the browser.

### Step 2 — Rule out browser cache
Tried Incognito mode — still showed the old price:

<img width="1512" height="805" alt="24-website-incognito-still-old-price" src="https://github.com/user-attachments/assets/a3dc40c1-8039-4a8a-85f3-98f2e18cfa23" />

Then cleared all browsing data (history, cookies, cached images/files) directly in Chrome settings:

<img width="632" height="701" alt="25-chrome-delete-browsing-data-dialog" src="https://github.com/user-attachments/assets/78f3556b-af0f-461e-b968-f46b26b68fbe" />

Still no change after a hard refresh — ruling out simple HTTP/browser caching.

### Step 3 — Watch the actual network traffic
Opened Chrome DevTools → **Network** tab and reloaded the page to capture every request the site makes:

<img width="1918" height="867" alt="26-devtools-network-tab-empty" src="https://github.com/user-attachments/assets/ac0027f5-dacf-4d58-bfba-69501c557358" />

After reloading, one entry stood out in the request list: **`all_products_on_offer.json`** — a plain static `.json` file being requested via `xhr`, sitting right next to the real image assets. That file name doesn't belong to anything in this lab's architecture (the real data should only ever come from the API Gateway/Lambda endpoint):

<img width="1918" height="928" alt="27-devtools-network-mystery-json-file" src="https://github.com/user-attachments/assets/316a9343-af3b-496a-8981-a13cfe622d05" />

Inspecting that file's response revealed a **hardcoded JSON blob** frozen at the old price — proof the frontend was quietly reading from a bundled static fallback file instead of ever calling the live API.

### ✅ The Fix
Tracing this back to the frontend configuration (`config.js`, which tells the site where the live API lives) and the `update_config.py` script that publishes it to S3 resolved the mismatch. After correcting the API base URL configuration and re-publishing `config.js` to the S3 bucket, a fresh load of the site showed the correct, live price:

<img width="1918" height="868" alt="28-website-fixed-price-1999" src="https://github.com/user-attachments/assets/5097bcb9-df19-4824-867f-9810426c8b8d" />

**$19.99 — live from DynamoDB.** ✅

### 🧠 Root Cause, In One Line

> The frontend had a hardcoded local JSON fallback that looked identical to real data — so instead of failing loudly when the API wasn't reachable/configured correctly, it silently served stale numbers. Tracing actual network requests in DevTools (rather than assuming it was a caching issue) was what surfaced the real cause.

A good reminder that a "silent fallback" can be more dangerous than a hard crash — it looks like everything's working.

---

## 🛠️ Other Issues Fixed During Setup

Beyond the main bug hunt above, several smaller issues came up while building out the Lambda functions and API Gateway integrations.

| # | Issue | Cause | Fix |
|---|-------|-------|-----|
| 1 | `IndentationError` in `*_wrapper.py` | Stray leading whitespace before `ROLE = '...'` | Removed leading whitespace so the line starts at column 0 |
| 2 | `NoSuchKey` S3 error on `create_function` | The `.zip` deployment package hadn't been uploaded to S3 yet | `zip` → `aws s3 cp` → then run the wrapper script |
| 3 | `ValidationException: Value '<FMI_1>' at 'tableName'` | `<FMI_1>`/`<FMI_2>` placeholders in `get_all_products_code.py` never replaced, and edits weren't re-deployed to Lambda | Set `TABLE_NAME_STR = 'FoodProducts'` and `INDEX_NAME_STR = 'special_GSI'`; commented out the local test line; re-zipped, re-uploaded, and updated the Lambda function code from S3 |
| 4 | `Invalid Lambda function or Lambda function ARN` in API Gateway (both functions, at different points) | The target Lambda function hadn't actually been created yet | Verified via the Lambda console function list, then re-ran the wrapper script |
| 5 | Local test line left active in Lambda code | `print(lambda_handler(...))` re-executes on every invocation if left uncommented | Commented it out in both `get_all_products_code.py` and `create_report_code.py` |
| 6 | CORS header literally set to `*wildcard` | Helper placeholder text was typed into the Allow-Origin field instead of just `*` | Cleared the field and entered only `*` |
| 7 | `/products/on_offer` returning all 26 items instead of 6 | API Gateway wasn't passing a `path` value to Lambda, so `event.get('path')` was always `None` | Added a Mapping Template: `{"path": "$context.resourcePath"}` |
| 8 | `{"message":"Missing Authentication Token"}` | Not a bug — caused by hitting the API root path directly, or sending a browser `GET` to a `POST`-only resource | Tested using full resource paths and the console's built-in Test feature |

> ⚠️ **Key takeaway across issues 3 & 5:** editing a local `.py` file does nothing to a deployed Lambda function until you re-zip, re-upload to S3, and explicitly update the function code (or re-run the wrapper script). And always comment out local test invocations before deploying — an active call at module scope re-executes on every cold start.

---

## ✅ Testing & Verification

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
| DynamoDB live price update reflected via direct API call | ✅ Confirmed |
| DynamoDB live price update reflected on website UI | ✅ Confirmed after fixing frontend config |

---

## 🛠️ What This Project Covers

- ✅ Writing a Lambda function with `boto3` to scan a DynamoDB table and its GSI
- ✅ Branching logic in a single Lambda to serve both `/products` and `/products/on_offer`
- ✅ Packaging and deploying Lambda code via S3 + `boto3`
- ✅ Wiring API Gateway methods to Lambda integrations (replacing mock endpoints)
- ✅ Enabling CORS across API Gateway resources
- ✅ Using Mapping Templates to pass context (`$context.resourcePath`) into Lambda events
- ✅ Debugging a full-stack data flow from DynamoDB → Lambda → API Gateway → S3-hosted frontend using Chrome DevTools (Network, Application tabs)
- ✅ Diagnosing a silent frontend fallback vs. a genuine backend failure

---

## 📁 Project Structure

```
.
├── README.md
├── screenshots/                        # All screenshots referenced in this README
├── python_3/
│   ├── get_all_products_code.py        # Lambda: reads menu data from DynamoDB
│   ├── get_all_products_wrapper.py     # Creates the Lambda function via boto3
│   ├── create_report_code.py           # Lambda: report acknowledgment
│   ├── create_report_wrapper.py        # Creates the Lambda function via boto3
│   └── update_config.py                # Pushes config.js to S3
└── resources/
    ├── setup.sh                        # Recreates S3/DynamoDB/API Gateway from prior labs
    └── website/
        ├── index.html
        ├── config.js                   # Frontend ↔ API Gateway link
        ├── scripts/
        └── styles/
```

---

## 🎓 Course Context

This lab is part of an AWS hands-on training series on building serverless applications with Lambda, API Gateway, DynamoDB, and S3.

## License

This lab is based on AWS Training and Certification course material.
© Amazon Web Services, Inc. — used here for personal educational documentation purposes only.

---

<p align="center"><i>Built one debugging step at a time — because "it works on my DynamoDB" isn't the same as "it works on the website." ☕</i></p>
