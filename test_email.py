import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys

def send_test_email(sender_email, app_password, recipient_email):
    print(f"Attempting to send test email from {sender_email} to {recipient_email}...")
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "Kora Gmail Connection Test"
        
        body = """Mingalabar Aung Chan Myint,

This is a test email sent from your personal assistant Kora (OpenClaw) using your Gmail App Password!

If you received this, it means our Gmail SMTP integration is working 100% perfectly and we can now send emails automatically as needed.

Best regards,
Kora"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # Login
        server.login(sender_email, app_password)
        
        # Send
        server.send_message(msg)
        server.quit()
        
        print("Success! Test email sent successfully.")
        return True
    except Exception as e:
        print(f"Error occurred: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python test_email.py <sender_email> <app_password> <recipient_email>")
        sys.exit(1)
        
    sender = sys.argv[1]
    pwd = sys.argv[2]
    recipient = sys.argv[3]
    
    send_test_email(sender, pwd, recipient)
