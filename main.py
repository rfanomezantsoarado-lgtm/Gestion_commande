from kivy.config import Config

# Taille téléphone Android
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', '0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.logger import Logger
import sys
import os

# Gestion des erreurs globales
def handle_exception(exc_type, exc_value, exc_traceback):
    Logger.exception("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    if issubclass(exc_type, Exception):
        # Enregistrer l'erreur dans un fichier
        with open('/sdcard/error_log.txt', 'a') as f:
            import traceback
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)

sys.excepthook = handle_exception

# Importations conditionnelles pour Android
try:
    from accueil import AccueilScreen
    from clients import ClientScreen
    from produits import ProduitScreen
    from commande import CommandeScreen
    from historique_commande import HistoriqueCommandeScreen
except ImportError as e:
    Logger.error(f"Import error: {e}")
    raise

class ENApp(App):
    def build(self):
        try:
            sm = ScreenManager()

            sm.add_widget(AccueilScreen(name="accueil"))
            sm.add_widget(ClientScreen(name="clients"))
            sm.add_widget(ProduitScreen(name="produits"))
            sm.add_widget(CommandeScreen(name="commande"))
            sm.add_widget(HistoriqueCommandeScreen(name="historique_commande"))

            return sm
        except Exception as e:
            Logger.error(f"Build error: {e}")
            # Créer un écran d'erreur simple
            from kivy.uix.label import Label
            return Label(text=f"Erreur: {str(e)}")

if __name__ == "__main__":
    ENApp().run()