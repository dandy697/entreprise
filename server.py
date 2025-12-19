from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import time
import re
from urllib.parse import urlparse

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# --- Configuration ---
SECTOR_CONFIG = {
    "Agriculture / Livestock / Seafood": {
        "naf_prefixes": ["01", "02", "03"],
        "keywords": ["agriculture", "élevage", "pêche", "agricole", "ferme", "bio", "tracteur", "champs", "vigne", "viticulture", "horticulture", "maraichage", "bétail", "aquaculture", "farming", "livestock", "seafood", "crops"]
    },
    "Banking": {
        "naf_prefixes": ["641"],
        "keywords": ["banque", "crédit", "bancaire", "épargne", "financement", "prêt", "compte", "livret", "cb", "fonds", "bank", "banking", "loan", "credit", "finance", "wealth"]
    },
    "Chemicals": {
        "naf_prefixes": ["20"],
        "keywords": ["chimie", "laboratoire", "molécules", "réactif", "polymère", "plastique", "chimique", "petrochemical", "chemicals", "chemistry", "lab", "laboratory"]
    },
    "Communication / Media & Entertainment / Telecom": {
        "naf_prefixes": ["59", "60", "61", "63"],
        "keywords": ["télécom", "média", "publicité", "fibre", "internet", "presse", "journal", "tv", "radio", "marketing", "agence", "communication", "entertainment", "telecom", "broadcasting", "advertising", "media"]
    },
    "Agri-food / Beverages": {
        "naf_prefixes": ["10", "11", "01", "463"],
        "keywords": ["agroalimentaire", "food", "beverage", "boisson", "agriculture", "vin", "champagne", "spiritueux", "traiteur", "viande", "lait", "bio", "pernod"]
    },
    "Retail": {
        "naf_prefixes": ["47", "45", "46", "464"],
        "keywords": ["commerce", "retail", "distribution", "magasin", "boutique", "vente", "e-commerce", "wholesaler", "supermarket", "fashion", "mode", "luxe", "parfum", "cosmétique", "longchamp"]
    },
    "Luxury / Fashion": {
        "naf_prefixes": ["14", "15"],
        "keywords": ["luxe", "fashion", "haute couture", "mode", "maroquinerie", "joaillerie", "parfum", "cosmétique", "beaute", "beauty"]
    },
    "Construction / Real Estate": {
        "naf_prefixes": ["41", "42", "43", "68", "711", "681", "682", "683"],
        "keywords": ["btp", "construction", "bâtiment", "travaux", "chantier", "rénovation", "gros oeuvre", "maçonnerie", "architecte", "immobilier", "promoteur", "building", "real estate", "foncière", "agence immobilière"]
    },
    "Consulting / IT Services": {
        "naf_prefixes": ["62", "702", "69", "70", "71", "73", "74"],
        "keywords": ["conseil", "consulting", "esn", "stratégie", "audit", "expertise", "ingénierie", "management", "digital", "transformation", "it services", "système d'information", "data", "advisory", "capgemini"]
    },
    "Human Resources": {
        "naf_prefixes": ["78"],
        "keywords": ["interim", "rh", "ressources humaines", "recrutement", "chasseur de tête", "talent", "portage salarial", "manpower", "adecco", "randstad"]
    },
    "Entertainment / Media": {
        "naf_prefixes": ["59", "60", "90", "91", "93"],
        "keywords": ["media", "entertainment", "divertissement", "cinéma", "télévision", "production", "presse", "journalisme", "culture", "loisir", "parc d'attraction", "musée", "spectacle", "disney", "netflix"]
    },
    "Hotels / Restaurants": {
        "naf_prefixes": ["55", "56"],
        "keywords": ["hotel", "restauran", "hébergement", "tourisme", "café", "bar", "traiteur", "restauration", "hospitality"]
    },
    "Finance / Insurance": {
        "naf_prefixes": ["64", "65", "66"],
        "keywords": ["banque", "assurance", "finance", "investissement", "gestion d'actifs", "courtier", "mutuelle", "crédit", "bank", "insurance", "invest", "wealth"]
    },
    "Manufacturing / Industry": {
        "naf_prefixes": ["20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33"],
        "keywords": ["industrie", "manufacturing", "usine", "production", "fabrication", "électronique", "mécanique", "chimie", "pharma", "automobile", "aéronautique", "industry"]
    },
    "Transport / Logistics": {
        "naf_prefixes": ["49", "50", "51", "52", "53"],
        "keywords": ["transport", "logistique", "fret", "livraison", "messagerie", "entrepôt", "supply chain", "shipping", "transit", "colis"]
    },
    "Energies / Utilities": {
        "naf_prefixes": ["35", "36", "37", "38", "39"],
        "keywords": ["énergie", "électricité", "gaz", "eau", "déchets", "environnement", "recyclage", "solaire", "éolien", "nucléaire", "oil", "petrol"]
    },
    "Healthcare / Medical Services": {
        "naf_prefixes": ["86", "87", "88", "21"],
        "keywords": ["santé", "clinique", "hôpital", "soins", "médecin", "infirmier", "ehpad", "médical", "chirurgie", "patient", "healthcare", "medical", "hospital", "clinic", "care", "doctor"]
    },
    "Hotels / Restaurants": {
        "naf_prefixes": ["55", "56"],
        "keywords": ["hôtel", "restaurant", "tourisme", "hébergement", "camping", "voyage", "traiteur", "bar", "café", "brasserie", "cuisine", "hotel", "hospitality", "tourism", "restaurant", "catering"]
    },
    "Insurance / Mutual Health Insurance": {
        "naf_prefixes": ["65"],
        "keywords": ["assurance", "mutuelle", "courtier", "protection", "prévoyance", "sinistre", "risque", "assureur", "insurance", "underwriting", "broker", "coverage"]
    },
    "Luxury": {
        "naf_prefixes": [],
        "keywords": ["luxe", "prestige", "haute couture", "joaillerie", "exception", "maroquinerie", "palace", "luxury", "fashion", "jewelry", "premium", "high-end"]
    },
    "Manufacturing / Industry": {
        "naf_prefixes": ["13", "14", "15", "16", "17", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32"],
        "keywords": ["industrie", "usine", "fabrication", "mécanique", "métallurgie", "plasturgie", "assemblage", "production", "machine", "outil", "industriel", "manufacturing", "industry", "factory", "plant", "metal", "machinery", "tesla", "ev", "electric vehicle", "voiture", "automotive"]
    },
    "Not For Profit": {
        "naf_prefixes": ["94"],
        "keywords": ["association", "ong", "fondation", "bénévolat", "caritatif", "solidaire", "général", "non-profit", "charity", "foundation", "ngo"]
    },
    "Pharmaceutics": {
        "naf_prefixes": ["21"],
        "keywords": ["pharmacie", "médicament", "biotech", "laboratoire", "vaccin", "recherche", "molécule", "thérapie", "pharmaceutical", "pharma", "drug", "biotechnology", "medicine"]
    },
    "Public administration & government": {
        "naf_prefixes": ["84"],
        "keywords": ["administration", "état", "ministère", "service public", "mairie", "collectivité", "préfecture", "government", "public sector", "administration", "municipality"]
    },
    "Retail": {
        "naf_prefixes": ["47", "46", "45"],
        "keywords": ["commerce", "vente", "magasin", "boutique", "retail", "distribution", "e-commerce", "achat", "shop", "store", "supermarket", "mall", "market"]
    },
    "Tech / Software": {
        "naf_prefixes": ["582", "6201", "631", "620"],
        "keywords": ["logiciel", "saas", "tech", "software", "application", "ia", "intelligence artificielle", "cloud", "data", "développement", "web", "app", "cybersecurity", "platform", "technology", "developer", "apple", "iphone", "ios", "mac", "electronics", "smartphone"]
    },
    "Transportation, Logistics & Storage": {
        "naf_prefixes": ["49", "50", "51", "52", "53"],
        "keywords": ["transport", "logistique", "livraison", "fret", "colis", "camion", "train", "avion", "bateau", "supply chain", "entrepôt", "stockage", "transportation", "logistics", "shipping", "freight", "cargo"]
    }
}

NAF_BLACKLIST = ["7010Z", "6420Z"]

# --- Mappings ---
TRANCHE_EFFECTIFS = {
    "NN": "Non renseigné",
    "00": "0 salarié",
    "01": "1 ou 2 salariés",
    "02": "3 à 5 salariés",
    "03": "6 à 9 salariés",
    "11": "10 à 19 salariés",
    "12": "20 à 49 salariés",
    "21": "50 à 99 salariés",
    "22": "100 à 199 salariés",
    "31": "200 à 249 salariés",
    "32": "250 à 499 salariés",
    "41": "500 à 999 salariés",
    "42": "1 000 à 1 999 salariés",
    "51": "2 000 à 4 999 salariés",
    "52": "5 000 à 9 999 salariés",
    "53": "10 000 salariés et plus"
}

# --- GLOBAL STATIC OVERRIDES (Safety Net) ---
GLOBAL_OVERRIDES = {
    "APPLE": {"Secteur": "Tech / Software", "Nom Officiel": "APPLE INC.", "Adresse": "Cupertino, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "TESLA": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "TESLA INC.", "Adresse": "Austin, TX (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "GOOGLE": {"Secteur": "Tech / Software", "Nom Officiel": "ALPHABET INC.", "Adresse": "Mountain View, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "MICROSOFT": {"Secteur": "Tech / Software", "Nom Officiel": "MICROSOFT CORP", "Adresse": "Redmond, WA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "AMAZON": {"Secteur": "Tech / Software", "Nom Officiel": "AMAZON.COM INC", "Adresse": "Seattle, WA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "META": {"Secteur": "Tech / Software", "Nom Officiel": "META PLATFORMS", "Adresse": "Menlo Park, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "FACEBOOK": {"Secteur": "Tech / Software", "Nom Officiel": "META PLATFORMS", "Adresse": "Menlo Park, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "LVMH": {"Secteur": "Luxury / Fashion", "Nom Officiel": "LVMH MOET HENNESSY", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "ORANGE": {"Secteur": "Communication / Media & Entertainment / Telecom", "Nom Officiel": "ORANGE SA", "Adresse": "Issy-les-Moulineaux (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    
    # Tech / Web
    "SPOTIFY": {"Secteur": "Tech / Software", "Nom Officiel": "SPOTIFY TECHNOLOGY", "Adresse": "Stockholm (Sweden)", "Région": "Monde", "Effectif": "5 000+ salariés"},
    "UBER": {"Secteur": "Tech / Software", "Nom Officiel": "UBER TECHNOLOGIES", "Adresse": "San Francisco, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "AIRBNB": {"Secteur": "Tech / Software", "Nom Officiel": "AIRBNB INC.", "Adresse": "San Francisco, CA (USA)", "Région": "Monde", "Effectif": "5 000+ salariés"},
    "NETFLIX": {"Secteur": "Entertainment / Media", "Nom Officiel": "NETFLIX INC.", "Adresse": "Los Gatos, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "NVIDIA": {"Secteur": "Tech / Software", "Nom Officiel": "NVIDIA CORP", "Adresse": "Santa Clara, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    
    # Auto
    "BMW": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "BMW AG", "Adresse": "Munich (Germany)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "MERCEDES": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "MERCEDES-BENZ GROUP", "Adresse": "Stuttgart (Germany)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "TOYOTA": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "TOYOTA MOTOR CORP", "Adresse": "Toyota City (Japan)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "VOLKSWAGEN": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "VOLKSWAGEN AG", "Adresse": "Wolfsburg (Germany)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    
    # Consumer
    "COCA COLA": {"Secteur": "Agri-food / Beverages", "Nom Officiel": "THE COCA-COLA COMPANY", "Adresse": "Atlanta, GA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "PEPSI": {"Secteur": "Agri-food / Beverages", "Nom Officiel": "PEPSICO INC.", "Adresse": "Harrison, NY (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "SAMSUNG": {"Secteur": "Tech / Software", "Nom Officiel": "SAMSUNG ELECTRONICS", "Adresse": "Suwon (South Korea)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "NIKE": {"Secteur": "Retail", "Nom Officiel": "NIKE INC.", "Adresse": "Beaverton, OR (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    
    # Smartphones / Tech Asia
    "XIAOMI": {"Secteur": "Tech / Software", "Nom Officiel": "XIAOMI CORP", "Adresse": "Beijing (China)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "OPPO": {"Secteur": "Tech / Software", "Nom Officiel": "OPPO ELECTRONICS", "Adresse": "Dongguan (China)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "HUAWEI": {"Secteur": "Tech / Software", "Nom Officiel": "HUAWEI TECHNOLOGIES", "Adresse": "Shenzhen (China)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "ONEPLUS": {"Secteur": "Tech / Software", "Nom Officiel": "ONEPLUS TECHNOLOGY", "Adresse": "Shenzhen (China)", "Région": "Monde", "Effectif": "5 000+ salariés"},

    # Retail / Supermarkets (France & Global)
    "CARREFOUR": {"Secteur": "Retail", "Nom Officiel": "CARREFOUR SA", "Adresse": "Massy (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "AUCHAN": {"Secteur": "Retail", "Nom Officiel": "AUCHAN RETAIL", "Adresse": "Croix (France)", "Région": "Hauts-de-France", "Effectif": "10 000+ salariés"},
    "LECLERC": {"Secteur": "Retail", "Nom Officiel": "E.LECLERC", "Adresse": "Ivry-sur-Seine (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "INTERMARCHE": {"Secteur": "Retail", "Nom Officiel": "ITM ENTREPRISES", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "INTERMARCHÉ": {"Secteur": "Retail", "Nom Officiel": "ITM ENTREPRISES", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "LIDL": {"Secteur": "Retail", "Nom Officiel": "LIDL STIFTUNG", "Adresse": "Neckarsulm (Germany)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "ALDI": {"Secteur": "Retail", "Nom Officiel": "ALDI EINKAUF", "Adresse": "Essen (Germany)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "NETTO": {"Secteur": "Retail", "Nom Officiel": "NETTO MARKEN-DISCOUNT", "Adresse": "Germany", "Région": "Monde", "Effectif": "5 000+ salariés"},
    "ACTION": {"Secteur": "Retail", "Nom Officiel": "ACTION B.V.", "Adresse": "Zwaagdijk (Netherlands)", "Région": "Monde", "Effectif": "10 000+ salariés"},

    # Fixes from User Feedback
    "DISNEY": {"Secteur": "Entertainment / Media", "Nom Officiel": "THE WALT DISNEY COMPANY", "Adresse": "Burbank, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "DECATHLON": {"Secteur": "Retail", "Nom Officiel": "DECATHLON SE", "Adresse": "Villeneuve-d'Ascq (France)", "Région": "Hauts-de-France", "Effectif": "10 000+ salariés"},
    "LONGCHAMP": {"Secteur": "Luxury / Fashion", "Nom Officiel": "LONGCHAMP SAS", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "1 000+ salariés"},
    "MONOPRIX": {"Secteur": "Retail", "Nom Officiel": "MONOPRIX", "Adresse": "Clichy (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "PERNOD RICARD": {"Secteur": "Agri-food / Beverages", "Nom Officiel": "PERNOD RICARD", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "PFIZER": {"Secteur": "Pharmaceutics", "Nom Officiel": "PFIZER INC.", "Adresse": "New York, NY (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "LA POSTE": {"Secteur": "Transport / Logistics", "Nom Officiel": "LA POSTE", "Adresse": "Issy-les-Moulineaux (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "GROUPE LA POSTE": {"Secteur": "Transport / Logistics", "Nom Officiel": "LA POSTE", "Adresse": "Issy-les-Moulineaux (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "TDF": {"Secteur": "Communication / Media & Entertainment / Telecom", "Nom Officiel": "TDF", "Adresse": "Montrouge (France)", "Région": "Île-de-France", "Effectif": "1 000+ salariés"},
    "SYMBIO": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "SYMBIO", "Adresse": "Vénissieux (France)", "Région": "Auvergne-Rhône-Alpes", "Effectif": "500+ salariés"},
    "APRIL": {"Secteur": "Insurance / Mutual Health Insurance", "Nom Officiel": "APRIL", "Adresse": "Lyon (France)", "Région": "Auvergne-Rhône-Alpes", "Effectif": "1 000+ salariés"},
    "SAFRAN": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "SAFRAN SA", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "VISIATIV": {"Secteur": "Tech / Software", "Nom Officiel": "VISIATIV", "Adresse": "Charbonnières-les-Bains (France)", "Région": "Auvergne-Rhône-Alpes", "Effectif": "1 000+ salariés"},
    "AMOOBI": {"Secteur": "Tech / Software", "Nom Officiel": "AMOOBI", "Adresse": "N/A (International)", "Région": "Monde", "Effectif": "10-50 salariés"},
    "SAFRAN AERO BOOSTERS": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "SAFRAN AERO BOOSTERS", "Adresse": "Herstal (Belgium)", "Région": "Monde", "Effectif": "1 000+ salariés"},
    "SAFRAN AERO BOSOTERS": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "SAFRAN AERO BOOSTERS", "Adresse": "Herstal (Belgium)", "Région": "Monde", "Effectif": "1 000+ salariés"},
    "SERFIGROUP": {"Secteur": "Retail", "Nom Officiel": "SERFI INTERNATIONAL", "Adresse": "Nice (France)", "Région": "Provence-Alpes-Côte d'Azur", "Effectif": "20-49 salariés"},
    "SERFI INTERNATIONAL": {"Secteur": "Retail", "Nom Officiel": "SERFI INTERNATIONAL", "Adresse": "Nice (France)", "Région": "Provence-Alpes-Côte d'Azur", "Effectif": "20-49 salariés"}
}

def get_region_from_dept(zip_code):
    if not zip_code or len(zip_code) < 2: return "Autre"
    dept = zip_code[:2]
    # Simplified map for major regions or using a dict
    # For now, let's return Department number to be safe, or a few key ones.
    # To do it properly, I'd need a huge dict. Let's try to get 'departement' name from API if possible?
    # The API returns 'departement' object usually.
    return f"Dept {dept}" # Placeholder, will try to fetch properly from API result

# --- Helper Functions ---

def extract_company_from_input(input_str):
    input_str = input_str.strip()
    company = input_str

    if "@" in input_str and not input_str.startswith("http"):
        try:
            domain = input_str.split("@")[1]
            if "." in domain:
                company = domain.split(".")[0]
                if company.lower() in ["gmail", "outlook", "hotmail", "yahoo", "orange", "wanadoo", "free", "sfr", "icloud"]:
                    return input_str, False 
        except:
            pass
    
    company = company.replace("-", " ").replace(".", " ")
    company = re.sub(r'(group|france|partners|holdings|corp|inc|ltd)$', r' \1', company, flags=re.IGNORECASE)
    
    return company.strip(), True

def get_sector_from_naf(naf_code):
    if not naf_code: return None
    naf_clean = naf_code.replace(".", "")
    best_sector = None
    max_prefix_len = 0
    for sector, config in SECTOR_CONFIG.items():
        for prefix in config["naf_prefixes"]:
            if naf_clean.startswith(prefix):
                if len(prefix) > max_prefix_len:
                    max_prefix_len = len(prefix)
                    best_sector = sector
    return best_sector

def score_text(text, weights=1.0):
    scores = {}
    text = text.lower()
    for sector, config in SECTOR_CONFIG.items():
        score = 0
        for keyword in config["keywords"]:
            count = len(re.findall(r'\\b' + re.escape(keyword) + r'\\b', text))
            score += count * weights
        scores[sector] = score
    return scores

def analyze_web_content(company_name):
    try:
        try:
            # googlesearch-python usage
            search_results = list(search(company_name, num_results=1, lang="fr"))
        except:
             search_results = list(search(company_name, num_results=1))
            
        if not search_results:
            return None, "URL not found", 0

        url = search_results[0]
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
        except:
            return None, f"Scraping failed for {url}", 0

        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string if soup.title else ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        desc = meta_desc['content'] if meta_desc and 'content' in meta_desc.attrs else ""
        high_priority_text = f"{title} {desc}"
        
        headers_text = " ".join([h.get_text() for h in soup.find_all(['h1', 'h2'])])
        body_text = " ".join([p.get_text() for p in soup.find_all('p')])[:5000]

        scores_high = score_text(high_priority_text, weights=3.0)
        scores_med = score_text(headers_text, weights=2.0)
        scores_low = score_text(body_text, weights=1.0)
        
        final_scores = {}
        for sector in SECTOR_CONFIG.keys():
            final_scores[sector] = scores_high.get(sector, 0) + scores_med.get(sector, 0) + scores_low.get(sector, 0)
            
        if not final_scores or all(score == 0 for score in final_scores.values()):
             return "Unknown", f"Web Analysis ({url}) - No keywords matched", 0
             
        best_sector = max(final_scores, key=final_scores.get)
        max_score = final_scores[best_sector]
        
        if max_score > 0:
             return best_sector, f"Web Analysis ({url})", max_score
        
        return "Unknown", f"Web Analysis ({url}) - No keywords matched", 0

    except Exception as e:
        return None, f"Error (Web): {str(e)}", 0

def categorize_company_logic(raw_input):
    try:
        company_name, is_valid = extract_company_from_input(raw_input)
        
        # 0. Check Private Global List (Fast Path)
        upper_name = company_name.upper().strip()
        if upper_name in GLOBAL_OVERRIDES:
            ov = GLOBAL_OVERRIDES[upper_name]
            return {
                "Input": raw_input,
                "Nom Officiel": ov["Nom Officiel"],
                "Secteur": ov["Secteur"],
                "Détail": "Global Brand (Static)",
                "Source": "Base de données Interne",
                "Score": "100%",
                "Adresse": ov["Adresse"],
                "Région": ov["Région"],
                "Lien": "#"
            }
        
        if not is_valid:
            return {
                "Input": raw_input,
                "Nom Officiel": "N/A",
                "Secteur": "N/A",
                "Détail": "Email Générique ignoré",
                "Source": "Filtre Email",
                "Score": "0",
                "Adresse": "-", 
                "Région": "-",
                "Lien": "-"
            }
        
        api_url = f"https://recherche-entreprises.api.gouv.fr/search?q={company_name}&per_page=3"
    
        naf_code = None
        naf_label = ""
        official_name = company_name
        address = "Non renseigné"
        region = "Non renseigné"
        headcount = "Non renseigné"
        slug = ""
        link_url = "" # init to empty string

        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                if data and data['results']:
                    best_result = None
                    for res in data['results']:
                        name_check = res.get('nom_complet', '').upper()
                        if "COMITE" not in name_check and "CSE" not in name_check and "INDIVISION" not in name_check:
                             best_result = res
                             break
                    
                    if not best_result:
                        best_result = data['results'][0]
    
                    naf_code = best_result.get('activite_principale', '')
                    naf_label = best_result.get('libelle_activite_principale', '')
                    official_name = best_result.get('nom_complet', company_name)
                    
                    # Extra Data
                    siege = best_result.get('siege', {})
                    address = siege.get('adresse', best_result.get('adresse', ''))
                    
                    # Region logic
                    cp = siege.get('code_postal', '')
                    city = siege.get('libelle_commune', '')
                    
                    # Priority: Siege Region Name > Root Region > CP Inference
                    region = siege.get('libelle_region') or best_result.get('region') or ""
                    
                    if not region and cp:
                         if cp.startswith('75') or cp.startswith('92') or cp.startswith('93') or cp.startswith('94') or cp.startswith('78') or cp.startswith('91') or cp.startswith('95') or cp.startswith('77'):
                             region = "Île-de-France"
                         else:
                             region = f"{city} ({cp[:2]})"
                    
                    # Headcount - Check root then unite_legale
                    tranche = best_result.get('tranche_effectifs')
                    unite_legale = best_result.get('unite_legale') or {}
                    
                    if not tranche:
                        tranche = unite_legale.get('tranche_effectifs')
                    
                    if not tranche: tranche = "NN"
                    
                    headcount = TRANCHE_EFFECTIFS.get(tranche, "Non renseigné")
                    
                    # Link - Use SIREN which is safer than slug
                    siren = best_result.get('siren')
                    if not siren:
                         siren = unite_legale.get('siren')
                         
                    link_url = f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}" if siren else "#"
    
        except Exception as e:
            print(f"API Error: {e}")
    
        result_base = {
            "Input": raw_input,
            "Nom Officiel": official_name,
            "Adresse": address,
            "Région": region,
            "Lien": link_url
        }
    
        if naf_code:
            sector_naf = get_sector_from_naf(naf_code)
            if sector_naf:
                # --- SMART CONFLICT RESOLUTION ---
                # If API gives "Agriculture", "Construction", "Hotels" or "Consulting" (common for small local companies with big names)
                # We double check with Web Analysis to see if it's actually a Global Brand
                
                is_suspicious_sector = sector_naf in [
                    "Agriculture / Livestock / Seafood", 
                    "Construction / Real Estate", 
                    "Agri-food / Beverages",
                    "Hotels / Restaurants",
                    "Consulting / IT Services"
                ]
                
                if is_suspicious_sector:
                     # Check the web
                     sector_web, source_web, score_web = analyze_web_content(company_name)
                     
                     # If Web says "Tech" or "Retail" (and score is decent), we OVERRIDE the API.
                     # Example: API says "Apple = Agriculture", Web says "Apple = Tech". We take Tech.
                     if sector_web and sector_web != "Non Trouvé" and sector_web != sector_naf and score_web >= 2:
                          address = "International / Web" # Override address too as it's likely wrong
                          region = "Monde"
                          return {
                              **result_base,
                              "Secteur": sector_web,
                              "Détail": f"Web Override (was {sector_naf})", 
                              "Source": f"{source_web}", 
                              "Score": f"{score_web}",
                              "Adresse": address,
                              "Région": region,
                              "Nom Officiel": company_name.upper()
                          }
                
                # Debugging: If we stick with API, let's say what the web found
                if is_suspicious_sector:
                     web_msg = f"(Web saw: {sector_web} score {score_web})" if sector_web else "(Web Search Failed/Blocked)"
                     return {
                         **result_base, 
                         "Secteur": sector_naf, 
                         "Détail": f"NAF: {naf_code} {web_msg}", 
                         "Source": "Officiel (Code NAF)", 
                         "Score": "100%"
                     }
    
                return {**result_base, "Secteur": sector_naf, "Détail": f"NAF: {naf_code}", "Source": "Officiel (Code NAF)", "Score": "100%"}
    
        if naf_label:
            label_scores = score_text(naf_label, weights=5.0)
            best_label_sector = max(label_scores, key=label_scores.get)
            if label_scores[best_label_sector] > 0:
                 return {**result_base, "Secteur": best_label_sector, "Détail": f"NAF: {naf_code} (Label)", "Source": "Officiel (Label)", "Score": f"{label_scores[best_label_sector]}"}
    
        # --- FALLBACK: WEB ANALYSIS (International / No SIRET) ---
        sector_web, source_web, score_web = analyze_web_content(company_name)
        
        # If we are here, it means we didn't find a NAF code. 
        # Likely international or just name match without NAF.
        # Update visuals if they were "Non renseigné"
        if address == "Non renseigné": address = "International / Web"
        if region == "Non renseigné": region = "Monde"
        
        return {
            **result_base,
            "Nom Officiel": official_name if official_name != company_name else company_name,
            "Secteur": sector_web if sector_web else "Non Trouvé",
            "Détail": f"Web Keywords ({score_web})",
            "Source": source_web + " (Hors France)",
            "Score": f"{score_web}",
            "Adresse": address,
            "Région": region
        }
    
    except Exception as e:
        # Catch-all to prevent "Erreur Interne" in batch from crashing the loop without details
        return {
            "Input": raw_input,
            "Nom Officiel": "Erreur",
            "Secteur": "Erreur",
            "Détail": f"FIXED CRASH: {str(e)}",
            "Source": "System Error",
            "Score": "0",
            "Adresse": "-", "Région": "-", "Lien": "-"
        }

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/categorize', methods=['POST'])
def api_categorize():
    data = request.json
    company_input = data.get('input')
    if not company_input:
        return jsonify({"error": "No input provided"}), 400
    
    result = categorize_company_logic(company_input)
    return jsonify(result)

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filename = file.filename.lower()
    inputs = []
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file, header=None)
            inputs = df.iloc[:, 0].dropna().astype(str).tolist()
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file, header=None)
            inputs = df.iloc[:, 0].dropna().astype(str).tolist()
        else:
             return jsonify({"error": "Format non supporté (CSV ou Excel)"}), 400
             
        # Process the list (same as batch)
        # We can reuse the batch logic or return the list for the client to call batch?
        # Let's return the processed results directly to be efficient.
        results = []
        for i, line in enumerate(inputs):
            if line.strip():
                 if i > 0: time.sleep(1.0) # Rate limit
                 results.append(categorize_company_logic(line))
        
        return jsonify({"results": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch', methods=['POST'])
def api_batch():
    try:
        data = request.json
        if not data:
             return jsonify({"error": "Invalid JSON/Empty Body"}), 400
             
        inputs = data.get('inputs', [])
        results = []
        
        for i, line in enumerate(inputs):
            if not isinstance(line, str): line = str(line) # Safety cast
            
            if line.strip():
                # Basic rate limiting for batch to avoid flooding Google if many requests
                if i > 0: time.sleep(1.0)
                try:
                    results.append(categorize_company_logic(line))
                except Exception as e:
                    print(f"Batch Error on {line}: {e}")
                    results.append({
                        "Input": line,
                        "Nom Officiel": "Erreur Interne",
                        "Secteur": "Erreur",
                        "Détail": f"Crash: {str(e)}",
                        "Source": "Server Error",
                        "Score": "0",
                        "Adresse": "-", "Région": "-", "Effectif": "-", "Lien": "-"
                    })
                
        return jsonify({"results": results})

    except Exception as e:
        print(f"API Batch FATAL: {e}")
        return jsonify({"error": f"Fatal Batch Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
