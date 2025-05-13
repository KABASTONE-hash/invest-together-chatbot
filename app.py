import streamlit as st
import os
import json
import sqlite3
from dotenv import load_dotenv
from openai import OpenAI

# --- Chargement des variables d'environnement ---
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    st.error("Clé API OpenAI manquante. Crée un fichier .env avec OPENAI_API_KEY=ta_clé.")
    st.stop()

client = OpenAI(api_key=openai_api_key)

st.set_page_config(page_title="Chatbot Invest Together", page_icon="🤖")
st.title("🤖 Assistant IA – Invest Together")

st.markdown("""
Bienvenue sur le chatbot intelligent d’Invest Together. 
Posez vos questions sur :
- Comment soumettre un projet
- Comment investir dans un projet
- Les documents nécessaires
- Les étapes à suivre
- La sécurité des transactions
""")

# --- Chargement de la FAQ ---
def charger_faq():
    try:
        with open("faq.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

faq_data = charger_faq()

def chercher_reponse_faq(question):
    for item in faq_data:
        if item["question"].lower() in question.lower():
            return item["answer"]
    return None

# --- Connexion à SQLite ---
def enregistrer_message(role, contenu):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (role TEXT, content TEXT)''')
    c.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, contenu))
    conn.commit()
    conn.close()

# --- Historique de session ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Tu es un assistant pour une plateforme de financement participatif en Guinée. Tu aides les utilisateurs (investisseurs ou porteurs de projet) à comprendre la plateforme Invest Together avec un langage très simple."}
    ]

# --- Entrée utilisateur ---
user_input = st.chat_input("Pose ta question ici...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    enregistrer_message("user", user_input)

    with st.spinner("L'IA réfléchit..."):
        reponse_faq = chercher_reponse_faq(user_input)
        if reponse_faq:
            assistant_message = reponse_faq
        else:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.messages
            )
            assistant_message = response.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
    enregistrer_message("assistant", assistant_message)

# --- Affichage de l'historique ---
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
