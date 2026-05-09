from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from database import (init_database, get_all_produits, get_all_clients,
                      ajouter_commande_db, payer_reste_db, get_all_commandes)
import datetime
import os
import re
import subprocess
import sys
from kivy.utils import platform

# Importer le générateur PDF depuis pdf_generator
from pdf_generator import generer_pdf_facture

# Import conditionnel pour Android
ANDROID_AVAILABLE = False
if platform == 'android':
    try:
        from android import activity
        from android.permissions import request_permissions, Permission
        from jnius import autoclass
        ANDROID_AVAILABLE = True
    except ImportError:
        pass

# ===================================================
# COULEURS
# ===================================================
BG_DARK       = (0.04, 0.07, 0.16, 1)
BG_CARD       = (0.07, 0.11, 0.22, 1)
ACCENT        = (0.08, 0.45, 0.82, 1)
ACCENT_GREEN  = (0.05, 0.68, 0.38, 1)
ACCENT_RED    = (0.82, 0.08, 0.08, 1)
ACCENT_ORANGE = (0.95, 0.55, 0.08, 1)
ACCENT_PURPLE = (0.55, 0.08, 0.82, 1)
TEXT_WHITE    = (1, 1, 1, 1)
ROW_ODD       = (0.10, 0.16, 0.30, 1)
ROW_EVEN      = (0.07, 0.12, 0.24, 1)
HEADER_BG     = (0.05, 0.35, 0.65, 1)
BAR_TOP       = (0.05, 0.08, 0.18, 1)
TEXT_DIM      = (0.6, 0.6, 0.6, 1)
ACCENT_BLUE   = (0.08, 0.45, 0.82, 1)


def _bg(widget, color, radius=0):
    with widget.canvas.before:
        Color(*color)
        if radius:
            rr = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
        else:
            rr = Rectangle(pos=widget.pos, size=widget.size)
        widget.bind(
            pos=lambda i, v, r=rr: setattr(r, 'pos', v),
            size=lambda i, v, r=rr: setattr(r, 'size', v)
        )


def make_cell(text, w, bg_color, bold=False, font_size=13):
    lbl = Label(
        text=f"[b]{text}[/b]" if bold else text,
        markup=bold,
        size_hint=(None, None),
        size=(w, 35),
        font_size=font_size,
        color=TEXT_WHITE,
        halign="center",
        valign="middle"
    )
    lbl.bind(size=lambda inst, v: setattr(inst, "text_size", v))
    _bg(lbl, bg_color)
    return lbl


class CommandeScreen(Screen):

    HEADERS_COMMANDE = ["Designation", "Prix unitaire", "Quantite", "Montant"]
    COL_WIDTHS_COMMANDE = [140, 100, 80, 100]
    ROW_H = 35

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.produits_disponibles = []
        self.produits_commandes = []
        self.clients_disponibles = []
        self.total_commande = 0
        self._derniere_commande_id = None

        main_scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=8,
            bar_color=list(ACCENT[:3]) + [0.8]
        )
        main_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=8,
            padding=[5, 5, 5, 5]
        )
        main_container.bind(minimum_height=main_container.setter('height'))

        # ── BARRE HAUTE ───────────────────────────────────
        top_bar = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=50,
            padding=[8, 5, 8, 5],
            spacing=10
        )
        _bg(top_bar, BAR_TOP)

        top_bar.add_widget(Label(size_hint=(None, 1), width=80))
        title_label = Label(
            text="[b]COMMANDE[/b]",
            markup=True, font_size=18,
            color=TEXT_WHITE, size_hint=(1, 1),
            halign="center", valign="middle"
        )
        title_label.bind(size=lambda inst, v: setattr(inst, "text_size", v))
        top_bar.add_widget(title_label)
        top_bar.add_widget(Label(size_hint=(None, 1), width=80))
        main_container.add_widget(top_bar)

        # ── SECTION CLIENT ────────────────────────────────
        client_card = BoxLayout(
            orientation="vertical",
            size_hint=(1, None), height=160,
            padding=[10, 8, 10, 8], spacing=6
        )
        _bg(client_card, BG_CARD, radius=12)
        client_card.add_widget(Label(
            text="[b]Informations client[/b]", markup=True,
            font_size=13, color=ACCENT,
            size_hint=(1, None), height=22, halign="left"
        ))
        client_row = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        client_row.add_widget(Label(
            text="Client :", size_hint=(0.2, 1),
            color=TEXT_WHITE, font_size=12, halign="right"
        ))
        self.client_spinner = Spinner(
            text="Choisir un client", values=[],
            size_hint=(0.8, 1), font_size=12,
            background_color=(0.1, 0.16, 0.30, 1), color=TEXT_WHITE
        )
        self.client_spinner.bind(text=self.on_client_select)
        client_row.add_widget(self.client_spinner)
        client_card.add_widget(client_row)
        self.client_details = Label(
            text="", font_size=11, color=TEXT_WHITE,
            size_hint=(1, None), height=50,
            halign="left", valign="top"
        )
        self.client_details.bind(
            size=lambda inst, v: setattr(inst, "text_size", (v[0] - 15, None))
        )
        client_card.add_widget(self.client_details)
        main_container.add_widget(client_card)

        # ── SECTION PRODUIT ───────────────────────────────
        produit_card = BoxLayout(
            orientation="vertical",
            size_hint=(1, None), height=170,
            padding=[10, 8, 10, 8], spacing=6
        )
        _bg(produit_card, BG_CARD, radius=12)
        produit_card.add_widget(Label(
            text="[b]Ajouter un produit[/b]", markup=True,
            font_size=13, color=ACCENT,
            size_hint=(1, None), height=22
        ))
        produit_row = BoxLayout(size_hint=(1, None), height=38, spacing=10)
        produit_row.add_widget(Label(
            text="Produit :", size_hint=(0.25, 1),
            color=TEXT_WHITE, font_size=12, halign="right"
        ))
        self.produit_spinner = Spinner(
            text="Choisir un produit", values=[],
            size_hint=(0.75, 1), font_size=12,
            background_color=(0.1, 0.16, 0.30, 1), color=TEXT_WHITE
        )
        self.produit_spinner.bind(text=self.on_produit_select)
        produit_row.add_widget(self.produit_spinner)
        produit_card.add_widget(produit_row)

        prix_row = BoxLayout(size_hint=(1, None), height=38, spacing=10)
        prix_row.add_widget(Label(
            text="Prix unitaire (Ar) :", size_hint=(0.25, 1),
            color=TEXT_WHITE, font_size=12, halign="right"
        ))
        self.prix_vente_client = TextInput(
            text="", multiline=False, font_size=12,
            foreground_color=TEXT_WHITE,
            background_color=(0.1, 0.16, 0.30, 1),
            size_hint=(0.5, 1), padding=[8, 8]
        )
        prix_row.add_widget(self.prix_vente_client)
        prix_row.add_widget(Label(size_hint=(0.25, 1)))
        produit_card.add_widget(prix_row)

        quantite_row = BoxLayout(size_hint=(1, None), height=38, spacing=10)
        quantite_row.add_widget(Label(
            text="Quantite :", size_hint=(0.25, 1),
            color=TEXT_WHITE, font_size=12, halign="right"
        ))
        self.quantite = TextInput(
            text="1", multiline=False, font_size=12,
            foreground_color=TEXT_WHITE,
            background_color=(0.1, 0.16, 0.30, 1),
            size_hint=(0.2, 1), padding=[8, 8]
        )
        self.quantite.bind(text=self.on_quantite_change)
        quantite_row.add_widget(self.quantite)
        btn_ajouter = Button(
            text="+ AJOUTER", size_hint=(0.3, 1),
            font_size=11, bold=True,
            background_normal="",
            background_color=ACCENT, color=TEXT_WHITE
        )
        btn_ajouter.bind(on_release=self.ajouter_produit_commande)
        quantite_row.add_widget(btn_ajouter)
        quantite_row.add_widget(Label(size_hint=(0.25, 1)))
        produit_card.add_widget(quantite_row)
        main_container.add_widget(produit_card)

        # ── TABLEAU PRODUITS COMMANDES ────────────────────
        self.lbl_count_commande = Label(
            text="Produits commandes  -  0 article(s)",
            font_size=11, color=TEXT_WHITE,
            size_hint=(1, None), height=22,
            halign="left", valign="middle"
        )
        main_container.add_widget(self.lbl_count_commande)

        table_commande_container = BoxLayout(size_hint=(1, None), height=200)
        total_w_commande = sum(self.COL_WIDTHS_COMMANDE)
        self.table_commande = GridLayout(
            cols=4,
            size_hint=(None, None), width=total_w_commande,
            row_default_height=self.ROW_H, row_force_default=True,
            spacing=0, padding=0
        )
        self.table_commande.bind(minimum_height=self.table_commande.setter('height'))
        for h, w in zip(self.HEADERS_COMMANDE, self.COL_WIDTHS_COMMANDE):
            self.table_commande.add_widget(
                make_cell(h, w, HEADER_BG, bold=True, font_size=11)
            )
        scroll_commande = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=True, do_scroll_y=True, bar_width=4
        )
        scroll_commande.add_widget(self.table_commande)
        table_commande_container.add_widget(scroll_commande)
        main_container.add_widget(table_commande_container)

        # ── SECTION PAIEMENT ─────────────────────────────
        paiement_card = BoxLayout(
            orientation="vertical",
            size_hint=(1, None), height=220,
            padding=[10, 8, 10, 8], spacing=6
        )
        _bg(paiement_card, BG_CARD, radius=12)
        paiement_card.add_widget(Label(
            text="[b]Informations de paiement[/b]", markup=True,
            font_size=13, color=ACCENT,
            size_hint=(1, None), height=22
        ))

        # Mode de paiement
        mode_row = BoxLayout(size_hint=(1, None), height=35, spacing=8)
        mode_row.add_widget(Label(
            text="Mode de paiement :", size_hint=(0.3, 1),
            color=TEXT_WHITE, font_size=12, halign="right"
        ))
        self.mode_paiement = Spinner(
            text="Espèce",
            values=["Espèce", "Mvola", "Chèque"],
            size_hint=(0.7, 1),
            font_size=11,
            background_color=(0.1, 0.16, 0.30, 1),
            color=TEXT_WHITE
        )
        self.mode_paiement.bind(text=self.on_mode_paiement_change)
        mode_row.add_widget(self.mode_paiement)
        paiement_card.add_widget(mode_row)

        # Numéro de chèque
        cheque_row = BoxLayout(size_hint=(1, None), height=38, spacing=10)
        cheque_row.add_widget(Label(
            text="N° Chèque :", size_hint=(0.3, 1),
            color=TEXT_WHITE, font_size=12, halign="right"
        ))
        self.numero_cheque = TextInput(
            text="", multiline=False, font_size=12,
            foreground_color=TEXT_WHITE,
            background_color=(0.1, 0.16, 0.30, 1),
            size_hint=(0.7, 1), padding=[8, 8],
            hint_text="Numéro du chèque"
        )
        cheque_row.add_widget(self.numero_cheque)
        paiement_card.add_widget(cheque_row)
        self.numero_cheque.opacity = 0
        self.numero_cheque.disabled = True

        total_row = BoxLayout(size_hint=(1, None), height=35, spacing=10)
        total_row.add_widget(Label(
            text="Total commande (Ar) :", size_hint=(0.5, 1),
            color=TEXT_WHITE, font_size=13, bold=True, halign="right"
        ))
        self.lbl_total = Label(
            text="0", size_hint=(0.5, 1),
            color=ACCENT_GREEN, font_size=14,
            bold=True, halign="left", valign="middle"
        )
        total_row.add_widget(self.lbl_total)
        paiement_card.add_widget(total_row)

        avance_row = BoxLayout(size_hint=(1, None), height=38, spacing=10)
        avance_row.add_widget(Label(
            text="Montant verse (Ar) :", size_hint=(0.5, 1),
            color=TEXT_WHITE, font_size=12, halign="right"
        ))
        self.montant_verse = TextInput(
            text="0", multiline=False, font_size=12,
            foreground_color=TEXT_WHITE,
            background_color=(0.1, 0.16, 0.30, 1),
            size_hint=(0.5, 1), padding=[8, 8]
        )
        avance_row.add_widget(self.montant_verse)
        paiement_card.add_widget(avance_row)

        reste_row = BoxLayout(size_hint=(1, None), height=38, spacing=10)
        reste_row.add_widget(Label(
            text="Reste a payer (Ar) :", size_hint=(0.5, 1),
            color=ACCENT_RED,
            font_size=12, bold=True, halign="right"
        ))
        self.reste_payer = TextInput(
            text="0", multiline=False, font_size=13,
            foreground_color=ACCENT_RED,
            background_color=(0.08, 0.12, 0.25, 1),
            size_hint=(0.5, 1), padding=[8, 8], disabled=True,
            disabled_foreground_color=ACCENT_RED
        )
        reste_row.add_widget(self.reste_payer)
        paiement_card.add_widget(reste_row)

        self.montant_verse.bind(text=self.calculer_reste)
        main_container.add_widget(paiement_card)

        # ── BOUTONS ────────────────────────────────────────
        btn_row = BoxLayout(
            size_hint=(1, None), height=50,
            padding=[10, 5, 10, 5], spacing=10
        )

        btn_abandonner = Button(
            text="FERMER",
            font_size=12, bold=True,
            background_normal="",
            background_color=(0, 0, 0, 0), color=TEXT_WHITE
        )
        _bg(btn_abandonner, ACCENT_RED, radius=8)
        btn_abandonner.bind(on_release=self.abandonner_commande)

        btn_pdf = Button(
            text="EXPORTER PDF",
            font_size=12, bold=True,
            background_normal="",
            background_color=(0, 0, 0, 0), color=TEXT_WHITE
        )
        _bg(btn_pdf, ACCENT_PURPLE, radius=8)
        btn_pdf.bind(on_release=self.exporter_pdf)

        btn_row.add_widget(btn_abandonner)
        btn_row.add_widget(btn_pdf)
        main_container.add_widget(btn_row)

        main_scroll.add_widget(main_container)
        self.add_widget(main_scroll)
        Clock.schedule_once(lambda dt: self.initialiser_donnees(), 0.5)

    # ═══════════════════════════════════════════════════════════
    # MÉTHODES PRINCIPALES
    # ═══════════════════════════════════════════════════════════

    def abandonner_commande(self, instance):
        self.reset_commande(None)
        self.manager.current = "accueil"

    def exporter_pdf(self, instance):
        if not self._valider_commande():
            return
        try:
            montant_verse = self._get_montant_verse()
            reste = max(0, self.total_commande - montant_verse)
            mode_paiement = self.mode_paiement.text

            numero_cheque = ""
            if mode_paiement == "Chèque":
                numero_cheque = self.numero_cheque.text.strip()
                if not numero_cheque:
                    self.show_message("Information", "Veuillez saisir le numéro du chèque")
                    return

            commande_id = ajouter_commande_db(
                client_nom=self.client_spinner.text,
                produits=self.produits_commandes,
                total=self.total_commande,
                avance=montant_verse,
                reste=reste,
                mode_paiement=mode_paiement,
                numero_cheque=numero_cheque,
                date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            if not commande_id:
                self.show_message("Erreur", "Erreur lors de l'enregistrement")
                return

            client_info = {}
            for c in self.clients_disponibles:
                if c['nom'] == self.client_spinner.text:
                    client_info = c
                    break

            filename = generer_pdf_facture(
                commande_id=commande_id,
                client_nom=self.client_spinner.text,
                client_info=client_info,
                produits=self.produits_commandes,
                total=self.total_commande,
                avance=montant_verse,
                reste=reste,
                mode_paiement=mode_paiement,
                numero_cheque=numero_cheque,
                date_str=datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            )

            if filename:
                self.afficher_apercu_pdf(filename, commande_id)
            else:
                self._generer_txt(commande_id, montant_verse, reste, mode_paiement, numero_cheque)
                self.show_message(
                    "Succès",
                    f"Commande N° {commande_id} enregistrée.\n"
                    f"Mode de paiement: {mode_paiement}\n"
                    "(Installez reportlab pour le PDF)"
                )

            self.reset_commande(None)

        except Exception as e:
            self.show_message("Erreur", str(e))

    def afficher_apercu_pdf(self, chemin_pdf, commande_id):
        content = BoxLayout(orientation='vertical', spacing=12, padding=15)
        _bg(content, BG_DARK)

        content.add_widget(Label(
            text=f"[b]Facture N° {commande_id}[/b]\n\nPDF généré avec succès !",
            markup=True,
            font_size=13,
            color=TEXT_WHITE,
            size_hint=(1, None),
            height=60,
            halign="center"
        ))

        info_box = BoxLayout(orientation='vertical', size_hint=(1, None), height=50, spacing=5)
        info_box.add_widget(Label(
            text=f"{os.path.basename(chemin_pdf)}",
            font_size=10,
            color=ACCENT,
            halign="center"
        ))
        content.add_widget(info_box)

        btn_box = BoxLayout(orientation='vertical', spacing=8, size_hint=(1, None))
        btn_box.height = 130

        btn_voir = Button(
            text="VISUALISER",
            size_hint=(1, None), height=38,
            font_size=12, bold=True,
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=TEXT_WHITE
        )
        _bg(btn_voir, ACCENT_BLUE, radius=6)
        btn_voir.bind(on_release=lambda x: self.visualiser_pdf(chemin_pdf))

        btn_imprimer = Button(
            text="IMPRIMER",
            size_hint=(1, None), height=38,
            font_size=12, bold=True,
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=TEXT_WHITE
        )
        _bg(btn_imprimer, ACCENT_PURPLE, radius=6)
        btn_imprimer.bind(on_release=lambda x: self.imprimer_pdf(chemin_pdf))

        btn_fermer = Button(
            text="FERMER",
            size_hint=(1, None), height=38,
            font_size=11,
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=TEXT_WHITE
        )
        _bg(btn_fermer, ACCENT_RED, radius=6)

        btn_box.add_widget(btn_voir)
        btn_box.add_widget(btn_imprimer)
        btn_box.add_widget(btn_fermer)
        content.add_widget(btn_box)

        popup = Popup(
            title="Facture prête",
            content=content,
            size_hint=(0.9, 0.55),
            background_color=BG_CARD
        )
        btn_fermer.bind(on_release=popup.dismiss)
        popup.open()

    def visualiser_pdf(self, chemin_pdf):
        try:
            if sys.platform == 'win32':
                os.startfile(chemin_pdf)
            elif sys.platform == 'darwin':
                subprocess.run(['open', chemin_pdf])
            else:
                subprocess.run(['xdg-open', chemin_pdf])
        except Exception as e:
            self.show_message("Erreur", f"Impossible d'ouvrir le PDF: {e}")

    def imprimer_pdf(self, chemin_pdf):
        try:
            if sys.platform == 'win32':
                subprocess.run(['print', chemin_pdf], shell=True)
                self.show_message("Impression", "Impression envoyée")
            else:
                self.show_message(
                    "Impression",
                    f"Le fichier PDF est disponible ici:\n{chemin_pdf}\n\n"
                    "Ouvrez-le avec une application PDF pour imprimer."
                )
        except Exception as e:
            self.show_message("Erreur", f"Erreur d'impression: {e}")

    # ═══════════════════════════════════════════════════════════
    # MÉTHODES UTILITAIRES
    # ═══════════════════════════════════════════════════════════

    def _valider_commande(self):
        if not self.produits_commandes:
            self.show_message("Erreur", "Aucun produit dans la commande")
            return False
        if self.client_spinner.text == "Choisir un client":
            self.show_message("Erreur", "Veuillez sélectionner un client")
            return False
        return True

    def _get_montant_verse(self):
        montant_text = re.sub(r'[^0-9.]', '', self.montant_verse.text or "0")
        montant = float(montant_text) if montant_text else 0
        if montant > self.total_commande:
            montant = self.total_commande
            Clock.schedule_once(lambda dt: setattr(self.montant_verse, 'text', str(int(montant))))
        return montant

    def on_enter(self):
        self.initialiser_donnees()

    def initialiser_donnees(self):
        try:
            init_database()
            self.charger_produits()
            self.charger_clients()
        except Exception as e:
            print(f"Erreur init: {e}")

    def charger_produits(self):
        try:
            produits_data = get_all_produits()
            self.produits_disponibles = []
            lst = []
            for p in produits_data:
                if len(p) >= 3:
                    nom = str(p[0])
                    self.produits_disponibles.append(
                        {'nom': nom, 'prix_vente': str(p[2]) if p[2] else "0"}
                    )
                    lst.append(nom)
            if self.produit_spinner:
                self.produit_spinner.values = lst
        except Exception as e:
            print(f"Erreur produits: {e}")

    def charger_clients(self):
        try:
            clients_data = get_all_clients()
            self.clients_disponibles = []
            lst = []
            for c in clients_data:
                if len(c) >= 5:
                    self.clients_disponibles.append({
                        'nom': str(c[0]),
                        'adresse': str(c[1]) if c[1] else "",
                        'nif': str(c[2]) if c[2] else "",
                        'stat': str(c[3]) if c[3] else "",
                        'contact': str(c[4]) if c[4] else ""
                    })
                    lst.append(str(c[0]))
            if self.client_spinner:
                self.client_spinner.values = lst
        except Exception as e:
            print(f"Erreur clients: {e}")

    def on_client_select(self, spinner, text):
        if text != "Choisir un client" and self.client_details:
            for c in self.clients_disponibles:
                if c['nom'] == text:
                    self.client_details.text = (
                        f"[b]Adresse:[/b] {c['adresse']}\n"
                        f"[b]NIF:[/b] {c['nif']} | "
                        f"[b]STAT:[/b] {c['stat']} | "
                        f"[b]Contact:[/b] {c['contact']}"
                    )
                    self.client_details.markup = True
                    break
        elif self.client_details:
            self.client_details.text = ""

    def on_produit_select(self, spinner, text):
        if text != "Choisir un produit":
            for p in self.produits_disponibles:
                if p['nom'] == text:
                    self.prix_vente_client.text = str(p['prix_vente'])
                    break

    def on_quantite_change(self, instance, value):
        if value and not value.isdigit():
            nv = re.sub(r'[^0-9]', '', value) or "1"
            self.quantite.text = nv

    def ajouter_produit_commande(self, instance):
        nom = self.produit_spinner.text
        if nom == "Choisir un produit":
            self.show_message("Info", "Sélectionnez un produit")
            return
        try:
            prix = float(re.sub(r'[^0-9.]', '', self.prix_vente_client.text or "0") or 0)
            qte = int(self.quantite.text or "1")
            if prix <= 0:
                self.show_message("Erreur", "Prix invalide")
                return
        except ValueError:
            self.show_message("Erreur", "Vérifiez prix et quantité")
            return
        self.produits_commandes.append(
            {'nom': nom, 'prix_unitaire': prix, 'quantite': qte, 'total': prix * qte}
        )
        self.actualiser_tableau_commande()
        self.produit_spinner.text = "Choisir un produit"
        self.prix_vente_client.text = ""
        self.quantite.text = "1"

    def actualiser_tableau_commande(self):
        if not self.table_commande:
            return
        enfants = list(self.table_commande.children)
        nb = len(self.HEADERS_COMMANDE)
        for e in (enfants[:-nb] if len(enfants) > nb else []):
            self.table_commande.remove_widget(e)
        self.total_commande = 0
        for idx, p in enumerate(self.produits_commandes):
            rc = ROW_ODD if idx % 2 == 0 else ROW_EVEN
            for val, w in zip(
                [p['nom'], f"{p['prix_unitaire']:,.0f}",
                 str(p['quantite']), f"{p['total']:,.0f}"],
                self.COL_WIDTHS_COMMANDE
            ):
                self.table_commande.add_widget(
                    make_cell(val, w, rc, bold=False, font_size=11)
                )
            self.total_commande += p['total']
        if self.lbl_total:
            self.lbl_total.text = f"{self.total_commande:,.0f} Ar"
        if self.lbl_count_commande:
            self.lbl_count_commande.text = (
                f"Produits commandés  -  {len(self.produits_commandes)} article(s)"
            )
        self.calculer_reste()

    def calculer_reste(self, *args):
        try:
            montant_text = re.sub(r'[^0-9.]', '', self.montant_verse.text or "0")
            montant = float(montant_text) if montant_text else 0
            reste = max(0, self.total_commande - montant)
            self.reste_payer.text = f"{reste:,.0f}"
            if reste > 0:
                self.reste_payer.foreground_color = ACCENT_RED
            else:
                self.reste_payer.foreground_color = ACCENT_GREEN
        except ValueError:
            self.reste_payer.text = "0"

    def _generer_txt(self, commande_id, montant_verse, reste, mode_paiement, numero_cheque=""):
        if not os.path.exists("factures"):
            os.makedirs("factures")
        fn = f"factures/facture_{commande_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(fn, "w", encoding="utf-8") as f:
            f.write(f"FACTURE N° {commande_id}\n")
            f.write(f"Client: {self.client_spinner.text}\n\n")
            for p in self.produits_commandes:
                f.write(f"{p['nom']} x{p['quantite']} = {p['total']:,.0f} Ar\n")
            f.write(f"\nTotal: {self.total_commande:,.0f} Ar\n")
            f.write(f"Montant versé: {montant_verse:,.0f} Ar\n")
            f.write(f"Reste à payer: {reste:,.0f} Ar\n")
            f.write(f"Mode de paiement: {mode_paiement}\n")
            if numero_cheque:
                f.write(f"N° Chèque: {numero_cheque}\n")

    def reset_commande(self, instance):
        self.produits_commandes = []
        self.total_commande = 0
        if self.table_commande:
            enfants = list(self.table_commande.children)
            nb = len(self.HEADERS_COMMANDE)
            for e in (enfants[:-nb] if len(enfants) > nb else []):
                self.table_commande.remove_widget(e)

        self.lbl_total.text = '0'
        self.lbl_count_commande.text = 'Produits commandés  -  0 article(s)'

        self.client_spinner.text = 'Choisir un client'
        self.produit_spinner.text = 'Choisir un produit'
        self.prix_vente_client.text = ''
        self.quantite.text = '1'
        self.montant_verse.text = '0'
        self.reste_payer.text = '0'
        self.mode_paiement.text = 'Espèce'
        self.numero_cheque.text = ''

        self.numero_cheque.opacity = 0
        self.numero_cheque.disabled = True

        if self.client_details:
            self.client_details.text = ""

    def show_message(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message, color=TEXT_WHITE))
        btn = Button(text="OK", size_hint=(1, None), height=35,
                     background_normal="", background_color=ACCENT)
        popup = Popup(title=title, content=content, size_hint=(0.78, 0.32))
        btn.bind(on_release=popup.dismiss)
        content.add_widget(btn)
        popup.open()

    def on_mode_paiement_change(self, spinner, text):
        if text == "Chèque":
            self.numero_cheque.opacity = 1
            self.numero_cheque.disabled = False
        else:
            self.numero_cheque.opacity = 0
            self.numero_cheque.disabled = True
            self.numero_cheque.text = ""