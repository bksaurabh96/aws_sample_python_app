## aws_sample_python_app

This repository contains a **simplified cloud-based application deployment pipeline** using:

- **Python FastAPI** for a small REST API
- **Docker** for containerization
- **AWS CDK (Python)** to define infrastructure (ECS Fargate + ALB)
- **GitHub Actions** for CI/CD (build, test, and deploy)

The goal is to demonstrate **market-standard practices** for a minimal, production-like pipeline while remaining suitable for the AWS Free Tier.

---

### Application Overview

- **Framework**: FastAPI
- **Endpoints**:
  - `GET /` – Simple welcome message (no auth)
  - `GET /health` – Health check (requires auth)
  - `GET /items` – Returns dummy data (requires auth)
- **Authentication**:
  - HTTP `Authorization` header with **Bearer token**
  - Example: `Authorization: Bearer <token>`
  - The expected token is provided via the `API_TOKEN` environment variable (in AWS, passed from CDK context; locally, you set it yourself).
  - **Reference token** (for local/testing): `API_TOKEN=token005`.

The application code lives in `app/main.py`.

---

### Local Development

#### 1. Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
```

#### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Set the API token

```bash
export API_TOKEN="token005"
```

(Use `token005` as the reference token for local development and testing; see Application Overview above.)

#### 4. Run tests

```bash
pytest
```

#### 5. Run the API locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Example authenticated request:

```bash
curl -H "Authorization: Bearer token005" http://localhost:8000/health
curl -H "Authorization: Bearer token005" http://localhost:8000/items
```

---

### Dockerization

The app is packaged into a Docker image using the `Dockerfile` in the repository root.

#### Build the image

```bash
docker build -t aws-sample-python-app .
```

#### Run the container locally

```bash
docker run -e API_TOKEN=token005 -p 8000:8000 aws-sample-python-app
```

Then call:

```bash
curl -H "Authorization: Bearer token005" http://localhost:8000/health
curl -H "Authorization: Bearer token005" http://localhost:8000/items
```

---

### Infrastructure with AWS CDK

The infrastructure is defined in **Python CDK** under the `infra/` folder.

- **Stack**: `AwsSamplePythonAppStack`
- **Components**:
  - New VPC (`ec2.Vpc`)
  - ECS Cluster (`ecs.Cluster`)
  - Fargate Service (`ecs_patterns.ApplicationLoadBalancedFargateService`)
    - Builds a Docker image from the repository (`ecs.ContainerImage.from_asset("..")`)
    - Exposes port `8000` behind an **Application Load Balancer**
    - Sets the `API_TOKEN` environment variable used by the FastAPI app

#### CDK Prerequisites

- AWS account with appropriate permissions (ideally an IAM user limited for CI/CD)
- AWS CLI configured locally if you deploy from your machine
- Node.js and `aws-cdk` CLI installed
- Python 3.10+ with virtual environment support

#### Install CDK dependencies

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r infra/requirements.txt
```

#### Test the infrastructure

Validate that the CDK app and stack synthesize (no AWS credentials needed):

```bash
cd infra
cdk synth
```

This runs the CDK app, builds the Docker image for the container asset, and prints the synthesized CloudFormation template. **Docker must be running** and the **CDK CLI** must be installed (`npm install -g aws-cdk`).

To run the automated infra test (from project root):

```bash
pytest infra/tests/ -v
```

This runs `cdk synth` from `infra/` and checks it succeeds. Requires Docker and the CDK CLI on your `PATH`.

#### Bootstrap the environment

```bash
cd infra
cdk bootstrap
```

#### Deploy the stack

You can (and should) provide a strong API token via CDK context:

```bash
cd infra
cdk deploy AwsSamplePythonAppStack --require-approval never -c apiToken=your-strong-token
```

On success, CDK will output the **Load Balancer DNS name**, for example:

```text
LoadBalancerDNS = my-app-alb-1234567890.us-east-1.elb.amazonaws.com
```

You can then call the API:

```bash
API_URL="http://my-app-alb-1234567890.us-east-1.elb.amazonaws.com"
TOKEN="your-strong-token"

curl -H "Authorization: Bearer $TOKEN" "$API_URL/health"
curl -H "Authorization: Bearer $TOKEN" "$API_URL/items"
```

> **Note**: When no `apiToken` context is supplied, the stack uses a placeholder `changeme-token`. This is not recommended for real environments.

---

### CI/CD with GitHub Actions

The pipeline is defined in `.github/workflows/cicd.yml`.

On every push or pull request to `main`/`master`, it:

1. **Checks out** the repository
2. **Sets up Python**
3. **Installs dependencies**
4. **Runs tests** (`pytest`)
5. **Installs CDK CLI** and CDK Python dependencies
6. **Configures AWS credentials** using **AWS access keys from secrets**
7. **Bootstraps** the CDK environment (if not already)
8. **Deploys** the `AwsSamplePythonAppStack` with an API token from secrets

#### Required GitHub Secrets

In your GitHub repository settings, configure these secrets:

- `AWS_ACCESS_KEY_ID` – AWS access key ID for an IAM user with permissions for CDK deploy (CloudFormation, ECS, ECR, IAM, etc.)
- `AWS_SECRET_ACCESS_KEY` – AWS secret access key corresponding to the access key ID
- `AWS_REGION` – e.g. `us-east-1`
- `API_TOKEN` – the Bearer token clients must use (e.g. `token005` for reference; passed as CDK context and injected as `API_TOKEN` into the container)

Once set, any push to the main branch will automatically:

- Run tests
- Build the Docker image as part of the CDK deployment
- Update the ECS Fargate service behind the ALB

#### Using AWS Access Keys with GitHub Actions

This project uses **AWS access keys** for authentication:

- Create an **IAM user** in AWS with:
  - An IAM policy granting the permissions required for CDK deploy (CloudFormation, ECS, ECR, IAM, etc.).
- In GitHub Actions, `aws-actions/configure-aws-credentials@v4` uses the access key ID and secret access key from secrets to authenticate.

High‑level IAM setup steps:

1. In AWS, create an IAM user for GitHub Actions.
2. Attach a policy allowing CDK operations (CloudFormation, ECS, ECR, IAM where needed).
3. Generate access keys for the user.
4. Copy the access key ID and secret access key into the GitHub secrets `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.

---

### Security and Best Practices (Simplified)

- **Authentication**:
  - Uses a Bearer token in the `Authorization` header.
  - The token is configured via:
    - Local env var `API_TOKEN` for development/tests.
    - CDK context + task environment for AWS.
- **Secrets management**:
  - For a real-world production system, you would typically store the token in:
    - AWS Secrets Manager, or
    - AWS Systems Manager Parameter Store (SSM)
  - This example keeps it simple using CDK context and environment variables, which is suitable for demos and learning.
- **Least privilege**:
  - The IAM user used by GitHub Actions for deployment should be limited to the resources required by CDK (CloudFormation, ECR, ECS, IAM, etc.), rather than using full admin.

---

### Project Structure

```text
app/
  main.py              # FastAPI application with authenticated endpoints
tests/
  test_main.py         # Pytest tests for the API
infra/
  app.py               # CDK app entrypoint
  aws_sample_python_app_stack.py  # CDK stack (VPC, ECS Fargate, ALB)
  cdk.json             # CDK configuration
  requirements.txt     # CDK Python dependencies
.github/
  workflows/
    cicd.yml           # GitHub Actions CI/CD pipeline
Dockerfile             # Docker image definition for the API
requirements.txt       # Application Python dependencies
README.md              # This documentation
```

---

### Extending This Example

Possible next steps:

- Integrate **AWS Secrets Manager** for API token and other secrets.
- Add **logging, metrics, and tracing** (e.g., CloudWatch, OpenTelemetry).
- Add **more endpoints** and **database integration** (e.g., RDS or DynamoDB).
- Introduce **staging/production environments** via separate CDK stacks.
