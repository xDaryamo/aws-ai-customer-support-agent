import os
import json
import boto3
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='static')
CORS(app)

# Database Setup
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME', 'customer_inquiry_db')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Inquiry(Base):
    __tablename__ = "inquiries"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100))
    message = Column(Text)
    category = Column(String(50))
    priority = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# AWS Regions from Environment Variables
BEDROCK_REGION = os.getenv('BEDROCK_REGION', 'us-east-1')
SES_REGION = os.getenv('SES_REGION', 'eu-south-1')

# AWS Clients
bedrock = boto3.client(service_name='bedrock-runtime', region_name=BEDROCK_REGION)
ses = boto3.client(service_name='ses', region_name=SES_REGION)

def classify_message(message):
    prompt = f"Classify this message: {message}. Return ONLY JSON with keys 'category' (Sales, Support, General) and 'priority' (High, Medium, Low)."
    
    body = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        "inferenceConfig": {
            "max_new_tokens": 100,
            "temperature": 0.1
        }
    })
    
    try:
        # Using Cross-Region Inference Profile for Nova Micro
        response = bedrock.invoke_model(
            modelId='us.amazon.nova-micro-v1:0', 
            body=body
        )
        res = json.loads(response.get('body').read())
        content = res['output']['message']['content'][0]['text'].strip()
        
        if '{' in content:
            content = content[content.find('{'):content.rfind('}')+1]
        return json.loads(content)
    except Exception as e:
        print(f"Bedrock Error: {e}")
        return {"category": "General", "priority": "Medium"}

def send_notification(data):
    if data['priority'] == 'High' or data['category'] == 'Sales':
        try:
            body_text = f"Urgent Inquiry!\n\nName: {data['name']}\nMessage: {data['message']}\nCategory: {data['category']}\nPriority: {data['priority']}"
            ses.send_email(
                Source=os.getenv('SES_SENDER_EMAIL'),
                Destination={'ToAddresses': [os.getenv('SES_RECEIVER_EMAIL')]},
                Message={
                    'Subject': {'Data': f"URGENT: {data['category']} Inquiry"},
                    'Body': {'Text': {'Data': body_text}}
                }
            )
            print("Email notification sent successfully!")
        except Exception as e:
            print(f"SES Error: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/inquiry', methods=['POST'])
def handle():
    d = request.json
    c = classify_message(d['message'])
    db = SessionLocal()
    n = Inquiry(name=d['name'], email=d['email'], message=d['message'], category=c['category'], priority=c['priority'])
    db.add(n)
    db.commit()
    db.close()
    send_notification({"name": d['name'], "message": d['message'], "category": c['category'], "priority": c['priority']})
    return jsonify(c)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
