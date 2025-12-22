import os
import json
from groq import Groq
import time

# Configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# --- CHOIX DU MODÈLE ---
# Option 1: "llama-3.3-70b-versatile" (Défaut)
#   - INTELLIGENCE : Top (Niveau GPT-4)
#   - QUOTA : 1,000 requêtes / jour (environ 40/heure en continu)
#   - USAGE : Recommandé pour la qualité de classification.

# Option 2: "llama-3.1-8b-instant"
#   - INTELLIGENCE : Bonne (Suffisant pour des cas simples)
#   - QUOTA : 14,400 requêtes / jour
#   - USAGE : À utiliser si vous traitez des fichiers EXCEL de 5000+ lignes d'un coup.

GROQ_MODEL = "llama-3.1-8b-instant" 

def analyze_with_groq(company_name, sectors_list, custom_sectors=None):
    """
    Uses Groq API (Llama 3) to determine the best sector for a company.
    """
    if not GROQ_API_KEY:
        print("❌ ERREUR: La clé GROQ_API_KEY est manquante dans les variables d'environnement !")
        return None, "Clé API Manquante", 0

    client = Groq(api_key=GROQ_API_KEY)
    
    all_sectors = sectors_list + (custom_sectors if custom_sectors else [])
    sectors_str = ", ".join([f'"{s}"' for s in all_sectors])

    # Prompt optimisé pour Llama 3
    prompt = f"""
    Tu es un expert en classification d'entreprises.
    Identifie le secteur d'activité de l'entreprise suivante : "{company_name}".
    
    Tu DOIS choisir le secteur le plus pertinent PARMI cette liste stricte :
    [{sectors_str}]

    Si tu ne trouves aucune correspondance ou que l'entreprise n'existe pas, réponds "Unknown".

    Réponds UNIQUEMENT au format JSON strict avec les clés "sector", "confidence", "reasoning".
    Exemple: {{"sector": "Technology", "confidence": "High", "reasoning": "Known tech company"}}
    """

    try:
        # Llama 3 supports json_object response format
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "Tu es un assistant JSON strict. Tu réponds uniquement en JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            # response_format={"type": "json_object"} # Activé pour robustesse
             # Note: Si le modèle 70b a du mal avec le mode JSON strict, on peut le retirer, mais c'est généralement mieux.
        )
        
        content = completion.choices[0].message.content
        
        # Nettoyage basique (au cas où le modèle est bavard)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        result = json.loads(content)
        sector = result.get("sector")
        
        # Validation
        if sector and sector != "Unknown" and sector in all_sectors:
            return sector, f"Groq Llama 3 ({result.get('confidence')})", 100
        else:
            return None, "Groq: Incertain / Hors Liste", 0

    except Exception as e:
        print(f"Groq Error: {e}")
        return None, f"Erreur Groq: {str(e)}", 0
