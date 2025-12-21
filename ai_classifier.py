
import os
import google.generativeai as genai
import time
import json

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY is not set.")

def analyze_with_gemini(company_name, sectors_list, custom_sectors=None):
    """
    Uses Gemini 1.5 Flash to determine the best sector for a company.
    Includes rate limiting to respect the free tier (15 RPM).
    """
    if not GEMINI_API_KEY:
        return None, "Clé API Manquante", 0

    # Rate limiting: 4 seconds sleep = 15 RPM max
    time.sleep(4.0)

    all_sectors = sectors_list + (custom_sectors if custom_sectors else [])
    sectors_str = ", ".join([f'"{s}"' for s in all_sectors])

    prompt = f"""
    Tu es un expert en classification d'entreprises.
    Identifie le secteur d'activité de l'entreprise suivante : "{company_name}".
    
    Tu DOIS choisir le secteur le plus pertinent PARMI cette liste stricte :
    [{sectors_str}]

    Si tu ne trouves aucune correspondance ou que l'entreprise n'existe pas, réponds "Unknown".

    Réponds UNIQUEMENT au format JSON :
    {{
        "sector": "Nom du secteur choisi",
        "confidence": "Haut/Moyen/Bas",
        "reasoning": "Courte justification"
    }}
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        result = json.loads(response.text)
        sector = result.get("sector")
        
        if sector and sector != "Unknown" and sector in all_sectors:
            return sector, f"Gemini 1.5 Flash ({result.get('confidence')})", 100
        else:
            return None, "Gemini: Incertain / Hors Liste", 0

    except Exception as e:
        print(f"Gemini Error: {e}")
        return None, f"Erreur Gemini: {str(e)}", 0
