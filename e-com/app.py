
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import stripe
from generate_invoice import generate_invoice  # Fichier où la fonction est définie
from flask import Flask, request, jsonify, send_file
from flask_mail import Mail, Message
import os
from datetime import datetime  # ✅ Importation correcte




app = Flask(__name__)

# Configuration de la base de données SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret'

db = SQLAlchemy(app)

stripe.api_key = "sk_test_51QvzwnKSOPBHXeDw42sm4oSPse5qFD7nGcL4xf8VfshNGzj5R4Sluqc52H4JQSOBBGVhVlmk9Uyd5uAVLKTjCS6e00jr9FVFFv"  
STRIPE_PUBLIC_KEY = "pk_test_51QvzwnKSOPBHXeDwplHTdeSwlDRgi1B3ZwpZAY638AuTJaWDL7R9WYQRmat6KNLWaCHvrECsVSVlwOZWXkzhpDku0093aRotO1" 

app.config['MAIL_SERVER'] = 'smtp.office365.com'  # Serveur SMTP d'Outlook
app.config['MAIL_PORT'] = 587  # Port SMTP
app.config['MAIL_USE_TLS'] = True  # Utiliser TLS
app.config['MAIL_USE_SSL'] = False  # SSL doit être désactivé
app.config['MAIL_USERNAME'] = 'lizamezioug03@outlook.com'  # Remplace avec ton adresse Outlook
app.config['MAIL_PASSWORD'] = 'Liza792003'  # Remplace avec ton mot de passe Outlook

mail = Mail(app)

# Modèle de produit
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255), nullable=False)
    stock = db.Column(db.Integer, nullable=False)

# Création des tables
with app.app_context():
    db.create_all()
    # Ajout de produits si la base est vide
    if not Product.query.first():
        sample_products = [
            Product(name="Laptop", price=799.99, image="laptop.jpg", stock=10),
            Product(name="Smartphone", price=499.99, image="Teljpg.jpg", stock=15),
            Product(name="Casque Bluetooth", price=59.99, image="Casque.jpg", stock=20),
            Product(name="Souris Gamer", price=29.99, image="souris.jpg", stock=30),
            Product(name="Clavier Mécanique", price=89.99, image="clavier.jpg", stock=25),
        ]
        db.session.add_all(sample_products)
        db.session.commit()

# Page d'accueil
@app.route('/')
def index():
    products = Product.query.all()
    cart_items = session.get('cart', {})
    cart_count = sum(cart_items.values())
    return render_template('index.html', products=products, cart_count=cart_count, stripe_public_key=STRIPE_PUBLIC_KEY)

# Page du panier
@app.route('/cart')
def cart():
    cart_items = session.get('cart', {})
    cart_data = []
    total_price = 0

    for product_id, quantity in cart_items.items():
        product = Product.query.get(product_id)
        if product:
            total_price += product.price * quantity
            cart_data.append({'product': product, 'quantity': quantity})

    return render_template('cart.html', cart_items=cart_data, total_price=total_price)

# Ajouter au panier
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if not product or product.stock <= 0:
        return jsonify({'error': 'Stock insuffisant'}), 400

    cart = session.get('cart', {})

    # Vérifier que l'ajout ne dépasse pas le stock disponible
    if cart.get(str(product_id), 0) >= product.stock:
        return jsonify({'error': 'Stock insuffisant'}), 400

    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    session.modified = True

    return jsonify({'cart_count': sum(cart.values())})


# Diminuer la quantité dans le panier
@app.route('/decrease_cart/<int:product_id>', methods=['POST'])
def decrease_cart(product_id):
    if 'cart' in session and str(product_id) in session['cart']:
        session['cart'][str(product_id)] -= 1

        if session['cart'][str(product_id)] <= 0:
            del session['cart'][str(product_id)]

        session.modified = True

    return jsonify({'cart_count': sum(session['cart'].values()) if session['cart'] else 0})

# Supprimer un produit du panier
@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session and str(product_id) in session['cart']:
        del session['cart'][str(product_id)]
        session.modified = True

    return jsonify({'cart_count': sum(session['cart'].values()) if session['cart'] else 0})

# Vider le panier
@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('cart'))

# Créer une session de paiement Stripe
@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    cart_items = session.get('cart', {})
    line_items = []

    for product_id, quantity in cart_items.items():
        product = Product.query.get(product_id)
        if product:
            line_items.append({
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': product.name,
                    },
                    'unit_amount': int(product.price * 100),  # Stripe utilise les centimes
                },
                'quantity': quantity,
            })

    if not line_items:
        return redirect(url_for('cart'))

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=url_for('success', _external=True),
            cancel_url=url_for('cart', _external=True),
            customer_creation="always"  # Crée toujours un client avec ses infos
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return str(e), 400


@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = "whsec_9d48afa36c993d3871f24b8bedfc65a659f45f7803b175dd3f9d85c6d04cf316"  # Remplace par le secret Webhook de Stripe

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session_data = event['data']['object']
        customer_email = session_data.get('customer_details', {}).get('email', '')
        customer_name = session_data.get('customer_details', {}).get('name', '')

        # Stocker ces informations en session ou base de données
        session['customer_email'] = customer_email
        session['customer_name'] = customer_name

    return '', 200







# Page de succès après paiement
@app.route('/success')
def success():
    cart_items = session.get('cart', {})

    if not cart_items:
        return redirect(url_for('index'))  # Rediriger si le panier est vide

    # Récupérer les informations du client depuis Stripe
    payment_intent = session.get('payment_intent', {})
    customer_name = session.get('customer_name', 'Client inconnu')
    customer_email = session.get('customer_email', '')
    order_id = f"CMD{int(datetime.now().timestamp())}"

    # Préparer les données pour la facture
    items = []
    total_price = 0
    for product_id, quantity in cart_items.items():
        product = Product.query.get(product_id)
        if product:
            items.append({
                'name': product.name,
                'quantity': quantity,
                'price': product.price
            })
            total_price += product.price * quantity
            product.stock -= quantity  # Mise à jour du stock

    db.session.commit()  # Sauvegarde des modifications

    # Générer la facture
    invoice_path = generate_invoice(order_id, customer_name, customer_email, items, total_price)

    # Envoyer la facture par e-mail
    if customer_email:
        try:
            msg = Message("Votre Facture", sender=app.config['MAIL_USERNAME'], recipients=[customer_email])
            msg.body = "Veuillez trouver votre facture ci-jointe."
            with app.open_resource(invoice_path) as fp:
                msg.attach(os.path.basename(invoice_path), "application/pdf", fp.read())
            mail.send(msg)
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email: {e}")

    # Vider le panier après la facture
    session.pop('cart', None)

    return render_template('success.html', invoice_path=invoice_path)













@app.route('/generate_invoice', methods=['POST'])
def generate_invoice_route():
    data = request.json
    if not data or 'order_id' not in data or 'customer_name' not in data or 'items' not in data or 'total_price' not in data:
        return jsonify({"error": "Données invalides"}), 400

    order_id = data['order_id']
    customer_name = data['customer_name']
    items = data['items']
    total_price = data['total_price']

    invoice_path = generate_invoice(order_id, customer_name, items, total_price)

    if invoice_path and os.path.exists(invoice_path):
        return send_file(invoice_path, as_attachment=True)
    return jsonify({"error": "Échec de la génération de la facture"}), 500







if __name__ == '__main__':
    app.run(debug=True)

