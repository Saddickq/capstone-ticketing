# Stellar Tickets | Event Registration Platform

Stellar Tickets is a modern, serverless event ticketing system built with AWS and provisioned using Terraform. 

It provides a dynamic web frontend to browse upcoming tech events, register instantly, and retrieve active booking passes.

---

## Serverless Architecture

The backend is fully serverless, scaling automatically with usage and incurring zero cost when idle:

```
[ Frontend Client ] 
       │
       ▼ (HTTP Requests)
[ API Gateway (HTTP API) ]
       │
       ├─► [ Lambda: list_events ] ──────► [ DynamoDB Table ]
       ├─► [ Lambda: register ] ─────────► [ DynamoDB Table ] (Writes registration & updates capacity)
       ├─► [ Lambda: get_registrations ] ─► [ DynamoDB Table ] (Queries GSI1 by email)
       └─► [ Lambda: cancel_registration ] ► [ DynamoDB Table ] (Deletes ticket pass)
```

- **API Gateway (HTTP API):** Handlers CORS and routes requests to corresponding Lambda triggers.
- **AWS Lambda (Python 3.x):** Independent microservices executing validation, business logic, and database operations.
- **Amazon DynamoDB:** A single-table NoSQL database storing both event metadata and user registrations.
- **Amazon S3:** Hosts the static web client (`index.html`, `app.js`, `style.css`).

---

## Database Schema (Single-Table Design)

The system stores all records in a single DynamoDB table to minimize provisioning overhead and maintain fast, single-request lookups:

### Table Indexes
- **Primary Keys:** Partition Key `PK` (string) and Sort Key `SK` (string).
- **Secondary Index:** Global Secondary Index `GSI1` (Partition Key `GSI1PK`, Sort Key `GSI1SK`) to support lookup queries by user email.

### Data Layout

| Record Type | PK (Hash) | SK (Range) | GSI1PK (Hash) | GSI1SK (Range) | Attributes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Event** | `EVENT#{id}` | `METADATA` | *None* | *None* | `name`, `date`, `location`, `capacity` |
| **Registration** | `EVENT#{id}` | `REG#{reg_id}` | `EMAIL#{email}` | `REG#{reg_id}` | `name`, `email`, `status`, `registered_at` |

---

## How to Build & Deploy

### Prerequisites
- Install [Terraform CLI](https://developer.hashicorp.com/terraform/downloads)
- Configure your AWS credentials (`aws configure`)

### Deploying Infrastructure

1. Navigate to the Terraform folder:
   ```bash
   cd terraform
   ```
2. Initialize backend plugins and modules:
   ```bash
   terraform init
   ```
3. Plan and apply the resource configuration:
   ```bash
   terraform apply
   ```
   *Note: Terraform will package the Lambda functions inside `src/lambdas` into ZIP archives, build the AWS infrastructure, and output the API base URL.*

### Frontend Distribution
Upload the frontend client files (`src/index.html`, `src/app.js`, `src/style.css`) to the S3 bucket created by Terraform.
