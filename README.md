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

  ![Lambda code before fix — placeholders still present](screenshots/05-lambda-code-placeholders.png)
  ![Lambda code after fix — real table/index names set](screenshots/07-lambda-code-fixed-tablename-index.png)

### 2. `create_report`
- **Runtime:** Python 3.10
- **Handler:** `create_report_code.lambda_handler`
- **Role:** `LambdaAccessToDynamoDB`
- **Logic:** Returns a static acknowledgment message:
  ```json
  {"msg_str": "Report processing, check your phone shortly"}
  ```
  (To be enhanced with real logic in a later Cognito authentication lab.)

  ![create_report test succeeded](screenshots/18-createreport-test-succeeded.png)

---

## 🔧 Building & Wiring the Lambda Functions

| Step | Screenshot |
|---|---|
| Confirming `boto3` (AWS SDK for Python) is installed in the VS Code IDE | ![boto3 installed](screenshots/01-vscode-boto3-installed.png) |
| DynamoDB `FoodProducts` table + `special_GSI` index — both **Active** | ![DynamoDB table active](screenshots/02-dynamodb-table-active.png) |
| First attempt to wire API Gateway to Lambda — function not found yet | ![Invalid ARN error](screenshots/03-lambda-invalid-arn-error.png) |
| Selecting the function correctly from the ARN dropdown | ![ARN dropdown selected](screenshots/04-lambda-arn-dropdown-selected.png) |
| Updating deployed Lambda code directly from an S3 object | ![Update from S3 dialog](screenshots/06-lambda-update-from-s3-dialog.png) |
| Creating the `onOffer` test event | ![Create test event 1](screenshots/08-lambda-create-test-event-onoffer-1.png) ![Create test event 2](screenshots/09-lambda-create-test-event-onoffer-2.png) |
| Enabling CORS on `/products` | ![CORS enabled](screenshots/10-apigateway-cors-enabled-products.png) |
| Correcting the CORS `Access-Control-Allow-Origin` value to a plain `*` | ![CORS wildcard fixed](screenshots/11-apigateway-cors-settings-correct-wildcard.png) |
| Adding a Mapping Template so API Gateway passes `$context.resourcePath` into the Lambda event | ![Mapping template](screenshots/12-apigateway-mapping-template.png) |
| `/products/on_offer` resource wired to Lambda | ![on_offer methods](screenshots/13-apigateway-on-offer-resource-methods.png) |
| Deploying the API to the `prod` stage | ![Deploy success](screenshots/14-apigateway-deploy-success-prod.png) |
| First attempt to wire `/create_report` — function didn't exist yet | ![create_report invalid ARN](screenshots/15-createreport-invalid-arn-error.png) |
| Lambda function list before `create_report` was created | ![Functions list](screenshots/16-lambda-functions-list-before-createreport.png) |
| `create_report` test event configuration | ![Test event JSON](screenshots/17-createreport-test-event-json.png) |
| Full menu ("view all") on the live website — 26 items | ![View all](screenshots/19-website-view-all-26-items.png) |
| Default "on offer" view on the live website — 6 items | ![On offer](screenshots/20-website-on-offer-6-items.png) |

---

## 🐛 The Bug Hunt: "Why isn't my price updating?"

Everything looked done — until the price on the website *refused* to update, no matter how many times DynamoDB said otherwise.

### 🔍 Symptom
In DynamoDB, the "Apple Pie Slice" item was edited and its price changed from **595** cents ($5.95) to **1999** cents ($19.99).

![DynamoDB edit item — before the price change](screenshots/21-dynamodb-edit-item-before-price-change.png)

The website, however, kept showing **$5.95** — even after a normal refresh:

![Website still showing $5.95](screenshots/22-website-price-not-updated-attempt1.png)

### Step 1 — Confirm DynamoDB actually saved the new price
Went back into **DynamoDB → Explore items** and confirmed the table itself was correct — `apple pie slice` now shows `1999` in the `price_in_cents` column:

![DynamoDB confirms price is 1999](screenshots/23-dynamodb-confirms-price-updated-1999.png)

So the data layer was fine. The problem was somewhere between DynamoDB and the browser.

### Step 2 — Rule out browser cache
Tried Incognito mode — still showed the old price:

![Website in Incognito still shows old price](screenshots/24-website-incognito-still-old-price.png)

Then cleared all browsing data (history, cookies, cached images/files) directly in Chrome settings:

![Chrome Delete Browsing Data dialog](screenshots/25-chrome-delete-browsing-data-dialog.png)

Still no change after a hard refresh — ruling out simple HTTP/browser caching.

### Step 3 — Watch the actual network traffic
Opened Chrome DevTools → **Network** tab and reloaded the page to capture every request the site makes:

![Network tab before reload](screenshots/26-devtools-network-tab-empty.png)

After reloading, one entry stood out in the request list: **`all_products_on_offer.json`** — a plain static `.json` file being requested via `xhr`, sitting right next to the real image assets. That file name doesn't belong to anything in this lab's architecture (the real data should only ever come from the API Gateway/Lambda endpoint):

![Network requests list showing the suspicious all_products_on_offer.json request](screenshots/27-devtools-network-mystery-json-file.png)

Inspecting that file's response revealed a **hardcoded JSON blob** frozen at the old price — proof the frontend was quietly reading from a bundled static fallback file instead of ever calling the live API.

### ✅ The Fix
Tracing this back to the frontend configuration (`config.js`, which tells the site where the live API lives) and the `update_config.py` script that publishes it to S3 resolved the mismatch. After correcting the API base URL configuration and re-publishing `config.js` to the S3 bucket, a fresh load of the site showed the correct, live price:

![Website showing the corrected $19.99 price, live from DynamoDB](screenshots/28-website-fixed-price-1999.png)

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
