# database.py
import os
import sqlite3
import json
from kivy.utils import platform

# ===================================================
# CONFIGURATION DU CHEMIN DE BASE DE DONNEES
# ===================================================

# Determiner le chemin de la base de donnees selon la plateforme
if platform == 'android':
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        context = PythonActivity.mActivity
        # Obtenir le repertoire de fichiers prives de l'application
        files_dir = context.getFilesDir().getAbsolutePath()
        DB_PATH = os.path.join(str(files_dir), "gestion_clients.db")
        print(f"Base de donnees Android : {DB_PATH}")
    except Exception as e:
        print(f"Erreur chemin Android: {e}, utilisation du stockage externe")
        DB_PATH = os.path.join("/sdcard", "gestion_clients.db")
else:
    DB_NAME = "gestion_clients.db"
    DB_PATH = DB_NAME
    print(f"Base de donnees locale : {DB_PATH}")


# ===================================================
# INITIALISATION DE LA BASE DE DONNEES
# ===================================================

def init_database():
    """Initialise la base de donnees et cree les tables si elles n'existent pas"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Table clients
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                adresse TEXT,
                nif TEXT,
                stat TEXT,
                contact TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table produits
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                prix_achat TEXT,
                prix_vente TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table commandes avec la colonne numero_cheque
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commandes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_nom TEXT NOT NULL,
                produits TEXT,
                total REAL,
                avance REAL,
                reste REAL,
                mode_paiement TEXT DEFAULT 'Espece',
                numero_cheque TEXT,
                date_commande TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

        # Appliquer les migrations necessaires
        migrer_ajouter_colonne_numero_cheque()
        ajouter_colonne_mode_paiement()

        print("Base de donnees initialisee avec succes")
        return True

    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de donnees: {e}")
        return False


# ===================================================
# FONCTIONS DE MIGRATION
# ===================================================

def ajouter_colonne_mode_paiement():
    """Ajoute la colonne mode_paiement si elle n'existe pas (migration)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verifier si la colonne existe
        cursor.execute("PRAGMA table_info(commandes)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'mode_paiement' not in columns:
            print("Ajout de la colonne 'mode_paiement'...")
            cursor.execute("ALTER TABLE commandes ADD COLUMN mode_paiement TEXT DEFAULT 'Espece'")
            conn.commit()
            print("Colonne 'mode_paiement' ajoutee avec succes")

        # Mettre a jour les valeurs NULL
        cursor.execute("UPDATE commandes SET mode_paiement = 'Espece' WHERE mode_paiement IS NULL")
        conn.commit()

        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de la migration mode_paiement: {e}")
        return False


def migrer_ajouter_colonne_numero_cheque():
    """Ajoute la colonne numero_cheque a la table commandes si elle n'existe pas"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verifier si la colonne existe
        cursor.execute("PRAGMA table_info(commandes)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'numero_cheque' not in columns:
            print("Ajout de la colonne 'numero_cheque'...")
            cursor.execute("ALTER TABLE commandes ADD COLUMN numero_cheque TEXT")
            conn.commit()
            print("Colonne 'numero_cheque' ajoutee avec succes")
        else:
            print("La colonne 'numero_cheque' existe deja")

        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de la migration numero_cheque: {e}")
        return False


# ===================================================
# FONCTIONS POUR CLIENTS
# ===================================================

def ajouter_client_db(nom, adresse, nif, stat, contact):
    """Ajoute un nouveau client dans la base de donnees"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO clients (nom, adresse, nif, stat, contact)
            VALUES (?, ?, ?, ?, ?)
        ''', (nom, adresse, nif, stat, contact))

        conn.commit()
        client_id = cursor.lastrowid
        conn.close()
        return client_id
    except Exception as e:
        print(f"Erreur lors de l'ajout du client: {e}")
        return None


def get_all_clients():
    """Recupere tous les clients de la base de donnees"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT nom, adresse, nif, stat, contact FROM clients ORDER BY id DESC')
        clients = cursor.fetchall()

        conn.close()
        return clients
    except Exception as e:
        print(f"Erreur lors de la recuperation des clients: {e}")
        return []


def supprimer_client_db(client_id):
    """Supprime un client de la base de donnees"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de la suppression du client: {e}")
        return False


def get_clients_count():
    """Recupere le nombre total de clients"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM clients')
        count = cursor.fetchone()[0]

        conn.close()
        return count
    except Exception as e:
        print(f"Erreur lors du comptage des clients: {e}")
        return 0


# ===================================================
# FONCTIONS POUR PRODUITS
# ===================================================

def ajouter_produit_db(nom, prix_achat, prix_vente):
    """Ajoute un nouveau produit dans la base de donnees"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO produits (nom, prix_achat, prix_vente)
            VALUES (?, ?, ?)
        ''', (nom, prix_achat, prix_vente))

        conn.commit()
        produit_id = cursor.lastrowid
        conn.close()
        return produit_id
    except Exception as e:
        print(f"Erreur lors de l'ajout du produit: {e}")
        return None


def get_all_produits():
    """Recupere tous les produits de la base de donnees"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT nom, prix_achat, prix_vente FROM produits ORDER BY id DESC')
        produits = cursor.fetchall()

        conn.close()
        return produits
    except Exception as e:
        print(f"Erreur lors de la recuperation des produits: {e}")
        return []


def supprimer_produit_db(produit_id):
    """Supprime un produit de la base de donnees"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM produits WHERE id = ?', (produit_id,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de la suppression du produit: {e}")
        return False


def get_produits_count():
    """Recupere le nombre total de produits"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM produits')
        count = cursor.fetchone()[0]

        conn.close()
        return count
    except Exception as e:
        print(f"Erreur lors du comptage des produits: {e}")
        return 0


# ===================================================
# FONCTIONS POUR COMMANDES
# ===================================================

def ajouter_commande_db(client_nom=None, produits=None, total=None, avance=None,
                         reste=None, mode_paiement=None, numero_cheque=None, date=None):
    """Ajoute une nouvelle commande dans la base de donnees"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        produits_json = json.dumps(produits, ensure_ascii=False) if produits else "[]"

        cursor.execute("""
            INSERT INTO commandes (client_nom, produits, total, avance, reste, mode_paiement, numero_cheque, date_commande)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (client_nom, produits_json, total, avance, reste, mode_paiement, numero_cheque, date))

        commande_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return commande_id
    except Exception as e:
        print(f"Erreur ajout commande: {e}")
        return None


def get_all_commandes():
    """Recupere toutes les commandes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT id, client_nom, total, avance, reste, mode_paiement, date_commande FROM commandes ORDER BY id DESC')
        commandes = cursor.fetchall()

        conn.close()
        return commandes
    except Exception as e:
        print(f"Erreur lors de la recuperation des commandes: {e}")
        return []


def get_commandes_client(client_nom):
    """Recupere toutes les commandes d'un client specifique"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, client_nom, total, avance, reste, mode_paiement, date_commande 
            FROM commandes 
            WHERE client_nom = ? 
            ORDER BY id DESC
        ''', (client_nom,))

        commandes = cursor.fetchall()
        conn.close()
        return commandes
    except Exception as e:
        print(f"Erreur lors de la recuperation des commandes du client: {e}")
        return []


def get_commande_by_id(commande_id):
    """Recupere une commande specifique par son ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, client_nom, produits, total, avance, reste, mode_paiement, date_commande 
            FROM commandes 
            WHERE id = ?
        ''', (commande_id,))

        commande = cursor.fetchone()
        conn.close()

        if commande:
            produits = json.loads(commande[2]) if commande[2] else []
            return {
                'id': commande[0],
                'client_nom': commande[1],
                'produits': produits,
                'total': commande[3],
                'avance': commande[4],
                'reste': commande[5],
                'mode_paiement': commande[6],
                'date': commande[7]
            }
        return None
    except Exception as e:
        print(f"Erreur lors de la recuperation de la commande: {e}")
        return None


def supprimer_commande_db(commande_id):
    """Supprime une commande de la base de donnees"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM commandes WHERE id = ?', (commande_id,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de la suppression de la commande: {e}")
        return False


def get_commandes_count():
    """Recupere le nombre total de commandes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM commandes')
        count = cursor.fetchone()[0]

        conn.close()
        return count
    except Exception as e:
        print(f"Erreur lors du comptage des commandes: {e}")
        return 0


def get_commandes_count_by_client(client_nom):
    """Recupere le nombre de commandes pour un client specifique"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM commandes WHERE client_nom = ?', (client_nom,))
        count = cursor.fetchone()[0]

        conn.close()
        return count
    except Exception as e:
        print(f"Erreur lors du comptage des commandes du client: {e}")
        return 0


def payer_reste_db(commande_id, montant_paye, nouveau_reste):
    """Met a jour le paiement d'une commande"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE commandes
            SET avance = avance + ?, reste = ?
            WHERE id = ?
        """, (montant_paye, nouveau_reste, commande_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur payer_reste_db: {e}")
        return False