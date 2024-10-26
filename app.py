from fpdf import FPDF
import pymongo
import matplotlib.pyplot as plt
import numpy as np
import cv2
import smtplib
import pyttsx3
import concurrent.futures
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from time import sleep
from flask import Flask, render_template, request
from tensorflow.keras.models import load_model

# Load the trained model
new_model = load_model('trained_model.h5')
app = Flask(__name__)

predictions = ["Mild", "Moderate", "No Diabetic Retinopathy", "Proliferate", "Severe"]

# Function to send email with PDF attachment
def send_email(receiver_email, pdf_path):
    sender_email = "samikshakadam0403@gmail.com"
    password = "vveluosuzdqhnpls"  # Use environment variable for security

    # Create email
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = 'Eye Check-Up Report'
    
    body = 'Hello,\n\nPlease find attached your eye check-up report.\n\nBest regards,\n iHelp'
    message.attach(MIMEText(body, 'plain'))

    # Attach PDF
    with open(pdf_path, 'rb') as binary_pdf:
        payload = MIMEBase('application', 'octet-stream')
        payload.set_payload(binary_pdf.read())
        encoders.encode_base64(payload)
        payload.add_header('Content-Disposition', f'attachment; filename={pdf_path}')
        message.attach(payload)

    # Send email
    with smtplib.SMTP('smtp.gmail.com', 587) as session:
        session.starttls()
        session.login(sender_email, password)
        session.sendmail(sender_email, receiver_email, message.as_string())
    print('Email Sent')

def predict_new(path, name, emailId, username, contact):
    img = cv2.imread(path)
    RGBImg = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    RGBImg = cv2.resize(RGBImg, (224, 224))
    plt.imshow(RGBImg)
    image = np.array(RGBImg) / 255.0
    predict = new_model.predict(np.array([image]))
    pred = np.argmax(predict, axis=1)
    diagnosis = predictions[pred[0]]
    print(f"\n\n\nPredicted: {diagnosis}\n\n\n")

    # Generate report content
    report_content = f"""
    DIABETIC RETINOPATHY report by i-Help

    Patient name: {name}
    Age: {username}
    Email id: {emailId}
    Contact no: {contact}

    Diagnosis:
    1. Retina scan shows signs of {diagnosis} DR.

    Further advice for treatment: 
    1. Patient is advised to keep sugar levels in check.
    2. Exercise regularly and monitor vision changes.

    Thank you for visiting us for your eye check-up.
    """

    # Create PDF report
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.multi_cell(0, 10, report_content)
    pdf_path = 'report.pdf'
    pdf.output(pdf_path)

    # Insert into database (if needed)
    databaseInsert(name, emailId, username, contact, diagnosis)

    # Send email with the report
    send_email(emailId, pdf_path)

@app.route('/', methods=['GET'])
def hello_world():
    return render_template('index.html')

    
@app.route("/help")
def help():
    return render_template('help.html')

@app.route('/', methods=['POST'])
def predict():
    name = request.form['name']
    emailId = request.form['emailId']
    contact = request.form['contact']
    username = request.form['username']

    imagefile = request.files['imagefile']
    image_path = "images/" + imagefile.filename
    imagefile.save(image_path)
    predict_new(image_path, name, emailId, username, contact)
    return render_template('index.html')

def databaseInsert(name, emailId, username, contact, diagnosis):
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client['iHelp']
    collection = db['iHelp']
    record = {"Name": name, "Email-ID": emailId, "Username": username, "Contact": contact, "Prediction": diagnosis}
    collection.insert_one(record)

if __name__ == '_main_':
    app.run(port=3000, debug=True)