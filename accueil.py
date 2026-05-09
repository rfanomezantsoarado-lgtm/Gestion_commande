from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle, Rectangle


MENU_WIDTH = 280


class MenuItemButton(BoxLayout):
    """
    Item de menu : fond coloré + icône à gauche + texte à droite.
    Hérite de BoxLayout pour que le DropDown accepte size_hint_y=None / height.
    """
    def __init__(self, texte, icone, callback, **kwargs):
        super().__init__(
            orientation="horizontal",
            spacing=14,
            padding=[16, 0, 10, 0],
            size_hint_y=None,
            height=56,
            **kwargs
        )

        # Fond sombre
        with self.canvas.before:
            Color(0.07, 0.10, 0.22, 0.5)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda inst, v: setattr(self._bg, 'pos', v),
            size=lambda inst, v: setattr(self._bg, 'size', v)
        )

        # Icône
        icon = Image(
            source=icone,
            size_hint=(None, None),
            size=(28, 28),
            pos_hint={"center_y": 0.5}
        )

        # Texte
        lbl = Label(
            text=texte,
            color=(0.88, 0.93, 1, 1),
            font_size=16,
            halign="left",
            valign="middle",
            size_hint_x=1
        )
        lbl.bind(size=lambda inst, v: setattr(inst, "text_size", v))

        self.add_widget(icon)
        self.add_widget(lbl)

        # Clic sur tout le widget
        self.bind(on_touch_down=lambda inst, touch: callback(touch)
                  if inst.collide_point(*touch.pos) else None)


class AccueilScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = FloatLayout()

        # ── FOND ──────────────────────────────────────────
        fond = Image(
            source="images/background.png",
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0}
        )
        layout.add_widget(fond)

        # ── OVERLAY SOMBRE ────────────────────────────────
        overlay = FloatLayout(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        with overlay.canvas.before:
            Color(0, 0, 0, 0.30)
            self._overlay_rect = Rectangle(pos=overlay.pos, size=overlay.size)
        overlay.bind(
            pos=lambda inst, v: setattr(self._overlay_rect, 'pos', v),
            size=lambda inst, v: setattr(self._overlay_rect, 'size', v)
        )
        layout.add_widget(overlay)

        # ── BARRE HAUTE ───────────────────────────────────
        top_bar = FloatLayout(
            size_hint=(1, 0.13),
            pos_hint={"x": 0, "top": 1}
        )
        with top_bar.canvas.before:
            Color(0.05, 0.08, 0.18, 0.92)
            self._bar_rect = Rectangle(pos=top_bar.pos, size=top_bar.size)
        top_bar.bind(
            pos=lambda inst, v: setattr(self._bar_rect, 'pos', v),
            size=lambda inst, v: setattr(self._bar_rect, 'size', v)
        )
        layout.add_widget(top_bar)

        # ── TITRE ─────────────────────────────────────────
        app_titre = Label(
            text="BIENVENUE",
            font_size=22,
            bold=True,
            color=(0.9, 0.95, 1, 1),
            size_hint=(0.55, 0.13),
            pos_hint={"x": 0.03, "top": 1}
        )
        layout.add_widget(app_titre)

        # ── BOUTON MENU ───────────────────────────────────
        self.menu_button = Button(
            text="MENU",
            size_hint=(0.36, 0.08),
            pos_hint={"right": 0.97, "top": 0.97},
            font_size=16,
            bold=True,
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1)
        )
        with self.menu_button.canvas.before:
            Color(0.08, 0.45, 0.82, 1)
            self._btn_rect = RoundedRectangle(
                pos=self.menu_button.pos,
                size=self.menu_button.size,
                radius=[8]
            )
        self.menu_button.bind(
            pos=lambda inst, v: setattr(self._btn_rect, 'pos', v),
            size=lambda inst, v: setattr(self._btn_rect, 'size', v)
        )

        # ── MENU DÉROULANT ────────────────────────────────
        self.dropdown = DropDown(auto_width=False, width=MENU_WIDTH)

        menus = [
            #("Accueil",     "images/home.png",     "accueil"),
            ("Clients",     "images/user.png",   "clients"),
            ("Produits",    "images/produit.png",  "produits"),
            ("Commande",    "images/commande.png", "commande"),
            ("Historique", "images/facturation.png",  "historique_commande"),
        ]

        for texte, icone, cible in menus:

            def make_callback(val, dest):
                def cb(touch):
                    self.dropdown.select((val, dest))
                return cb

            item = MenuItemButton(
                texte=texte,
                icone=icone,
                callback=make_callback(texte, cible),
                width=MENU_WIDTH
            )
            self.dropdown.add_widget(item)

        self.menu_button.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=self.menu_action)
        layout.add_widget(self.menu_button)

        # ── PIED DE PAGE ──────────────────────────────────
        footer = Label(
            text="© 2026  EN App  —  v1.0",
            font_size=11,
            color=(0.5, 0.6, 0.75, 0.8),
            size_hint=(1, 0.05),
            pos_hint={"center_x": 0.5, "y": 0.01}
        )
        layout.add_widget(footer)

        self.add_widget(layout)

    # ── ACTION MENU ───────────────────────────────────────
    def menu_action(self, instance, value):
        texte, dest = value
        self.menu_button.text = texte
        if dest in ("accueil", "clients", "produits", "commande", "historique_commande"):
            self.manager.current = dest

    # ── AJOUTER CETTE MÉTHODE POUR RÉINITIALISER LE MENU ──
    def on_enter(self):
        """Appelé quand on revient à l'écran d'accueil"""
        # Réinitialiser le texte du bouton menu à "MENU"
        self.menu_button.text = "MENU"

    # ── AJOUTER CETTE MÉTHODE POUR NETTOYER ───────────────
    def on_pre_leave(self):
        """Appelé quand on quitte l'écran d'accueil"""
        # Fermer le dropdown s'il est ouvert
        if self.dropdown.attach_to:
            self.dropdown.dismiss()