# pdf_generator.py
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# Définition du format NB-80 (80mm de large)
NB80_WIDTH = 80 * mm
NB80_HEIGHT = 297 * mm


def generer_pdf_facture(commande_id, client_nom, client_info,
                        produits, total, avance, reste, mode_paiement, numero_cheque, date_str):
    """Génère une facture PDF adaptée au papier NB-80 (80mm)"""
    try:
        # Vérifier si le dossier factures existe
        factures_dir = "factures"
        if not os.path.exists(factures_dir):
            os.makedirs(factures_dir)

        # Construire le chemin absolu pour le fichier
        nom_fichier = f"facture_{commande_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filename = os.path.join(factures_dir, nom_fichier)

        # Obtenir le chemin absolu
        chemin_absolu = os.path.abspath(filename)

        print(f"DEBUG - Génération PDF: {chemin_absolu}")

        doc = SimpleDocTemplate(
            chemin_absolu,
            pagesize=(NB80_WIDTH, NB80_HEIGHT),
            rightMargin=5*mm, leftMargin=5*mm,
            topMargin=8*mm, bottomMargin=5*mm
        )

        styles = getSampleStyleSheet()

        # Styles pour l'en-tête
        style_entreprise = ParagraphStyle(
            'entreprise',
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#0D47A1'),
            alignment=TA_LEFT,
            spaceAfter=2,
            leading=10
        )

        style_entreprise_info = ParagraphStyle(
            'entreprise_info',
            fontSize=7,
            fontName='Helvetica',
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=2,
            leading=9
        )

        style_facture_num = ParagraphStyle(
            'fnum',
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#0D47A1'),
            alignment=TA_RIGHT,
            spaceAfter=2,
            leading=14
        )

        style_date = ParagraphStyle(
            'fdate',
            fontSize=7,
            fontName='Helvetica',
            alignment=TA_RIGHT,
            spaceAfter=4
        )

        style_section = ParagraphStyle(
            'section',
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#0D47A1'),
            spaceBefore=4,
            spaceAfter=3
        )

        style_normal = ParagraphStyle(
            'normal_custom',
            fontSize=8,
            fontName='Helvetica',
            textColor=colors.black,
            spaceAfter=1,
            leading=10
        )

        style_small = ParagraphStyle(
            'small',
            fontSize=7,
            fontName='Helvetica',
            textColor=colors.black,
            leading=9
        )

        style_total_ligne = ParagraphStyle(
            'total_ligne',
            fontSize=9,
            fontName='Helvetica-Bold',
            alignment=TA_RIGHT,
            spaceAfter=0,
            leading=10
        )

        story = []

        # ── EN-TÊTE AVEC MARGE ──
        story.append(Spacer(1, 2*mm))

        header_data = [
            [
                Paragraph("<b>E &amp; N ENTREPRISE</b>", style_entreprise),
                Paragraph(f"<b>FACTURE N° {commande_id}</b>", style_facture_num)
            ],
            [
                Paragraph("Matériaux de Construction", style_entreprise_info),
                Paragraph(f"Date : {date_str}", style_date)
            ],
            [
                Paragraph("Vente en gros et détail", style_entreprise_info),
                Paragraph("", style_date)
            ],
            [
                Paragraph("Contact : 034 41 463 65", style_entreprise_info),
                Paragraph("", style_date)
            ]
        ]

        header_table = Table(header_data, colWidths=[35*mm, 32*mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(header_table)

        story.append(Spacer(1, 3*mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 3*mm))

        # INFOS CLIENT
        adresse = client_info.get('adresse', '') if client_info.get('adresse') else ''
        nif = client_info.get('nif', '') if client_info.get('nif') else ''
        stat = client_info.get('stat', '') if client_info.get('stat') else ''
        contact = client_info.get('contact', '') if client_info.get('contact') else ''

        client_data = [
            [Paragraph(f"<b>Client :</b> {client_nom}", style_normal)],
            [Paragraph(f"Adresse : {adresse}", style_small) if adresse else Paragraph("", style_small)],
            [Paragraph(f"Contact : {contact}", style_small) if contact else Paragraph("", style_small)],
        ]

        if nif or stat:
            client_data.insert(2, [Paragraph(f"NIF : {nif} | STAT : {stat}", style_small)])

        t_client = Table(client_data, colWidths=[70*mm])
        t_client.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EEF2FF')),
            ('GRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
            ('PADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t_client)
        story.append(Spacer(1, 3*mm))

        # TABLEAU PRODUITS
        story.append(Paragraph("DETAIL COMMANDE", style_section))
        story.append(Spacer(1, 2*mm))

        prod_data = [["Designation", "Qté", "Prix", "Montant"]]

        for p in produits:
            nom = p.get('nom', '')
            if len(nom) > 25:
                nom = nom[:22] + "..."

            prod_data.append([
                Paragraph(nom, style_small),
                Paragraph(str(p.get('quantite', '')),
                         ParagraphStyle('', alignment=TA_CENTER, fontSize=7)),
                Paragraph(f"{float(p.get('prix_unitaire', 0)):,.0f}",
                         ParagraphStyle('', alignment=TA_RIGHT, fontSize=7)),
                Paragraph(f"{float(p.get('total', 0)):,.0f}",
                         ParagraphStyle('', alignment=TA_RIGHT, fontSize=7))
            ])

        col_w = [32*mm, 8*mm, 14*mm, 16*mm]
        t_prod = Table(prod_data, colWidths=col_w)
        t_prod.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (-1,0),  colors.HexColor('#0D47A1')),
            ('TEXTCOLOR',   (0,0), (-1,0),  colors.white),
            ('FONTNAME',    (0,0), (-1,0),  'Helvetica-Bold'),
            ('FONTSIZE',    (0,0), (-1,0),  7),
            ('ALIGN',       (0,0), (-1,0),  'CENTER'),
            ('VALIGN',      (0,0), (-1,0),  'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1),
             [colors.white, colors.HexColor('#F5F5F5')]),
            ('FONTSIZE',    (0,1), (-1,-1), 7),
            ('ALIGN',       (1,1), (1,-1), 'CENTER'),
            ('ALIGN',       (2,1), (3,-1), 'RIGHT'),
            ('ALIGN',       (0,1), (0,-1), 'LEFT'),
            ('VALIGN',      (0,1), (-1,-1), 'TOP'),
            ('GRID',        (0,0), (-1,-1), 0.3, colors.lightgrey),
            ('PADDING',     (0,0), (-1,-1), 3),
        ]))
        story.append(t_prod)
        story.append(Spacer(1, 3*mm))

        # TOTAUX
        story.append(Paragraph(f"<b>TOTAL :</b> {total:,.0f} Ar", style_total_ligne))
        story.append(Paragraph(f"<b>MONTANT VERSE :</b> {avance:,.0f} Ar", style_total_ligne))

        if mode_paiement == "Chèque" and numero_cheque:
            story.append(Paragraph(f"<b>MODE DE PAIEMENT :</b> {mode_paiement} - N° {numero_cheque}",
                                   ParagraphStyle('mode_style', fontSize=9,
                                                 fontName='Helvetica-Bold',
                                                 alignment=TA_RIGHT,
                                                 spaceAfter=0)))
        else:
            story.append(Paragraph(f"<b>MODE DE PAIEMENT :</b> {mode_paiement}",
                                   ParagraphStyle('mode_style', fontSize=9,
                                                 fontName='Helvetica-Bold',
                                                 alignment=TA_RIGHT,
                                                 spaceAfter=0)))

        if reste > 0:
            story.append(Paragraph(f"<b>RESTE A PAYER :</b> {reste:,.0f} Ar",
                                   ParagraphStyle('reste_style', fontSize=9,
                                                 fontName='Helvetica-Bold',
                                                 textColor=colors.HexColor('#B71C1C'),
                                                 alignment=TA_RIGHT,
                                                 spaceAfter=0)))
        else:
            story.append(Paragraph(f"<b>RESTE A PAYER :</b> {reste:,.0f} Ar",
                                   ParagraphStyle('reste_style', fontSize=9,
                                                 fontName='Helvetica-Bold',
                                                 textColor=colors.HexColor('#1B5E20'),
                                                 alignment=TA_RIGHT,
                                                 spaceAfter=0)))

        story.append(Spacer(1, 3*mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black))
        story.append(Spacer(1, 3*mm))

        # SECTION SIGNATURE
        signature_data = [
            ["", "Cachet / Signature"],
        ]

        t_signature = Table(signature_data, colWidths=[35*mm, 35*mm])
        t_signature.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
            ('FONTSIZE', (0,0), (-1,-1), 7),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('PADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(t_signature)

        story.append(Spacer(1, 5*mm))

        story.append(Paragraph("-" * 37,
                               ParagraphStyle('cut', fontSize=7, alignment=TA_CENTER)))

        doc.build(story)

        # Retourner le chemin absolu
        return chemin_absolu

    except ImportError:
        return None
    except Exception as e:
        print(f"Erreur PDF: {e}")
        return None