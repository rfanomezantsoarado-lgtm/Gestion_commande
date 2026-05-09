from kivy.config import Config

# Taille téléphone Android
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')

# Empêche le redimensionnement Config.set('graphics', 'resizable', '0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from accueil import AccueilScreen
from clients import ClientScreen
from produits import ProduitScreen
from commande import CommandeScreen
from historique_commande import HistoriqueCommandeScreen
class ENApp(App):

    def build(self):

        sm = ScreenManager()

        sm.add_widget(AccueilScreen(name="accueil"))
        sm.add_widget(ClientScreen(name="clients"))
        sm.add_widget(ProduitScreen(name="produits"))
        sm.add_widget(CommandeScreen(name="commande"))
        sm.add_widget(HistoriqueCommandeScreen(name="historique_commande"))

        return sm


if __name__ == "__main__":
    ENApp().run()