#!/usr/bin/env python3
import boto3
import json
import sys

def fetch_secrets():
    print("🔐 FrameRatr Secrets Manager")
    print("=" * 50)
    
    try:
        client = boto3.client('secretsmanager', region_name='us-east-2')
        print("✓ Connected to AWS Secrets Manager")
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)
    
    try:
        # Fetch application config
        print("\nFetching application config...")
        response = client.get_secret_value(SecretId='frameratr/dev/config')
        config = json.loads(response['SecretString'])
        
        # Fetch Firebase service account
        print("Fetching Firebase credentials...")
        firebase_response = client.get_secret_value(SecretId='frameratr/dev/firebase')
        firebase_config = json.loads(firebase_response['SecretString'])
        
        # Write .env file
        with open('.env', 'w') as f:
            f.write("# Auto-generated from AWS Secrets Manager\n\n")
            for key, value in config.items():
                f.write(f"{key}={value}\n")
            f.write("FIREBASE_SERVICE_ACCOUNT=firebase-service-account.json\n")
        
        print("✓ Created .env file")
        
        # Write Firebase service account JSON
        with open('firebase-service-account.json', 'w') as f:
            json.dump(firebase_config, f, indent=2)
        
        print("✓ Created firebase-service-account.json")
        print("\n✅ Success! All secrets configured!")
        print("🚀 You can now run: docker compose up --build")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fetch_secrets()