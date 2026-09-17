# ☕ Creating Lambda Functions Using the AWS SDK for Python

> A serverless café ordering website — built on **DynamoDB**, **Lambda**, and **API Gateway**, hosted on **S3** — including a real production-style bug I found and fixed along the way. 🐛➡️✅

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

**What each piece does:**

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

## 🐛 The Bug Hunt: "Why isn't my price updating?"

Everything looked done — until the price on the website *refused* to update, no matter how many times DynamoDB said otherwise. Here's how it was tracked down, live, one clue at a time.

### 🔍 Symptom
DynamoDB showed the "Apple Pie Slice" price updated to **1999** cents ($19.99). The website still showed **$5.95** — even in Incognito mode, even after clearing the browser cache.

### Step 1 — Rule out the backend
Called the API Gateway endpoint directly in the browser:
```
https://mfg5sv6f03.execute-api.us-east-1.amazonaws.com/prod/products/on_offer
```
The raw JSON response came back with `"price_in_cents_int": 1999` — **confirmed correct**. DynamoDB → Lambda → API Gateway chain was healthy. The bug had to be somewhere between the API and the browser.

### Step 2 — Rule out browser storage
Opened DevTools → **Application** tab → checked Local Storage and Session Storage.

![Empty local/session storage](screenshots/01-devtools-application-empty-storage.png)

Both empty. Not a client-side storage issue.

### Step 3 — Watch the actual network traffic
Opened the **Network** tab and reloaded the page to capture every request the site makes:

![Full list of network requests](screenshots/02-network-requests-list.png)

One entry stood out: **`all_products_on_offer.json`** — a plain static file being requested via `xhr`, sitting right next to the real API calls. That name doesn't belong to anything in the lab's architecture.

### Step 4 — Inspect the mystery file
![Selecting the request in the Network panel](screenshots/03-network-tab-request-selected.png)

Opening its **Response** tab revealed the smoking gun: a hardcoded JSON blob, permanently frozen at **`"price_in_cents_int": 595`**, with slightly different descriptions than the real API — proof the frontend was reading from a *stale local fallback file*, never touching the live API at all.

### Step 5 — Find out *why* the frontend was using the fallback file
Checked `config.js` — the file responsible for telling the frontend where the live API lives:

```js
window.COFFEE_CONFIG = {
	API_GW_BASE_URL_STR: null,
	COGNITO_LOGIN_BASE_URL_STR: null
};
```

![config.js showing API_GW_BASE_URL_STR as null](screenshots/04-config-null-bug.png)

**Found it.** `API_GW_BASE_URL_STR` was `null`, so the site had nothing to call — it silently fell back to the bundled static JSON instead of ever reaching API Gateway.

### Step 6 — Trace *why* config.js was never updated
Dug one level deeper into `update_config.py` — the script meant to push the real API URL up to S3:

```python
bucket_name = "<FMI_1>"   # 🚩 never replaced!
```

The placeholder had never been swapped for the real bucket name, so every previous run of the script had been silently failing to upload the corrected `config.js`.

### ✅ The Fix

1. Filled in the real API Gateway invoke URL in `config.js`.
2. Replaced `<FMI_1>` in `update_config.py` with the actual S3 bucket name.
3. Re-ran `python3 update_config.py` → `DONE`.
4. Hard-refreshed the site.

![Apple Pie Slice now showing $19.99 from the live API](screenshots/05-fixed-price-1999.png)

**$19.99, live from DynamoDB.** Description text matched the API exactly. Root cause fully resolved.

### 🧠 Root Cause, In One Line

> A leftover placeholder (`<FMI_1>`) in a config-upload script meant the site's API endpoint was never actually configured — so the frontend quietly served stale hardcoded data instead of failing loudly.

A good reminder that a "silent fallback" can be more dangerous than a hard crash — it looks like everything's working.

---

## 🛠️ Other Issues Fixed During Setup

Beyond the main bug hunt above, several smaller issues came up while building out the Lambda functions and API Gateway integrations. Documented here as a troubleshooting reference.

| # | Issue | Cause | Fix |
|---|-------|-------|-----|
| 1 | `IndentationError` in `*_wrapper.py` | Stray leading whitespace before `ROLE = '...'` | Removed leading whitespace so the line starts at column 0 |
| 2 | `NoSuchKey` S3 error on `create_function` | The `.zip` deployment package hadn't been uploaded to S3 yet | `zip` → `aws s3 cp` → then run the wrapper script |
| 3 | `ValidationException: Value '<FMI_1>' at 'tableName'` | `<FMI_1>`/`<FMI_2>` placeholders in `get_all_products_code.py` never replaced, and edits weren't re-deployed to Lambda | Set `TABLE_NAME_STR = 'FoodProducts'` and `INDEX_NAME_STR = 'special_GSI'`; commented out the local test line; re-zipped, re-uploaded, and updated the Lambda function code |
| 4 | `Invalid Lambda function or Lambda function ARN` in API Gateway | The `create_report` Lambda function hadn't actually been created yet | Verified via the Lambda console function list, then re-ran the wrapper script |
| 5 | Local test line left active in `create_report_code.py` | `print(lambda_handler(None, None))` re-executes on every invocation if left uncommented | Commented it out |
| 6 | CORS header literally set to `*wildcard` | Helper placeholder text was typed into the Allow-Origin field instead of just `*` | Cleared the field and entered only `*` |
| 7 | `/products/on_offer` returning all 26 items instead of 6 | API Gateway wasn't passing a `path` value to Lambda, so `event.get('path')` was always `None` | Added a Mapping Template: `{"path": "$context.resourcePath"}` |
| 8 | `{"message":"Missing Authentication Token"}` | Not a bug — caused by hitting the API root path directly, or sending a browser `GET` to a `POST`-only resource | Tested using full resource paths and the console's built-in Test feature |

> ⚠️ **Key takeaway across issues 3 & 5:** editing a local `.py` file does nothing to a deployed Lambda function until you re-zip, re-upload to S3, and explicitly update the function code (or re-run the wrapper script). And always comment out local test invocations (`print(lambda_handler(...))`) before deploying — an active call at module scope re-executes on every cold start.

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
| DynamoDB live price update reflected on website UI | ✅ Confirmed after fixing `config.js` / `update_config.py` |

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
├── python_3/
│   ├── get_all_products_code.py       # Lambda: reads menu data from DynamoDB
│   ├── get_all_products_wrapper.py    # Creates the Lambda function via boto3
│   ├── create_report_code.py          # Lambda: report acknowledgment
│   ├── create_report_wrapper.py       # Creates the Lambda function via boto3
│   └── update_config.py               # Pushes config.js to S3
└── resources/
    ├── setup.sh                       # Recreates S3/DynamoDB/API Gateway from prior labs
    └── website/
        ├── index.html
        ├── config.js                  # Frontend ↔ API Gateway link
        ├── scripts/
        └── styles/
```

---

## 📸 Screenshots

| # | Screenshot | Description |
|---|------------|--------------|
| 1 | `screenshots/00-vscode-boto3-installed.png` | VS Code terminal confirming boto3 installation |
| 2 | `screenshots/00-dynamodb-table-details.png` | DynamoDB `FoodProducts` table & `special_GSI` index — Active |
| 3 | `screenshots/00-dynamodb-explore-items.png` | DynamoDB Explore Items — 26 menu items |
| 4 | `screenshots/00-apigateway-resources.png` | API Gateway resource tree (`/products`, `/on_offer`, `/create_report`) |
| 5 | `screenshots/00-lambda-test-products.png` | Lambda "Products" test event — 26 items |
| 6 | `screenshots/00-lambda-test-onoffer.png` | Lambda "onOffer" test event — 6 items |
| 7 | `screenshots/00-apigateway-cors-enabled.png` | "Successfully enabled CORS" confirmation |
| 8 | `screenshots/00-apigateway-onoffer-mapping-template.png` | Mapping template configuration for path passthrough |
| 9 | `screenshots/00-lambda-create-report-test.png` | `create_report` Lambda test — succeeded |
| 10 | `screenshots/00-apigateway-deploy-success.png` | "Successfully created deployment" banner (prod stage) |
| 11 | `screenshots/01-devtools-application-empty-storage.png` | DevTools Application tab — Local/Session Storage confirmed empty |
| 12 | `screenshots/02-network-requests-list.png` | Network tab showing the suspicious `all_products_on_offer.json` request |
| 13 | `screenshots/03-network-tab-request-selected.png` | Inspecting the mystery request in the Network panel |
| 14 | `screenshots/04-config-null-bug.png` | `config.js` showing `API_GW_BASE_URL_STR: null` |
| 15 | `screenshots/05-fixed-price-1999.png` | Website showing the corrected $19.99 price, live from DynamoDB |

---

## 🎓 Course Context

This lab is part of an AWS hands-on training series on building serverless applications with Lambda, API Gateway, DynamoDB, and S3.

## License

This lab is based on AWS Training and Certification course material.
© Amazon Web Services, Inc. — used here for personal educational documentation purposes only.

---

<p align="center"><i>Built one debugging step at a time — because "it works on my DynamoDB" isn't the same as "it works on the website." ☕</i></p>
