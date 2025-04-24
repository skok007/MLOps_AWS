# AWS Setup Guide for Bedrock Access

This guide provides step-by-step instructions for setting up AWS Bedrock access for the MLOps project. It covers everything from initial AWS account setup to configuring the necessary IAM resources and testing your access.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS Account Setup](#aws-account-setup)
3. [AWS CLI Configuration](#aws-cli-configuration)
4. [Setting Up Bedrock Access](#setting-up-bedrock-access)
5. [Using the Setup Scripts](#using-the-setup-scripts)
6. [Troubleshooting](#troubleshooting)
7. [Security Best Practices](#security-best-practices)
8. [Common Issues and Solutions](#common-issues-and-solutions)

## Prerequisites

Before you begin, ensure you have:

- An AWS account (or the ability to create one)
- AWS CLI installed on your machine
- `jq` command-line tool installed
- Basic understanding of AWS IAM concepts

### Installing Prerequisites

#### AWS CLI Installation

**macOS:**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Windows:**
Download and run the [AWS CLI MSI installer](https://awscli.amazonaws.com/AWSCLIV2.msi).

#### jq Installation

**macOS:**
```bash
brew install jq
```

**Linux:**
```bash
sudo apt-get install jq
```

**Windows:**
Download from [jq's official website](https://stedolan.github.io/jq/download/) or use Chocolatey:
```bash
choco install jq
```

## AWS Account Setup

1. **Create an AWS Account:**
   - Go to [AWS Sign Up](https://portal.aws.amazon.com/billing/signup)
   - Follow the registration process
   - You'll need a credit card for verification (AWS has a free tier for many services)

2. **Create an IAM User:**
   - Log into the AWS Management Console (https://console.aws.com)
   - Search for "IAM" in the top search bar
   - Click on "IAM" in the search results
   - In the left navigation pane, click on "Users"
   - Click the "Create user" button
   - Enter a name for your user (e.g., "bedrock-user")
   - Click "Next"
   - For permissions, select "Attach policies directly"
   - Search for and select "AdministratorAccess" (for initial setup - you can restrict this later)
   - Click "Next"
   - Review the details and click "Create user"
   - After creation, click on the user's name
   - Go to the "Security credentials" tab
   - Under "Access keys", click "Create access key"
   - Choose "Command Line Interface (CLI)"
   - Acknowledge the recommendations and click "Next"
   - Click "Create access key"
   - **IMPORTANT**: Save both the Access Key ID and Secret Access Key - you won't see the secret key again!

3. **Set Up Budget Alerts:**
   - Go to the AWS Billing Dashboard
   - Select "Budgets" from the left navigation
   - Click "Create budget"
   - Set a monthly budget (e.g., $30) with alerts at 80% and 100%
   - This helps prevent unexpected charges

4. **Enable Bedrock Service:**
   - Go to the AWS Bedrock console
   - Click "Get Started" or "Enable Bedrock"
   - Enable the models you plan to use (at minimum, enable Titan Text models)

## AWS CLI Configuration

1. **Configure AWS CLI with your credentials:**
   ```bash
   aws configure
   ```
   - Enter your AWS Access Key ID
   - Enter your AWS Secret Access Key
   - Enter your default region (e.g., `eu-west-2`)
   - Enter your preferred output format (e.g., `json`)

2. **Verify your configuration:**
   ```bash
   aws sts get-caller-identity
   ```
   You should see output similar to:
   ```json
   {
     "UserId": "AIDAEXAMPLEEXAMPLEEXAMPLE",
     "Account": "123456789012",
     "Arn": "arn:aws:iam::123456789012:user/YourUsername"
   }
   ```

## Setting Up Bedrock Access

There are two ways to set up Bedrock access:

1. **Using the automated script (recommended):**
   - Use the `setup-aws-bedrock.sh` script which handles all the steps automatically
   - See [Using the Setup Scripts](#using-the-setup-scripts) section for details

2. **Manual setup (for learning purposes):**
   - Create an IAM user with appropriate permissions
   - Create an IAM role with Bedrock access
   - Configure the trust relationship
   - Assume the role to get temporary credentials

## Using the Setup Scripts

### Option 1: Using the Consolidated Script

The `setup-aws-bedrock.sh` script combines all the necessary steps into a single command:

```bash
# Basic usage with defaults
./setup-aws-bedrock.sh

# Custom region and user
./setup-aws-bedrock.sh --region us-east-1 --user my-user

# Store credentials in Secrets Manager
./setup-aws-bedrock.sh --store-secret

# Skip policy creation (use existing policies)
./setup-aws-bedrock.sh --skip-policies

# Display help
./setup-aws-bedrock.sh --help
```

### Option 2: Using Individual Scripts

If you prefer to run the steps separately:

1. **Create IAM policies:**
   ```bash
   ./create-policies.sh
   ```

2. **Set up Bedrock access:**
   ```bash
   ./setup-bedrock.sh
   ```

3. **Store credentials in Secrets Manager (optional):**
   ```bash
   ./store-credentials-secret.sh
   ```

## Troubleshooting

### Common Error Messages and Solutions

1. **"Unable to locate credentials"**
   - **Solution:** Run `aws configure` to set up your credentials

2. **"AccessDeniedException"**
   - **Solution:** Check that your IAM user has the necessary permissions
   - Verify that you've assumed the correct role

3. **"Policy BedrockAccessPolicy not found"**
   - **Solution:** Run `./create-policies.sh` first to create the required policies

4. **"Failed to retrieve AWS account ID automatically"**
   - **Solution:** Set the AWS_ACCOUNT_ID environment variable manually:
     ```bash
     export AWS_ACCOUNT_ID=123456789012
     ```

5. **"Failed to list Bedrock foundation models"**
   - **Solution:** Verify that Bedrock is enabled in your AWS account
   - Check that you've enabled the specific models you're trying to access

### Debugging Steps

1. **Check AWS CLI version:**
   ```bash
   aws --version
   ```
   Ensure you're using AWS CLI v2 for Bedrock support.

2. **Verify your current identity:**
   ```bash
   aws sts get-caller-identity
   ```
   This shows which AWS identity you're currently using.

3. **Check your region:**
   ```bash
   aws configure get region
   ```
   Ensure you're using a region where Bedrock is available.

4. **List available Bedrock models:**
   ```bash
   aws bedrock list-foundation-models --region eu-west-2
   ```