"""
Email service for FutureGolf application.
Handles email verification, password reset, and notification emails.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USERNAME)
FROM_NAME = os.getenv("FROM_NAME", "FutureGolf")

# Frontend URLs
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
VERIFY_URL = f"{FRONTEND_URL}/verify-email"
RESET_URL = f"{FRONTEND_URL}/reset-password"


class EmailService:
    """Email service class for handling all email operations."""
    
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.username = SMTP_USERNAME
        self.password = SMTP_PASSWORD
        self.from_email = FROM_EMAIL
        self.from_name = FROM_NAME
    
    def _create_connection(self) -> Optional[smtplib.SMTP]:
        """Create and return SMTP connection."""
        try:
            if not self.username or not self.password:
                logger.warning("SMTP credentials not configured")
                return None
                
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            return None
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Send email with HTML and optional text content."""
        try:
            server = self._create_connection()
            if not server:
                return False
            
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            server.send_message(message)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_verification_email(self, email: str, first_name: str, verification_token: str) -> bool:
        """Send email verification email."""
        verify_link = f"{VERIFY_URL}?token={verification_token}"
        
        subject = "Verify Your FutureGolf Account"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2c5530; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #4CAF50; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0; 
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to FutureGolf!</h1>
                </div>
                <div class="content">
                    <h2>Hi {first_name or 'there'}!</h2>
                    <p>Thank you for creating your FutureGolf account. To complete your registration, please verify your email address by clicking the button below:</p>
                    
                    <a href="{verify_link}" class="button">Verify Email Address</a>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p><a href="{verify_link}">{verify_link}</a></p>
                    
                    <p>This verification link will expire in 24 hours.</p>
                    
                    <p>If you didn't create this account, you can safely ignore this email.</p>
                    
                    <p>Best regards,<br>The FutureGolf Team</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 FutureGolf. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to FutureGolf!
        
        Hi {first_name or 'there'}!
        
        Thank you for creating your FutureGolf account. To complete your registration, please verify your email address by clicking the link below:
        
        {verify_link}
        
        This verification link will expire in 24 hours.
        
        If you didn't create this account, you can safely ignore this email.
        
        Best regards,
        The FutureGolf Team
        """
        
        return self._send_email(email, subject, html_content, text_content)
    
    def send_password_reset_email(self, email: str, first_name: str, reset_token: str) -> bool:
        """Send password reset email."""
        reset_link = f"{RESET_URL}?token={reset_token}"
        
        subject = "Reset Your FutureGolf Password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2c5530; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #ff6b6b; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0; 
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Hi {first_name or 'there'}!</h2>
                    <p>We received a request to reset your password for your FutureGolf account.</p>
                    
                    <a href="{reset_link}" class="button">Reset Password</a>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p><a href="{reset_link}">{reset_link}</a></p>
                    
                    <div class="warning">
                        <strong>Important:</strong> This password reset link will expire in 1 hour for security reasons.
                    </div>
                    
                    <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                    
                    <p>Best regards,<br>The FutureGolf Team</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 FutureGolf. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Hi {first_name or 'there'}!
        
        We received a request to reset your password for your FutureGolf account.
        
        Click the link below to reset your password:
        {reset_link}
        
        Important: This password reset link will expire in 1 hour for security reasons.
        
        If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
        
        Best regards,
        The FutureGolf Team
        """
        
        return self._send_email(email, subject, html_content, text_content)
    
    def send_welcome_email(self, email: str, first_name: str) -> bool:
        """Send welcome email after successful verification."""
        subject = "Welcome to FutureGolf - Your Account is Ready!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to FutureGolf</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2c5530; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #4CAF50; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0; 
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                .features {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to FutureGolf!</h1>
                </div>
                <div class="content">
                    <h2>Hi {first_name or 'there'}!</h2>
                    <p>Your email has been successfully verified and your FutureGolf account is now ready to use!</p>
                    
                    <div class="features">
                        <h3>What you can do with FutureGolf:</h3>
                        <ul>
                            <li>Upload and analyze your golf swing videos</li>
                            <li>Get personalized coaching feedback</li>
                            <li>Track your progress over time</li>
                            <li>Access professional golf tips and techniques</li>
                        </ul>
                    </div>
                    
                    <p>Ready to improve your golf game? Start by uploading your first swing video!</p>
                    
                    <a href="{FRONTEND_URL}/dashboard" class="button">Go to Dashboard</a>
                    
                    <p>If you have any questions or need help getting started, feel free to contact our support team.</p>
                    
                    <p>Best regards,<br>The FutureGolf Team</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 FutureGolf. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to FutureGolf!
        
        Hi {first_name or 'there'}!
        
        Your email has been successfully verified and your FutureGolf account is now ready to use!
        
        What you can do with FutureGolf:
        - Upload and analyze your golf swing videos
        - Get personalized coaching feedback
        - Track your progress over time
        - Access professional golf tips and techniques
        
        Ready to improve your golf game? Start by uploading your first swing video!
        
        Visit: {FRONTEND_URL}/dashboard
        
        If you have any questions or need help getting started, feel free to contact our support team.
        
        Best regards,
        The FutureGolf Team
        """
        
        return self._send_email(email, subject, html_content, text_content)
    
    def send_password_changed_notification(self, email: str, first_name: str) -> bool:
        """Send notification after password change."""
        subject = "Your FutureGolf Password Has Been Changed"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Password Changed</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2c5530; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                .info {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Changed Successfully</h1>
                </div>
                <div class="content">
                    <h2>Hi {first_name or 'there'}!</h2>
                    
                    <div class="info">
                        <strong>Your password has been successfully changed.</strong>
                    </div>
                    
                    <p>This is a confirmation that your FutureGolf account password was changed at {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}.</p>
                    
                    <p>If you made this change, no further action is needed.</p>
                    
                    <p>If you did not make this change, please contact our support team immediately and consider changing your password again.</p>
                    
                    <p>Best regards,<br>The FutureGolf Team</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 FutureGolf. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Changed Successfully
        
        Hi {first_name or 'there'}!
        
        Your password has been successfully changed.
        
        This is a confirmation that your FutureGolf account password was changed at {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}.
        
        If you made this change, no further action is needed.
        
        If you did not make this change, please contact our support team immediately and consider changing your password again.
        
        Best regards,
        The FutureGolf Team
        """
        
        return self._send_email(email, subject, html_content, text_content)


# Create singleton instance
email_service = EmailService()