from fpdf import FPDF
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


def generate_invoice(order_id, customer_name, customer_email, items, total_price):
    INVOICE_DIR = "./invoice"  # Dossier des factures
    os.makedirs(INVOICE_DIR, exist_ok=True)

    file_path = os.path.join(INVOICE_DIR, f"invoice_{order_id}.pdf")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)

    # En-tête de la facture
    pdf.cell(200, 10, f"Facture N°: {order_id}", ln=True, align="C")
    pdf.ln(10)  # Espace

    # Informations du client
    pdf.set_font("Arial", "", 12)
    pdf.cell(100, 10, f"Client: {customer_name if customer_name else 'Client inconnu'}", ln=True)
    pdf.cell(100, 10, f"Email: {customer_email}", ln=True)
    pdf.ln(10)

    # Tableau des produits
    pdf.set_font("Arial", "B", 12)
    pdf.cell(80, 10, "Produit", 1, 0, "C")
    pdf.cell(30, 10, "Quantité", 1, 0, "C")
    pdf.cell(40, 10, "Prix Unitaire", 1, 0, "C")
    pdf.cell(40, 10, "Total", 1, 1, "C")

    pdf.set_font("Arial", "", 12)
    for item in items:
        pdf.cell(80, 10, item["name"], 1, 0, "C")
        pdf.cell(30, 10, str(item["quantity"]), 1, 0, "C")
        pdf.cell(40, 10, f"{item['price']}", 1, 0, "C")
        pdf.cell(40, 10, f"{item['quantity'] * item['price']}", 1, 1, "C")

    # Ligne Total
    pdf.set_font("Arial", "B", 12)
    pdf.cell(150, 10, "Total général", 1, 0, "C")
    pdf.cell(40, 10, f"{total_price}", 1, 1, "C")

    pdf.output(file_path)

    # Envoi de la facture par email
    send_invoice_by_email(customer_email, file_path, order_id)

    return file_path


# Fonction pour envoyer la facture par e-mail
def send_invoice_by_email(to_email, file_path, order_id):
    sender_email = "tonemail@gmail.com"  # Remplace par ton email
    sender_password = "tonmotdepasse"  # Remplace par ton mot de passe

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = f"Votre Facture N° {order_id}"

    # Attacher le fichier PDF
    with open(file_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename=invoice_{order_id}.pdf")
        msg.attach(part)

    # Envoi de l'e-mail
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        print(f"Facture envoyée à {to_email}")
    except Exception as e:
        print(f"Erreur d'envoi d'email: {e}")
