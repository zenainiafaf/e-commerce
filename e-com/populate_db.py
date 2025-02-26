import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Création de la table "products" si elle n'existe pas
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL CHECK(stock >= 0),
        image TEXT DEFAULT 'https://via.placeholder.com/150'
    )
''')

# Vérification du nombre de produits existants
cursor.execute("SELECT COUNT(*) FROM products")
count = cursor.fetchone()[0]

# Ajouter des produits si la table est vide
if count == 0:
    products = [
        ("Laptop", 799.99, 10, "https://via.placeholder.com/150"),
        ("Smartphone", 499.99, 15, "https://via.placeholder.com/150"),
        ("Casque Bluetooth", 59.99, 20, "https://via.placeholder.com/150"),
        ("Souris Gamer", 29.99, 30, "https://via.placeholder.com/150"),
        ("Clavier Mécanique", 89.99, 25, "https://via.placeholder.com/150")
    ]

    cursor.executemany("INSERT INTO products (name, price, stock, image) VALUES (?, ?, ?, ?)", products)
    conn.commit()
    print("✅ Produits ajoutés à la base de données.")

else:
    print("ℹ️ La base de données contient déjà des produits, aucun ajout nécessaire.")

# Fermeture de la connexion
conn.close()

print("✅ Base de données initialisée avec succès !")
