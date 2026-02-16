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

# AWS Clients
bedrock = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
ses = boto3.client(service_name='ses', region_name='us-east-1')

def classify_message(message):
    prompt = f"""
    Human: Classify the following customer message into one of these categories: Sales, Support, General. 
    Also assign a priority: High, Medium, Low.
    Return only a JSON object with keys 'category' and 'priority'.
    
    Message: {message}
    
    Assistant:"""
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    })
    
    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-haiku-4-5-20251001-v1:0',
            body=body
        )
        response_body = json.loads(response.get('body').read())
        content = response_body['content'][0]['text']
        return json.loads(content)
    except Exception as e:
        print(f"Error calling Bedrock: {e}")
        return {"category": "General", "priority": "Medium"}

def send_notification(inquiry_data):
    if inquiry_data['priority'] == 'High' or inquiry_data['category'] == 'Sales':
        try:
            email_body = (
                f"New urgent inquiry!\n\n"
                f"Name: {inquiry_data['name']}\n"
                f"Email: {inquiry_data['email']}\n"
                f"Message: {inquiry_data['message']}\n"
                f"Priority: {inquiry_data['priority']}"
            )
            ses.send_email(
                Source=os.getenv('SES_SENDER_EMAIL'),
                Destination={'ToAddresses': [os.getenv('SES_RECEIVER_EMAIL')]},
                Message={
                    'Subject': {'Data': f"URGENT: {inquiry_data['category']} Inquiry from {inquiry_data['name']}"},
                    'Body': {
                        'Text': {'Data': email_body}
                    }
                }
            )
        except Exception as e:
            print(f"Error sending SES email: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/inquiry', methods=['POST'])
def handle_inquiry():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')
    
    # 1. AI Classification
    classification = classify_message(message)
    
    # 2. Save to Database
    db = SessionLocal()
    new_inquiry = Inquiry(
        name=name,
        email=email,
        message=message,
        category=classification['category'],
        priority=classification['priority']
    )
    db.add(new_inquiry)
    db.commit()
    db.refresh(new_inquiry)
    db.close()
    
    # 3. Send Notification if urgent
    send_notification({
        "name": name,
        "email": email,
        "message": message,
        "category": classification['category'],
        "priority": classification['priority']
    })
    
    return jsonify({
        "status": "success",
        "category": classification['category'],
        "priority": classification['priority']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
