import boto3
import json
import uuid
from datetime import datetime
from botocore.exceptions import ClientError

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
            print(f"Table {self.table_name} already exists.")
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
            print(f"Table {self.table_name} created successfully.")

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
            response = table.put_item(Item=item)
            print(f"Content saved to DynamoDB with ID: {item['id']}")
            return item['id']
        
        except ClientError as e:
            print(f"DynamoDB Error: {e.response['Error']['Message']}")
            return None

def main():
    try:
        # Initialize generator
        generator = ContentGenerator()
        
        while True:
            # Get topic input
            topic = input("Enter a topic for content generation (or 'quit' to exit): ")
            
            # Exit condition
            if topic.lower() in ['quit', 'exit']:
                print("Exiting content generator.")
                break
            
            # Validate input
            if not topic.strip():
                print("Topic cannot be empty. Please try again.")
                continue
            
            # Generate full prompt
            full_prompt = (
                f"Write a comprehensive blog post about the topic: {topic}. "
                "Include key insights, current trends, and future implications."
            )
            
            # Generate content
            content = generator.generate_content(full_prompt)
            
            # Save to DynamoDB if content generated
            if content:
                print("\n--- Generated Content ---")
                print(content)
                
                # Save to DynamoDB
                dynamodb_id = generator.save_to_dynamodb(topic, content)
                
                # Optional: Save to file
                if dynamodb_id:
                    filename = f"{dynamodb_id}_content.txt"
                    with open(filename, 'w') as f:
                        f.write(content)
                    print(f"Content also saved to {filename}")
            else:
                print("Failed to generate content. Please try a different topic.")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()