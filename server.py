from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import requests
from bs4 import BeautifulSoup
# from duckduckgo_search import DDGS # Moved to local scope for safety
import time
import re
from urllib.parse import urlparse

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# --- Configuration ---
# --- Comprehensive Region Mapping (The Trap Anti-Fail) ---
DEPT_TO_REGION = {
    "01": "Auvergne-Rhône-Alpes", "02": "Hauts-de-France", "03": "Auvergne-Rhône-Alpes", "04": "Provence-Alpes-Côte d'Azur", "05": "Provence-Alpes-Côte d'Azur",
    "06": "Provence-Alpes-Côte d'Azur", "07": "Auvergne-Rhône-Alpes", "08": "Grand Est", "09": "Occitanie", "10": "Grand Est",
    "11": "Occitanie", "12": "Occitanie", "13": "Provence-Alpes-Côte d'Azur", "14": "Normandie", "15": "Auvergne-Rhône-Alpes",
    "16": "Nouvelle-Aquitaine", "17": "Nouvelle-Aquitaine", "18": "Centre-Val de Loire", "19": "Nouvelle-Aquitaine", "21": "Bourgogne-Franche-Comté",
    "22": "Bretagne", "23": "Nouvelle-Aquitaine", "24": "Nouvelle-Aquitaine", "25": "Bourgogne-Franche-Comté", "26": "Auvergne-Rhône-Alpes",
    "27": "Normandie", "28": "Centre-Val de Loire", "29": "Bretagne", "2A": "Corse", "2B": "Corse",
    "30": "Occitanie", "31": "Occitanie", "32": "Occitanie", "33": "Nouvelle-Aquitaine", "34": "Occitanie",
    "35": "Bretagne", "36": "Centre-Val de Loire", "37": "Centre-Val de Loire", "38": "Auvergne-Rhône-Alpes", "39": "Bourgogne-Franche-Comté",
    "40": "Nouvelle-Aquitaine", "41": "Centre-Val de Loire", "42": "Auvergne-Rhône-Alpes", "43": "Auvergne-Rhône-Alpes", "44": "Pays de la Loire",
    "45": "Centre-Val de Loire", "46": "Occitanie", "47": "Nouvelle-Aquitaine", "48": "Occitanie", "49": "Pays de la Loire",
    "50": "Normandie", "51": "Grand Est", "52": "Grand Est", "53": "Pays de la Loire", "54": "Grand Est",
    "55": "Grand Est", "56": "Bretagne", "57": "Grand Est", "58": "Bourgogne-Franche-Comté", "59": "Hauts-de-France",
    "60": "Hauts-de-France", "61": "Normandie", "62": "Hauts-de-France", "63": "Auvergne-Rhône-Alpes", "64": "Nouvelle-Aquitaine",
    "65": "Occitanie", "66": "Occitanie", "67": "Grand Est", "68": "Grand Est", "69": "Auvergne-Rhône-Alpes",
    "70": "Bourgogne-Franche-Comté", "71": "Bourgogne-Franche-Comté", "72": "Pays de la Loire", "73": "Auvergne-Rhône-Alpes", "74": "Auvergne-Rhône-Alpes",
    "75": "Île-de-France", "76": "Normandie", "77": "Île-de-France", "78": "Île-de-France", "79": "Nouvelle-Aquitaine",
    "80": "Hauts-de-France", "81": "Occitanie", "82": "Occitanie", "83": "Provence-Alpes-Côte d'Azur", "84": "Provence-Alpes-Côte d'Azur",
    "85": "Pays de la Loire", "86": "Nouvelle-Aquitaine", "87": "Nouvelle-Aquitaine", "88": "Grand Est", "89": "Bourgogne-Franche-Comté",
    "90": "Bourgogne-Franche-Comté", "91": "Île-de-France", "92": "Île-de-France", "93": "Île-de-France", "94": "Île-de-France",
    "95": "Île-de-France", "971": "Guadeloupe", "972": "Martinique", "973": "Guyane", "974": "La Réunion", "976": "Mayotte"
}

SECTOR_CONFIG = {
    "Agriculture / Livestock / Seafood": {
        "naf_prefixes": ["01", "02", "03"],
        "keywords": ["agriculture", "élevage", "pêche", "agricole", "ferme", "bio", "tracteur", "champs", "vigne", "viticulture", "horticulture", "maraichage", "bétail", "aquaculture", "farming", "livestock", "seafood", "crops"]
    },
    "Banking": {
        "naf_prefixes": ["641"],
        "keywords": ["banque", "crédit", "bancaire", "compte", "livret", "cb", "bank", "banking", "loan", "credit", "bnp", "société générale", "crédit agricole", "bpce"]
    },
    "Chemicals": {
        "naf_prefixes": ["20"],
        "keywords": ["chimie", "laboratoire", "molécules", "réactif", "polymère", "plastique", "chimique", "petrochemical", "chemicals", "chemistry", "lab", "solvay", "arkema", "air liquide"]
    },
    "Communication / Media & Entertainment / Telecom": {
        "naf_prefixes": ["59", "60", "61", "63"],
        "keywords": ["télécom", "média", "publicité", "fibre", "internet", "presse", "journal", "tv", "radio", "marketing", "agence", "communication", "entertainment", "telecom", "broadcasting", "advertising", "media", "orange", "sfr", "bouygues", "free", "publicis", "havas"]
    },
    "Construction": {
        "naf_prefixes": ["41", "42", "43"],
        "keywords": ["btp", "construction", "bâtiment", "génie civil", "infrastructure", "travaux", "architecture", "maçonnerie", "électicité", "plomberie", "architect", "builder", "contractor", "civil", "renovation", "vinci", "eiffage", "bouygues construction"]
    },
    "Consulting / IT Services": {
        "naf_prefixes": ["62", "631", "582", "702", "692", "7112", "712", "732", "74"],
        "keywords": ["conseil", "consulting", "esn", "stratégie", "audit", "expertise", "ingénierie", "rub", "management", "digital", "transformation", "it services", "système d'information", "data", "advisory", "capgemini", "deloitte", "kpmg", "pwc", "mckinsey", "bain", "bcg", "accenture", "sogeti", "sopra", "wavestone", "alteca", "umanis"]
    },
    "CPG (Consumer Packaged Goods)": {
        "naf_prefixes": ["204"],
        "keywords": ["fmcg", "biens de consommation", "hygiène", "produits ménagers", "cosmétique", "beauté", "parfum", "shampoing", "savon", "lessive", "cpg", "consumer goods", "l'oréal", "procter", "gamble", "unilever", "danone", "nestlé", "henkel"]
    },
    "Education": {
        "naf_prefixes": ["85"],
        "keywords": ["éducation", "formation", "école", "université", "training", "learning", "elearning", "edtech", "campus", "formation continue", "school", "university", "academy", "college"]
    },
    "Energy / Utilities": {
        "naf_prefixes": ["35", "36", "37", "38", "39"],
        "keywords": ["énergie", "électricité", "gaz", "eau", "déchets", "environnement", "recyclage", "solaire", "éolien", "nucléaire", "oil", "petrol", "renewables", "green", "carbon", "hydrogen", "edf", "engie", "total", "veolia", "suez"]
    },
    "Finance / Real Estate": {
        "naf_prefixes": ["64", "66", "68"],
        "keywords": ["finance", "immobilier", "investissement", "gestion d'actifs", "courtier", "syndic", "promoteur", "real estate", "realty", "property", "logement", "immo", "wealth", "fintech", "payment", "trading", "crypto", "blockchain", "vc", "private equity", "fund", "foncia", "nexity"]
    },
    "Food / Beverages": {
        "naf_prefixes": ["10", "11"],
        "keywords": ["agroalimentaire", "aliments", "boissons", "food", "beverage", "vin", "spiritueux", "bière", "champagne", "nutrition", "snack", "dairy", "laitier", "viande", "boulangerie", "traiteur"]
    },
    "Healthcare / Medical Services": {
        "naf_prefixes": ["86", "87", "88"],
        "keywords": ["santé", "clinique", "hôpital", "soins", "médecin", "infirmier", "ehpad", "médical", "chirurgie", "patient", "healthcare", "medical", "hospital", "clinic", "care", "doctor", "diagnostic", "radiologie", "dentaire", "kine", "ramsay", "elsan"]
    },
    "Hotels / Restaurants": {
        "naf_prefixes": ["55", "56"],
        "keywords": ["hôtel", "restaurant", "tourisme", "hébergement", "camping", "voyage", "bar", "café", "brasserie", "cuisine", "hotel", "hospitality", "tourism", "restaurant", "catering", "accor", "club med", "sodexo", "elior"]
    },
    "Insurance / Mutual Health Insurance": {
        "naf_prefixes": ["65"],
        "keywords": ["assurance", "mutuelle", "courtage", "assureur", "prévoyance", "risques", "insurance", "underwriting", "axa", "allianz", "generali", "maif", "macif", "groupama", "malakoff"]
    },
    "Luxury": {
        "naf_prefixes": ["141", "142", "151", "152"],
        "keywords": ["luxe", "prestige", "haute couture", "joaillerie", "maroquinerie", "palace", "luxury", "fashion", "jewelry", "premium", "high-end", "mode", "vêtement", "chaussures", "shoes", "wear", "apparel", "lvmh", "kering", "hermès", "chanel", "dior", "vuitton", "gucci", "prada"]
    },
    "Manufacturing / Industry": {
        "naf_prefixes": ["13", "14", "15", "16", "17", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33"],
        "keywords": ["industrie", "usine", "fabrication", "mécanique", "métallurgie", "plasturgie", "assemblage", "production", "machine", "outil", "industriel", "manufacturing", "industry", "factory", "plant", "metal", "machinery", "automotive", "aéronautique", "aerospace", "defense", "textile", "imprimerie", "packaging", "saint-gobain", "schneider", "legrand", "michelin"]
    },
    "Not For Profit": {
        "naf_prefixes": ["94", "91"],
        "keywords": ["association", "fondation", "ong", "non-profit", "charity", "bénévole", "social", "humanitaire", "syndicat", "union", "club", "croix rouge", "secours populaire"]
    },
    "Pharmaceutics": {
        "naf_prefixes": ["21"],
        "keywords": ["pharmacie", "médicament", "biotech", "laboratoire", "vaccin", "recherche", "molécule", "thérapie", "pharmaceutical", "pharma", "drug", "biotechnology", "medicine", "lifescience", "sanofi", "servier", "pfizer", "moderna"]
    },
    "Public administration & government": {
        "naf_prefixes": ["84"],
        "keywords": ["mairie", "préfecture", "ministère", "collectivité", "public", "etat", "government", "administration", "caisse", "caf", "urssaf", "pole emploi", "france travail", "ambassade", "consulat"]
    },
    "Retail": {
        "naf_prefixes": ["45", "46", "47"],
        "keywords": ["commerce", "vente", "magasin", "boutique", "supermarché", "distribution", "retail", "store", "shop", "e-commerce", "marketplace", "grossiste", "grand magasin", "shopping", "mall", "outlet", "franchise", "carrefour", "auchan", "leclerc", "decathlon", "fnac", "darty", "amazon", "cdiscount"]
    },
    "Tech / Software": {
        "naf_prefixes": ["582", "6201", "6312", "262"],
        "keywords": ["logiciel", "saas", "tech", "software", "application", "ia", "intelligence artificielle", "cloud", "développement", "web", "app", "cybersecurity", "platform", "technology", "developer", "electronics", "hardware", "computer", "start-up", "google", "microsoft", "apple", "meta", "aws", "salesforce", "sap", "oracle"]
    },
    "Transportation, Logistics & Storage": {
        "naf_prefixes": ["49", "50", "51", "52", "53"],
        "keywords": ["transport", "logistique", "fret", "livraison", "messagerie", "entrepôt", "supply chain", "shipping", "transit", "colis", "airline", "aérien", "avion", "bateau", "compagnie aérienne", "rail", "ferroviaire", "maritime", "port", "sncf", "air france", "maersk", "cma cgm", "dhl", "fedex", "ups"]
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
    "LVMH": {"Secteur": "Luxury", "Nom Officiel": "LVMH MOET HENNESSY", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "CHRISTIAN DIOR": {"Secteur": "Luxury", "Nom Officiel": "CHRISTIAN DIOR SE", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "LOUIS VUITTON": {"Secteur": "Luxury", "Nom Officiel": "LOUIS VUITTON MALLETIER", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "CHRISTIAN LOUBOUTIN": {"Secteur": "Luxury", "Nom Officiel": "CHRISTIAN LOUBOUTIN", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "1 000+ salariés"},
    "CHANEL": {"Secteur": "Luxury", "Nom Officiel": "CHANEL SAS", "Adresse": "Neuilly-sur-Seine (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "HERMES": {"Secteur": "Luxury", "Nom Officiel": "HERMES INTERNATIONAL", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "GUCCI": {"Secteur": "Luxury", "Nom Officiel": "GUCCI", "Adresse": "Florence (Italy)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "PRADA": {"Secteur": "Luxury", "Nom Officiel": "PRADA SPA", "Adresse": "Milan (Italy)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "ORANGE": {"Secteur": "Communication / Media & Entertainment / Telecom", "Nom Officiel": "ORANGE SA", "Adresse": "Issy-les-Moulineaux (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "SFR": {"Secteur": "Communication / Media & Entertainment / Telecom", "Nom Officiel": "SFR", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "FREE": {"Secteur": "Communication / Media & Entertainment / Telecom", "Nom Officiel": "ILIAD (FREE)", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "ILIAD": {"Secteur": "Communication / Media & Entertainment / Telecom", "Nom Officiel": "ILIAD (FREE)", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "BOUYGUES": {"Secteur": "Construction", "Nom Officiel": "BOUYGUES SA", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "BOUYGUES TELECOM": {"Secteur": "Communication / Media & Entertainment / Telecom", "Nom Officiel": "BOUYGUES TELECOM", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    
    # Consulting (Added due to user feedback)
    "CAPGEMINI": {"Secteur": "Consulting / IT Services", "Nom Officiel": "CAPGEMINI SE", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "KPMG": {"Secteur": "Consulting / IT Services", "Nom Officiel": "KPMG S.A", "Adresse": "Paris La Défense (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "DELOITTE": {"Secteur": "Consulting / IT Services", "Nom Officiel": "DELOITTE SAS", "Adresse": "Paris La Défense (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "EY": {"Secteur": "Consulting / IT Services", "Nom Officiel": "ERNST & YOUNG", "Adresse": "Paris La Défense (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "PWC": {"Secteur": "Consulting / IT Services", "Nom Officiel": "PWC FRANCE", "Adresse": "Neuilly-sur-Seine (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "ACCENTURE": {"Secteur": "Consulting / IT Services", "Nom Officiel": "ACCENTURE", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    
    # Retail / Grands Magasins
    "GALERIES LAFAYETTE": {"Secteur": "Retail", "Nom Officiel": "GALERIES LAFAYETTE", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "PRINTEMPS": {"Secteur": "Retail", "Nom Officiel": "PRINTEMPS", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},

    # Tech / Web
    "SPOTIFY": {"Secteur": "Tech / Software", "Nom Officiel": "SPOTIFY TECHNOLOGY", "Adresse": "Stockholm (Sweden)", "Région": "Monde", "Effectif": "5 000+ salariés"},
    "UBER": {"Secteur": "Tech / Software", "Nom Officiel": "UBER TECHNOLOGIES", "Adresse": "San Francisco, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "AIRBNB": {"Secteur": "Tech / Software", "Nom Officiel": "AIRBNB INC.", "Adresse": "San Francisco, CA (USA)", "Région": "Monde", "Effectif": "5 000+ salariés"},
    "AIR BNB": {"Secteur": "Tech / Software", "Nom Officiel": "AIRBNB INC.", "Adresse": "San Francisco, CA (USA)", "Région": "Monde", "Effectif": "5 000+ salariés"},
    "NETFLIX": {"Secteur": "Communication / Media & Entertainment / Telecom", "Nom Officiel": "NETFLIX INC.", "Adresse": "Los Gatos, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "NVIDIA": {"Secteur": "Tech / Software", "Nom Officiel": "NVIDIA CORP", "Adresse": "Santa Clara, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    
    # Auto
    "BMW": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "BMW AG", "Adresse": "Munich (Germany)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "MERCEDES": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "MERCEDES-BENZ GROUP", "Adresse": "Stuttgart (Germany)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "TOYOTA": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "TOYOTA MOTOR CORP", "Adresse": "Toyota City (Japan)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "VOLKSWAGEN": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "VOLKSWAGEN AG", "Adresse": "Wolfsburg (Germany)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    
    # Consumer
    "COCA COLA": {"Secteur": "Food / Beverages", "Nom Officiel": "THE COCA-COLA COMPANY", "Adresse": "Atlanta, GA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés", "Siren": None},
    "DANONE": {"Secteur": "Food / Beverages", "Nom Officiel": "DANONE", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés", "Siren": "552032534"},
    "PEPSI": {"Secteur": "Food / Beverages", "Nom Officiel": "PEPSICO INC.", "Adresse": "Harrison, NY (USA)", "Région": "Monde", "Effectif": "10 000+ salariés", "Siren": None},
    "SAMSUNG": {"Secteur": "Tech / Software", "Nom Officiel": "SAMSUNG ELECTRONICS", "Adresse": "Suwon (South Korea)", "Région": "Monde", "Effectif": "10 000+ salariés", "Siren": None},
    "NIKE": {"Secteur": "Retail", "Nom Officiel": "NIKE INC.", "Adresse": "Beaverton, OR (USA)", "Région": "Monde", "Effectif": "10 000+ salariés", "Siren": None},
    
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
    "DISNEY": {"Secteur": "Communication / Media & Entertainment / Telecom", "Nom Officiel": "THE WALT DISNEY COMPANY", "Adresse": "Burbank, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "DECATHLON": {"Secteur": "Retail", "Nom Officiel": "DECATHLON SE", "Adresse": "Villeneuve-d'Ascq (France)", "Région": "Hauts-de-France", "Effectif": "10 000+ salariés"},
    "LONGCHAMP": {"Secteur": "Luxury", "Nom Officiel": "LONGCHAMP SAS", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "1 000+ salariés"},
    "MONOPRIX": {"Secteur": "Retail", "Nom Officiel": "MONOPRIX", "Adresse": "Clichy (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "PERNOD RICARD": {"Secteur": "Food / Beverages", "Nom Officiel": "PERNOD RICARD", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "PFIZER": {"Secteur": "Pharmaceutics", "Nom Officiel": "PFIZER INC.", "Adresse": "New York, NY (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "LA POSTE": {"Secteur": "Transportation, Logistics & Storage", "Nom Officiel": "LA POSTE", "Adresse": "Issy-les-Moulineaux (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "GROUPE LA POSTE": {"Secteur": "Transportation, Logistics & Storage", "Nom Officiel": "LA POSTE", "Adresse": "Issy-les-Moulineaux (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "TDF": {"Secteur": "Communication / Media & Entertainment / Telecom", "Nom Officiel": "TDF", "Adresse": "Montrouge (France)", "Région": "Île-de-France", "Effectif": "1 000+ salariés"},
    "SYMBIO": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "SYMBIO", "Adresse": "Vénissieux (France)", "Région": "Auvergne-Rhône-Alpes", "Effectif": "500+ salariés"},
    "APRIL": {"Secteur": "Insurance / Mutual Health Insurance", "Nom Officiel": "APRIL", "Adresse": "Lyon (France)", "Région": "Auvergne-Rhône-Alpes", "Effectif": "1 000+ salariés"},
    "SAFRAN": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "SAFRAN SA", "Adresse": "Paris (France)", "Région": "Île-de-France", "Effectif": "10 000+ salariés"},
    "VISIATIV": {"Secteur": "Tech / Software", "Nom Officiel": "VISIATIV", "Adresse": "Charbonnières-les-Bains (France)", "Région": "Auvergne-Rhône-Alpes", "Effectif": "1 000+ salariés"},
    "AMOOBI": {"Secteur": "Tech / Software", "Nom Officiel": "AMOOBI", "Adresse": "N/A (International)", "Région": "Monde", "Effectif": "10-50 salariés"},
    "SAFRAN AERO BOOSTERS": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "SAFRAN AERO BOOSTERS", "Adresse": "Herstal (Belgium)", "Région": "Monde", "Effectif": "1 000+ salariés"},
    "SAFRAN AERO BOSOTERS": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "SAFRAN AERO BOOSTERS", "Adresse": "Herstal (Belgium)", "Région": "Monde", "Effectif": "1 000+ salariés"},
    "SERFIGROUP": {"Secteur": "Retail", "Nom Officiel": "SERFI INTERNATIONAL", "Adresse": "Nice (France)", "Région": "Provence-Alpes-Côte d'Azur", "Effectif": "20-49 salariés"},
    "SERFI GROUP": {"Secteur": "Retail", "Nom Officiel": "SERFI INTERNATIONAL", "Adresse": "Nice (France)", "Région": "Provence-Alpes-Côte d'Azur", "Effectif": "20-49 salariés"},
    "SERFI INTERNATIONAL": {"Secteur": "Retail", "Nom Officiel": "SERFI INTERNATIONAL", "Adresse": "Nice (France)", "Région": "Provence-Alpes-Côte d'Azur", "Effectif": "20-49 salariés"},
    
    # International Tech / Electronics (Added for safety)
    "ADOBE": {"Secteur": "Tech / Software", "Nom Officiel": "ADOBE INC.", "Adresse": "San Jose, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "NINTENDO": {"Secteur": "Communication / Media & Entertainment / Telecom", "Nom Officiel": "NINTENDO CO., LTD", "Adresse": "Kyoto (Japan)", "Région": "Monde", "Effectif": "5 000+ salariés"},
    "PHILIPS": {"Secteur": "Manufacturing / Industry", "Nom Officiel": "KONINKLIJKE PHILIPS", "Adresse": "Amsterdam (Netherlands)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    "SALESFORCE": {"Secteur": "Tech / Software", "Nom Officiel": "SALESFORCE", "Adresse": "San Francisco, CA (USA)", "Région": "Monde", "Effectif": "10 000+ salariés"},
    
    # Modern Tech / Remote Tools
    "ZOOM": {"Secteur": "Tech / Software", "Nom Officiel": "ZOOM VIDEO COMMUNICATIONS", "Adresse": "San Jose, CA (USA)", "Région": "Monde", "Effectif": "5 000+ salariés"},
    "SLACK": {"Secteur": "Tech / Software", "Nom Officiel": "SALESFORCE (SLACK)", "Adresse": "San Francisco, CA (USA)", "Région": "Monde", "Effectif": "1 000+ salariés"}
}

# Pre-compute Normalized Keys for Robust Matching
# Maps "COCACOLA" -> "COCA COLA", "LVMH" -> "LVMH", "AIRBNB" -> "AIRBNB"
NORMALIZED_OVERRIDES = {k.replace(" ", "").replace(".", "").replace("-", ""): k for k in GLOBAL_OVERRIDES}

def get_region_from_dept(zip_code):
    if not zip_code or len(zip_code) < 2: return "Autre"
    
    # Handle DOM-TOM (3 digits) vs metro (2 digits)
    if zip_code.startswith('97') or zip_code.startswith('98'):
        dept = zip_code[:3]
    else:
        dept = zip_code[:2]

    return DEPT_TO_REGION.get(dept, f"France ({dept})")

# --- Helper Functions ---

def extract_company_from_input(input_str):
    input_str = input_str.strip()
    company = input_str

    if "@" in input_str and not input_str.startswith("http"):
        try:
            domain = input_str.split("@")[1]
            if "." in domain:
                company = domain.split(".")[0]
                company = domain.split(".")[0]
                # Smart Filter: Keep Gmail/Outlook ignored, but ALLOW Orange/Free/SFR because they are also big companies to target.
                # If it's a personal email, let the user decide, but don't block valid corporate emails.
                if company.lower() in ["gmail", "outlook", "hotmail", "yahoo", "wanadoo", "icloud", "laposte"]:
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
            # Valid Regex: r'\b' (Word Boundary). escaped keyword.
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
            score += count * weights
        scores[sector] = score
    return scores

def analyze_web_content(company_name):
    try:
        search_results = []
        snippet_text = ""
        source_url = ""
        page_title = "" 
        
        # DuckDuckGo Search (Defensive)
        try:
            # Local import to prevent module-level crash if library is missing/incompatible
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                 # limit=1
                 results = list(ddgs.text(company_name, region='fr-fr', max_results=1))
                 if results:
                      first_res = results[0]
                      source_url = first_res.get('href', '')
                      page_title = first_res.get('title', '')
                      snippet_text = f"{page_title} {first_res.get('body', '')}"
        except Exception as e:
            print(f"DDG Lib Error: {e}")
            

        if not snippet_text:
            return None, "URL not found", 0, ""

        # Score the Snippet directly
        # Fix: Use r'\b' for word boundary instead of r'\\b' (which matches literal backslash)
        scores_snippet = score_text(snippet_text, weights=5.0)
        
        final_scores = scores_snippet
            
        if not final_scores or all(score == 0 for score in final_scores.values()):
             return "Unknown", f"Web Analysis ({source_url}) - No keywords in snippet", 0, page_title
             
        best_sector = max(final_scores, key=final_scores.get)
        max_score = final_scores[best_sector]
        
        if max_score > 0:
             return best_sector, f"Web Analysis ({source_url})", max_score, page_title
        
        return "Unknown", f"Web Analysis ({source_url}) - No keywords matched", 0, page_title

    except Exception as e:
        return None, f"Error (Web): {str(e)}", 0, ""


def categorize_company_logic(raw_input):
    try:
        company_name, is_valid = extract_company_from_input(raw_input)
        
        # 1. Check Global Overrides (for SECTOR enforcing)
        upper_name = company_name.upper().strip()
        normalized_input = upper_name.replace(" ", "").replace(".", "").replace("-", "")

        target_override = None
        if upper_name in GLOBAL_OVERRIDES:
            target_override = GLOBAL_OVERRIDES[upper_name]
        elif normalized_input in NORMALIZED_OVERRIDES:
            real_key = NORMALIZED_OVERRIDES[normalized_input]
            target_override = GLOBAL_OVERRIDES[real_key]
            
        forced_sector = target_override.get("Secteur") if target_override else None
        
        if not is_valid:
             return { "Input": raw_input, "Nom Officiel": "N/A", "Secteur": "N/A", "Détail": "Email Ignoré", "Source": "Filtre", "Score": "0", "Adresse": "-", "Région": "-", "Lien": "-" }

        # 2. Call API (Try to get official SIREN/Identity even if we have an override)
        # We search even if we have an override, to get the correct SIREN and Address.
        api_url = f"https://recherche-entreprises.api.gouv.fr/search?q={company_name}&per_page=5"
        
        naf_code = None
        official_name = company_name
        address = "Non renseigné"
        region = "Non renseigné"
        link_url = ""
        
        search_success = False

        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                if data and data['results']:
                    # Loop to find the first non-CSE/COMITE result
                    best_res = None
                    for res in data['results']:
                         name_check = res.get('nom_complet', '').upper()
                         if "COMITE" not in name_check and "CSE " not in name_check:
                              best_res = res
                              break
                    
                    if not best_res: 
                         best_res = data['results'][0]
                    
                    if best_res:
                        search_success = True
                        naf_code = best_res.get('activite_principale')
                        official_name = best_res.get('nom_complet')
                        
                        # Address / Region
                        siege = best_res.get('siege', {})
                        address = siege.get('adresse', best_res.get('adresse', ''))
                        region = siege.get('libelle_region', '')
                        if not region: region = best_res.get('region', '')
                        
                        # Simple Dept Fallback
                        cp = siege.get('code_postal', '')
                        if not region and cp:
                             region = get_region_from_dept(cp)
                        
                        siren = best_res.get('siren')
                        if siren: link_url = f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}"
        except Exception as e:
            print(f"API Call Error: {e}")

        # 3. Determine Final Result
        # CAS A: API Found something
        if search_success:
            # If we had a forced sector from overrides, use it
            final_sector = forced_sector if forced_sector else get_sector_from_naf(naf_code)
            
            # If still unknown sector, maybe fallback to web later? For now let's say API is authoritative for identity
            if not final_sector: final_sector = "Unknown" # Or could chain to web search

            return {
                "Input": raw_input,
                "Nom Officiel": official_name,
                "Secteur": final_sector,
                "Détail": "Override + API" if forced_sector else f"Code NAF: {naf_code}",
                "Source": "Officiel (API)",
                "Score": "100%",
                "Adresse": address,
                "Région": region,
                "Lien": link_url
            }
            
        # CAS B: API Failed but we have an Override
        if target_override:
             ov = target_override
             # Check for manual siren
             manual_link = f"https://annuaire-entreprises.data.gouv.fr/entreprise/{ov['Siren']}" if ov.get('Siren') else f"https://annuaire-entreprises.data.gouv.fr/rechercher?q={ov['Nom Officiel'].replace(' ', '+')}"
             
             return {
                "Input": raw_input,
                "Nom Officiel": ov["Nom Officiel"],
                "Secteur": ov["Secteur"],
                "Détail": "Override (API Echoit)",
                "Source": "Base Interne",
                "Score": "100%",
                "Adresse": ov.get("Adresse", "Non renseigné"),
                "Région": ov.get("Région", "Non renseigné"),
                "Lien": manual_link
            }

        # 4. Fallback: Web Search (Simple)

        # 4. Fallback: Web Search (Simple)
        sector_web, source_web, score_web, title_web = analyze_web_content(company_name)
        
        final_link = link_url
        if final_link == "-" or not final_link:
             # Fallback to general search if no specific SIREN link found
             final_link = f"https://annuaire-entreprises.data.gouv.fr/rechercher?q={company_name.replace(' ', '+')}"

        if sector_web:
             return {
                "Input": raw_input,
                "Nom Officiel": title_web if title_web and len(title_web) < 60 else official_name,
                "Secteur": sector_web,
                "Détail": f"Web Analysis ({score_web})",
                "Source": source_web,
                "Score": f"{score_web}",
                "Adresse": address if address != "Non renseigné" else "International / Web",
                "Région": region if region != "Non renseigné" else "Monde",
                "Lien": final_link
             }

        # 5. Nothing Found
        return {
            "Input": raw_input,
            "Nom Officiel": official_name,
            "Secteur": "Non Trouvé",
            "Détail": "Aucun résultat probant",
            "Source": "Échec",
            "Score": "0",
            "Adresse": "-", "Région": "-", "Lien": "-"
        }

    except Exception as e:
        return { 
            "Input": raw_input, 
            "Nom Officiel": "Erreur", 
            "Secteur": "Erreur", 
            "Détail": str(e), 
            "Source": "Crash", 
            "Score": "0", 
            "Adresse": "-", "Région": "-", "Lien": "-" 
        }

# --- Routes ---

@app.route('/')
def index():
    sectors_list = sorted(list(SECTOR_CONFIG.keys()))
    return render_template('index.html', sectors=sectors_list)

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
    app.run(debug=True, port=5001, host='0.0.0.0')
