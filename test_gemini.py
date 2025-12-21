
from dotenv import load_dotenv
import os
from ai_classifier import analyze_with_gemini
from server import SECTOR_CONFIG

# Load env vars
load_dotenv()

# Check for Key
key = os.environ.get("GEMINI_API_KEY")
if not key:
    print("❌ Erreur : Clé GEMINI_API_KEY introuvable dans le fichier .env")
    exit(1)
else:
    print(f"✅ Clé trouvée : {key[:5]}...")

# Test Case
company = "Doctolib"
print(f"\n🔍 Test de l'IA avec l'entreprise : '{company}'...")

sector, detail, score = analyze_with_gemini(company, list(SECTOR_CONFIG.keys()))

if sector:
    print(f"✅ Succès ! Gemini a trouvé :")
    print(f"   - Secteur : {sector}")
    print(f"   - Détail : {detail}")
else:
    print("❌ Échec : Gemini n'a rien trouvé (ou erreur).")
