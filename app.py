import streamlit as st
import os
import json
import sqlite3
import tempfile
from dotenv import load_dotenv
from fpdf import FPDF
from datetime import date
from openai import OpenAI

# --- Variables d’environnement ---
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# --- Config Streamlit ---
st.set_page_config(page_title="Chatbot Invest Together", page_icon="🤖")
st.title("🤖 Assistant IA – Invest Together")

st.markdown("""
Bienvenue sur le chatbot intelligent d’Invest Together.  
Posez vos questions sur :
- Comment soumettre un projet  
- Comment investir dans un projet  
- Générer un contrat personnalisé  
- Gestion des litiges  
- Impact social ou environnemental
""")

# --- Génération du contrat PDF ---
def generer_pdf_contrat_perso(type_contrat, investisseur, porteur, projet, montant, date_sig):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    if type_contrat == "financement":
        texte = f"""
CONTRAT DE FINANCEMENT PARTICIPATIF

Investisseur : {investisseur}
Porteur de projet : {porteur}
Projet financé : {projet}
Montant investi : {montant} GNF
Date de signature : {date_sig}

Engagements :
- Utilisation transparente des fonds.
- Reddition de comptes régulière.
- Règlement des litiges selon la loi guinéenne.
"""
    elif type_contrat == "partenariat":
        texte = f"""
CONTRAT DE PARTENARIAT

Entre : {investisseur} et {porteur}
Objet : Projet {projet}
Montant engagé : {montant} GNF
Date : {date_sig}

Engagements :
- Partage équitable des responsabilités.
- Respect des engagements contractuels.
"""
    elif type_contrat == "vente":
        texte = f"""
CONTRAT DE VENTE

Vendeur : {porteur}
Acheteur : {investisseur}
Projet : {projet}
Montant : {montant} GNF
Date de vente : {date_sig}

Le vendeur cède l’intégralité du projet au prix convenu.
"""
    else:
        texte = "Type de contrat invalide."

    for ligne in texte.strip().split('\n'):
        pdf.multi_cell(0, 10, ligne.encode('latin-1', 'replace').decode('latin-1'))

    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_pdf.name)
    return tmp_pdf.name

# --- FAQ ---
def charger_faq():
    try:
        with open("faq.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

faq_data = charger_faq()

def chercher_reponse_faq(question):
    question = question.lower().strip()
    for item in faq_data:
        for q in item["question"]:
            if q.lower() in question:
                return item["answer"]
    return None

# --- Historique DB ---
def enregistrer_message(role, contenu):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS messages (role TEXT, content TEXT)")
    try:
        c.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, contenu))
    except:
        c.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, contenu.encode('utf-8', 'replace').decode('utf-8')))
    conn.commit()
    conn.close()

# --- États Session ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "Tu es un assistant IA pour la plateforme Invest Together en Guinée."}]
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None

# --- Entrée utilisateur ---
user_input = st.chat_input("Pose ta question ici...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    enregistrer_message("user", user_input)

    if "contrat" in user_input.lower():
        msg = "📅 **Remplissez ce formulaire pour créer un contrat personnalisé :**"
        st.session_state.messages.append({"role": "assistant", "content": msg})
        enregistrer_message("assistant", msg)
        st.session_state.show_form = True
    else:
        faq = chercher_reponse_faq(user_input)
        if faq:
            msg = faq
        else:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.messages
            )
            msg = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": msg})
        enregistrer_message("assistant", msg)

# --- Affichage du chat ---
for m in st.session_state.messages[1:]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- Formulaire générateur de contrat ---
if st.session_state.show_form:
    with st.chat_message("assistant"):
        with st.form("formulaire_contrat"):
            st.markdown("💼 **Remplissez ce formulaire pour créer un contrat personnalisé :**")
            type_contrat = st.selectbox("Type de contrat", ["financement", "partenariat", "vente"])
            investisseur = st.text_input("Nom de l'investisseur")
            porteur = st.text_input("Nom du porteur de projet")
            projet = st.text_input("Nom du projet")
            montant = st.text_input("Montant investi (en GNF)")
            date_sig = st.date_input("Date de signature", value=date.today())
            submit = st.form_submit_button("📄 Générer le contrat")

        if submit:
            st.session_state.pdf_path = generer_pdf_contrat_perso(
                type_contrat, investisseur, porteur, projet, montant, date_sig
            )
            st.success("✅ Contrat généré ! Cliquez ci-dessous pour le télécharger 👇")

# --- Bouton de téléchargement ---
if st.session_state.pdf_path:
    with st.chat_message("assistant"):
        with open(st.session_state.pdf_path, "rb") as f:
            st.download_button("📥 Télécharger le contrat (PDF)", f, file_name="contrat_invest_together.pdf", mime="application/pdf")

# --- Liens utiles ---
st.markdown("""
---
📁 **Modèles disponibles :**  
👉 [https://investogether.net/bibliotheque](https://investogether.net/bibliotheque)

📘 **Guide complet & FAQ :**  
👉 [https://investogether.net](https://investogether.net)
""")
