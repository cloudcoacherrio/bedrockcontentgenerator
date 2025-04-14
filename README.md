# bedrockcontentgenerator
An application that generates blog content using Anthropic Claude 3.5 Sonnet.
## Prerequisites
- AWS Management Console Account
- IAM user with permissions for:
  - Amazon DynamoDB
  - AWS Lambda
  - IAM
- Python 3
- boto3 library
- AWS CLI
## 1. Local Environment Preparation
Create and prepare your local Python environment:
# Install boto3
pip install boto3
# Optional: Create virtual environment
```bash
python3 -m venv myenv
source myenv/bin/activate
```
# Authenticate into AWS via AWS CLI
Create a programmatic user with Access Keys (with permissions listed under Prerequisites)  
Authenticate via IDE stored locally  

## 2. Create DynamoDB Table
Create DynamoDB Table  
`python3 contentgenaidb.py`

## 3. Create Lambda Functions
Producer Lambda function  
`Upload contentgenerator.py`

Create Role for the Producer Lambda function  
`Attach IAM policy using contentgenpolicy.json`

Assign the execution role to the Producer Lambda function

## 4. Test Pipeline
In the Producer Lambda function, go to Test tab  
Create new test using `topictest.json`  
Run test  
Verify data in DynamoDB table  

## Configuration Notes
Replace REGION and ACCOUNT_ID in JSON policy files    
Verify DynamoDB table name: ContentGenerationLog  

## Troubleshooting
Check Lambda function logs for detailed error information  
Verify IAM role permissions  
Confirm all resource names match exactly  

## Clean Up
To avoid ongoing charges:

Delete Lambda functions    
Delete DynamoDB table  
Remove IAM roles  

## Architecture
[Test Event] → [Lambda Function] → [DynamoDB Table]  
