from fpdf import FPDF
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

load_dotenv()

def generate_invoice(order_id, customer_name, customer_email, items, total_price):
    INVOICE_DIR = "./invoice"  # Invoice folder
    os.makedirs(INVOICE_DIR, exist_ok=True)

    file_path = os.path.join(INVOICE_DIR, f"invoice_{order_id}.pdf")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)

    # Invoice header
    pdf.cell(200, 10, f"Invoice No: {order_id}", ln=True, align="C")
    pdf.ln(10)  # Spacing

    # Customer information
    pdf.set_font("Arial", "", 12)
    pdf.cell(100, 10, f"Customer: {customer_name if customer_name else 'Unknown customer'}", ln=True)
    pdf.cell(100, 10, f"Email: {customer_email}", ln=True)
    pdf.ln(10)

    # Products table
    pdf.set_font("Arial", "B", 12)
    pdf.cell(80, 10, "Product", 1, 0, "C")
    pdf.cell(30, 10, "Quantity", 1, 0, "C")
    pdf.cell(40, 10, "Unit Price", 1, 0, "C")
    pdf.cell(40, 10, "Total", 1, 1, "C")

    pdf.set_font("Arial", "", 12)
    for item in items:
        pdf.cell(80, 10, item["name"], 1, 0, "C")
        pdf.cell(30, 10, str(item["quantity"]), 1, 0, "C")
        pdf.cell(40, 10, f"{item['price']}", 1, 0, "C")
        pdf.cell(40, 10, f"{item['quantity'] * item['price']}", 1, 1, "C")

    # Total row
    pdf.set_font("Arial", "B", 12)
    pdf.cell(150, 10, "Grand Total", 1, 0, "C")
    pdf.cell(40, 10, f"{total_price}", 1, 1, "C")

    pdf.output(file_path)

   # Send the invoice by email
    try:
      send_invoice_by_email(customer_email, file_path, order_id)
    except Exception as e:
      print("Invoice email failed:", e)

    return file_path


# Function to send the invoice by email
def send_invoice_by_email(to_email, file_path, order_id):
    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = f"Your Invoice No. {order_id}"

    with open(file_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename=invoice_{order_id}.pdf"
        )
        msg.attach(part)

    try:
        # Ajout du timeout pour éviter Render timeout
        server = smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=10
        )

        server.starttls()

        server.login(
            sender_email,
            sender_password
        )

        server.sendmail(
            sender_email,
            to_email,
            msg.as_string()
        )

        server.quit()

        print(f"Invoice sent to {to_email}")

    except Exception as e:
        print(f"Email sending error: {e}")