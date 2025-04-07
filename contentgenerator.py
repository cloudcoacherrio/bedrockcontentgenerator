import json
import boto3
import uuid
from datetime import datetime
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    # Initialize generator
    generator = ContentGenerator()
    
    # Extract topic from event
    topic = event.get('topic', '')
    
    if not topic:
        return {
            'statusCode': 400,
            'body': json.dumps('No topic provided')
        }
    
    # Generate full prompt
    full_prompt = (
        f"Write a comprehensive blog post about the topic: {topic}. "
        "Include key insights, current trends, and future implications."
    )
    
    # Generate content
    content = generator.generate_content(full_prompt)
    
    # Save to DynamoDB
    if content:
        dynamodb_id = generator.save_to_dynamodb(topic, content)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'topic': topic,
                'content': content,
                'dynamodb_id': dynamodb_id
            })
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to generate content')
        }

class ContentGenerator:
    def __init__(self, region='us-west-2'):
        # AWS Clients
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # DynamoDB Table Name
        self.table_name = 'ContentGenerationLog'
        
        # Ensure table exists
        self.create_table_if_not_exists()

    def create_table_if_not_exists(self):
        try:
            # Check if table exists
            self.dynamodb.meta.client.describe_table(TableName=self.table_name)
        except self.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            # Create table if not exists
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            # Wait for table to be created
            table.meta.client.get_waiter('table_exists').wait(TableName=self.table_name)

    def generate_content(self, prompt, max_tokens=300):
        try:
            # Formatted input for Claude model
            formatted_prompt = f"Human: {prompt}\n\nAssistant:"
            
            response = self.bedrock_runtime.invoke_model(
                modelId='anthropic.claude-v2',
                body=json.dumps({
                    "prompt": formatted_prompt,
                    "max_tokens_to_sample": max_tokens,
                    "temperature": 0.7,
                    "stop_sequences": ["\n\nHuman:"]
                })
            )
            
            # Parse response
            generated_text = json.loads(response['body'].read())['completion'].strip()
            return generated_text
        
        except Exception as e:
            print(f"Content Generation Error: {e}")
            return None

    def save_to_dynamodb(self, topic, content):
        try:
            # Get DynamoDB table
            table = self.dynamodb.Table(self.table_name)
            
            # Prepare item to store
            item = {
                'id': str(uuid.uuid4()),  # Unique identifier
                'topic': topic,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'content_length': len(content)
            }
            
            # Put item in DynamoDB
            table.put_item(Item=item)
            return item['id']
        
        except ClientError as e:
            print(f"DynamoDB Error: {e.response['Error']['Message']}")
            return None