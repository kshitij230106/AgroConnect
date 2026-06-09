"""
AgroConnect Rasa Custom Actions
================================
Node-level validation & recovery implementation.

Key design principle
--------------------
Every "node" (district slot, product slot) validates its input inline
inside the action itself — no Rasa Forms are used. This means:

  • Invalid input → error message + re-ask SAME question
  • ALL previously collected slots are PRESERVED
  • Conversation never rewinds to an earlier node
  • The fallback action is context-aware and re-prompts the correct node

Node map
--------
  Node 0  – Greeting / entry point
  Node 1  – District collection        (ActionHandleDistrict)
  Node 2  – Product collection         (ActionHandleProduct)
  Node 3  – Retailer results display   (embedded in Node 2 on success)

  Flow 2  – Auto-location + product    (ActionSearchProductNearMe)
  Flow 1b – Inline district+product    (ActionSearchProductByDistrict / ActionSmartSearch)

Validation return contract
--------------------------
  Valid   → set slot, advance conversation
  Invalid → show error + re-ask SAME node, DO NOT change any other slot

Fallback contract (ActionHandleFallback)
-----------------------------------------
  Node 1 (district = None)             → re-prompt district, no slot changes
  Node 2 (district set, no results)    → re-prompt product, district preserved
  Node 3 (results_shown = True)        → "I didn't understand" + FULL RESET to Node 1
                                         (district, product, results_shown all cleared)
"""

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.types import DomainDict
import pandas as pd
import os
import math
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator
from spellchecker import SpellChecker


# ── Constants ────────────────────────────────────────────────────────────────

VALID_DISTRICTS = [
    "bhadohi", "pilibhit", "pratapgarh", "rae bareli",
    "rampur", "saharanpur", "sambhal", "sant kabeer nagar", "shahjahanpur",
]

PRODUCT_KEYWORDS = {
    # English
    "urea": "urea",
    "neem urea": "urea",
    "neem coated urea": "urea",
    "dap": "dap",
    "di ammonium phosphate": "dap",
    "mop": "mop",
    "muriate of potash": "mop",
    "potash": "mop",
    "npks": "npks",
    "npk": "npks",
    "ssp": "ssp",
    "single super phosphate": "ssp",
    "fom": "fom",
    "fertilizer": "urea",
    # Hindi
    "यूरिया": "urea",
    "युरिया": "urea",
    "नीम कोटेड यूरिया": "urea",
    "डीएपी": "dap",
    "डी ए पी": "dap",
    "एमओपी": "mop",
    "पोटाश": "mop",
    "एनपीके": "npks",
    "एनपीकेएस": "npks",
    "एसएसपी": "ssp",
    "एफओएम": "fom",
    "खाद": "urea",
    "उर्वरक": "urea",
}

DISTRICT_TRANSLATIONS = {
    "भदोही": "bhadohi",
    "पीलीभीत": "pilibhit",
    "प्रतापगढ़": "pratapgarh",
    "रायबरेली": "rae bareli",
    "रामपुर": "rampur",
    "सहारनपुर": "saharanpur",
    "संभल": "sambhal",
    "संत कबीर नगर": "sant kabeer nagar",
    "शाहजहांपुर": "shahjahanpur",
}

PRODUCT_DISPLAY = {
    "urea":  {"hi": "यूरिया", "en": "UREA"},
    "dap":   {"hi": "डीएपी", "en": "DAP"},
    "mop":   {"hi": "एमओपी (पोटाश)", "en": "MOP"},
    "npks":  {"hi": "एनपीकेएस", "en": "NPKS"},
    "ssp":   {"hi": "एसएसपी", "en": "SSP"},
    "fom":   {"hi": "एफओएम", "en": "FOM"},
}

EXCEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "Retailer Stock Sample data.xlsx",
)

KEEP_ORIGINAL = [
    "Bhadohi", "Pilibhit", "Pratapgarh", "Rae Bareli", "Rampur",
    "Saharanpur", "Sambhal", "Sant Kabeer Nagar", "Shahjahanpur",
]

DOMAIN_WORDS = [
    "urea", "dap", "mop", "npks", "npk", "ssp", "fom",
    "bhadohi", "pilibhit", "pratapgarh", "rae", "bareli",
    "rampur", "saharanpur", "sambhal", "sant", "kabeer",
    "nagar", "shahjahanpur", "fertilizer", "potash",
    "retailer", "district", "product",
]

spell = SpellChecker()
spell.word_frequency.load_words(DOMAIN_WORDS)

# ── Excel cache ──────────────────────────────────────────────────────────────

_DF_CACHE = None


def load_data():
    global _DF_CACHE
    if _DF_CACHE is not None:
        return _DF_CACHE
    df = pd.read_excel(EXCEL_PATH)
    df.columns = [col.strip().lower() for col in df.columns]
    df["district name"]      = df["district name"].astype(str).str.lower().str.strip()
    df["product group name"] = df["product group name"].astype(str).str.lower().str.strip()
    df["agency name"]        = df["agency name"].astype(str).str.strip()
    df["retailer id"]        = df["retailer id"].astype(str).str.strip()
    df["company name"]       = df["company name"].astype(str).str.strip()
    if "plant name" in df.columns:
        df["plant name"]     = df["plant name"].astype(str).str.strip()
    df["latitude"]           = pd.to_numeric(df["latitude"],  errors="coerce")
    df["longitude"]          = pd.to_numeric(df["longitude"], errors="coerce")
    df["quantity(mt.)"]      = pd.to_numeric(df["quantity(mt.)"], errors="coerce").fillna(0).round(2)
    _DF_CACHE = df
    return _DF_CACHE


# ── Utilities ────────────────────────────────────────────────────────────────

def correct_spelling(text: str) -> str:
    try:
        words = text.lower().split()
        corrected = []
        for word in words:
            if word.isdigit() or len(word) <= 2:
                corrected.append(word)
                continue
            if word in DOMAIN_WORDS:
                corrected.append(word)
                continue
            correction = spell.correction(word)
            corrected.append(correction if correction and correction != word else word)
        return " ".join(corrected)
    except Exception:
        return text


def haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return round(R * 2 * math.asin(math.sqrt(a)), 2)


def detect_language(text: str) -> str:
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return "hi"
    for ch in text:
        if "\u0B80" <= ch <= "\u0BFF":
            return "ta"
    try:
        if len(text.strip()) >= 10:
            lang = detect(text)
            if lang in ["hi", "ta"]:
                return lang
    except LangDetectException:
        pass
    return "en"


def get_lang(tracker, user_message: str) -> str:
    detected = detect_language(user_message)
    return detected if detected != "en" else "en"


def translate(text: str, target_lang: str) -> str:
    if target_lang == "en":
        return text
    try:
        placeholders = {}
        modified_text = text
        for i, word in enumerate(KEEP_ORIGINAL):
            placeholder = f"__KEEP{i}__"
            if word in modified_text or word.lower() in modified_text.lower():
                modified_text = modified_text.replace(word, placeholder)
                modified_text = modified_text.replace(word.lower(), placeholder)
                placeholders[placeholder] = word
        translated = GoogleTranslator(source="en", target=target_lang).translate(modified_text)
        for placeholder, original in placeholders.items():
            translated = translated.replace(placeholder, original)
        return translated if translated else text
    except Exception:
        return text


def say(dispatcher, text: str, lang: str):
    dispatcher.utter_message(text=translate(text, lang))


def display_product_name(product_key: str, lang: str) -> str:
    key = product_key.lower()
    if key in PRODUCT_DISPLAY:
        return PRODUCT_DISPLAY[key].get(lang, PRODUCT_DISPLAY[key]["en"])
    return product_key.upper()


def build_product_list(products: list, lang: str) -> str:
    return "\n".join(["- " + display_product_name(p, lang) for p in sorted(products)])


def build_retailer_table(
    filtered: pd.DataFrame,
    lang: str,
    farmer_lat=None,
    farmer_lon=None,
) -> str:
    if farmer_lat and farmer_lon:
        filtered = filtered.copy()
        filtered["distance_km"] = filtered.apply(
            lambda row: haversine(farmer_lat, farmer_lon, row["latitude"], row["longitude"])
            if pd.notna(row["latitude"]) and pd.notna(row["longitude"]) else 9999,
            axis=1,
        )
        filtered = filtered.sort_values("distance_km").head(10)
        show_distance = True
    else:
        filtered = filtered.head(10)
        show_distance = False

    if lang == "hi":
        headers = ["#", "रिटेलर ID", "एजेंसी का नाम", "कंपनी", "मात्रा (MT)"]
        if show_distance:
            headers.append("दूरी (KM)")
        headers.append("मैप")
    else:
        headers = ["#", "Retailer ID", "Agency Name", "Company", "Qty (MT)"]
        if show_distance:
            headers.append("Distance (KM)")
        headers.append("Directions")

    rows = ""
    for i, (_, row) in enumerate(filtered.iterrows(), 1):
        dist_cell = f"<td>{row['distance_km']} KM</td>" if show_distance else ""
        maps_url = f"https://www.google.com/maps/search/?api=1&query={row['latitude']},{row['longitude']}"
        direction_cell = f'<td><a href="{maps_url}" target="_blank">📍 Directions</a></td>'
        rows += f"""
        <tr>
          <td>{i}</td>
          <td>{row['retailer id']}</td>
          <td>{row['agency name']}</td>
          <td>{row['company name']}</td>
          <td>{row['quantity(mt.)']}</td>
          {dist_cell}
          {direction_cell}
        </tr>"""

    header_cells = "".join(f"<th>{h}</th>" for h in headers)
    return f"""<table class="retailer-table">
  <thead><tr>{header_cells}</tr></thead>
  <tbody>{rows}
  </tbody>
</table>"""


# ── Finders ──────────────────────────────────────────────────────────────────

def find_district(user_message: str, districts: list) -> str:
    """
    Returns a matched district string (lowercase) or None.
    Tries: direct substring → Hindi translation → spell-correction.
    """
    lower = user_message.lower()
    for district in districts:
        if district in lower:
            return district
    for translated_name, english_name in DISTRICT_TRANSLATIONS.items():
        if translated_name in user_message:
            return english_name
    lang = detect_language(user_message)
    if lang == "en":
        corrected = correct_spelling(user_message)
        if corrected != lower:
            for district in districts:
                if district in corrected:
                    return district
    return None


def find_product(user_message: str) -> str:
    """
    Returns a canonical product key (e.g. 'urea') or None.
    Tries: keyword match → spell-correction.
    """
    lower = user_message.lower()
    for keyword, full_name in PRODUCT_KEYWORDS.items():
        if keyword in lower or keyword in user_message:
            return full_name
    lang = detect_language(user_message)
    if lang == "en":
        corrected = correct_spelling(user_message)
        if corrected != lower:
            for keyword, full_name in PRODUCT_KEYWORDS.items():
                if keyword in corrected:
                    return full_name
    return None


# ── Node validation helpers ──────────────────────────────────────────────────

def _reprompt_district(dispatcher: CollectingDispatcher, lang: str):
    """
    Node 1 re-prompt: invalid district input detected.
    Emits error message and re-asks for district.
    Does NOT touch any other slot.
    """
    if lang == "hi":
        dispatcher.utter_message(text=(
            "❌ माफ़ करें, मैं वह जिला नहीं समझ पाया।\n\n"
            "कृपया नीचे दिए गए जिलों में से एक चुनें:\n"
            "- Bhadohi\n- Pilibhit\n- Pratapgarh\n- Rae Bareli\n"
            "- Rampur\n- Saharanpur\n- Sambhal\n"
            "- Sant Kabeer Nagar\n- Shahjahanpur\n\n"
            "अपने जिले का नाम टाइप करें।"
        ))
    else:
        say(dispatcher,
            "❌ Sorry, I didn't understand that district.\n\n"
            "Please select a valid district from the list below:\n"
            "- Bhadohi\n- Pilibhit\n- Pratapgarh\n- Rae Bareli\n"
            "- Rampur\n- Saharanpur\n- Sambhal\n"
            "- Sant Kabeer Nagar\n- Shahjahanpur\n\n"
            "Please type your district name.", lang)


def _reprompt_product(
    dispatcher: CollectingDispatcher,
    district: str,
    lang: str,
    df: pd.DataFrame,
):
    """
    Node 2 re-prompt: invalid product input detected.
    Emits error message, shows available products for the saved district,
    and re-asks for product. Does NOT touch the district slot.
    """
    products = (
        df[df["district name"] == district]["product group name"]
        .dropna().unique().tolist()
    )
    product_list = build_product_list(products, lang)

    if lang == "hi":
        dispatcher.utter_message(text=(
            "❌ माफ़ करें, वह उत्पाद मान्य नहीं है।\n\n"
            + district.title() + " में उपलब्ध उत्पाद:\n\n"
            + product_list
            + "\n\nकृपया ऊपर से एक उत्पाद का नाम टाइप करें।\n"
            "या NO कहें जिला बदलने के लिए।"
        ))
    else:
        say(dispatcher,
            "❌ Sorry, that is not a valid product.\n\n"
            "Available products in " + district.title() + ":\n\n"
            + product_list
            + "\n\nPlease enter a valid product from the list above.\n"
            "Or say NO to change district.", lang)


# ── Standard actions ─────────────────────────────────────────────────────────

class ActionGreet(Action):
    def name(self): return "action_greet"

    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        say(dispatcher,
            "Hello! Welcome to AgroConnect. I help you find fertilizer retailers.\n\n"
            "Which district are you from?\n"
            "Available: Bhadohi, Pilibhit, Pratapgarh, Rae Bareli, Rampur, "
            "Saharanpur, Sambhal, Sant Kabeer Nagar, Shahjahanpur\n\n"
            "Or say NO to exit.", lang)
        return [SlotSet("language", lang)]


class ActionGoodbye(Action):
    def name(self): return "action_goodbye"

    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        say(dispatcher, "Goodbye! Happy farming!", lang)
        return [SlotSet("language", lang)]


class ActionThanks(Action):
    def name(self): return "action_thanks"

    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        say(dispatcher, "You are welcome! Let me know if you need anything else.", lang)
        return [SlotSet("language", lang)]


class ActionHelp(Action):
    def name(self): return "action_help"

    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        say(dispatcher,
            "Tell me your district first. Then I will show available products. "
            "Then type the product name to find nearest retailers.", lang)
        return [SlotSet("language", lang)]


class ActionHowAreYou(Action):
    def name(self): return "action_how_are_you"

    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        say(dispatcher,
            "I am fine, thank you for asking! "
            "Now let us find fertilizer retailers for you.\n\n"
            "Which district are you from?\n"
            "Available: Bhadohi, Pilibhit, Pratapgarh, Rae Bareli, Rampur, "
            "Saharanpur, Sambhal, Sant Kabeer Nagar, Shahjahanpur", lang)
        return [SlotSet("language", lang)]


class ActionDenyDistrict(Action):
    def name(self): return "action_deny_district"

    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        say(dispatcher, "Okay! No problem. Come back anytime. Goodbye!", lang)
        return [
            SlotSet("district", None),
            SlotSet("product", None),
            SlotSet("results_shown", False),
            SlotSet("language", None),
        ]


class ActionDenyProduct(Action):
    def name(self): return "action_deny_product"

    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        say(dispatcher,
            "Okay! Do you want to search in a different district?\n"
            "Type the district name or say goodbye to exit.", lang)
        return [
            SlotSet("product", None),
            SlotSet("results_shown", False),
            SlotSet("language", lang),
        ]


class ActionRestartConversation(Action):
    def name(self): return "action_restart_conversation"

    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        say(dispatcher,
            "Let us start over!\n\n"
            "Which district are you looking for?\n"
            "Available: Bhadohi, Pilibhit, Pratapgarh, Rae Bareli, Rampur, "
            "Saharanpur, Sambhal, Sant Kabeer Nagar, Shahjahanpur\n\n"
            "Or say NO to exit.", lang)
        return [
            SlotSet("district", None),
            SlotSet("product", None),
            SlotSet("results_shown", False),
        ]


# ── Node 1: District ─────────────────────────────────────────────────────────

class ActionHandleDistrict(Action):
    """
    NODE 1 — District collection & validation.

    Valid input   → set district slot, list products, advance to Node 2.
    Invalid input → call _reprompt_district(), return [language only] (no slot changes).

    Context retention guarantee:
      On failure, ONLY SlotSet("language") is returned so all existing slots
      (product, results_shown) remain untouched.
    """
    def name(self): return "action_handle_district"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ):
        user_message = tracker.latest_message.get("text", "").strip()
        lang = get_lang(tracker, user_message)

        # ── Validation ────────────────────────────────────────────────────
        try:
            df = load_data()
            districts = df["district name"].dropna().unique().tolist()
            district_found = find_district(user_message, districts)
        except Exception as e:
            say(dispatcher,
                "Something went wrong loading district data: " + str(e) +
                "\n\nPlease type your district again.", lang)
            return [SlotSet("language", lang)]

        # INVALID → re-prompt Node 1, preserve ALL slots
        if not district_found:
            _reprompt_district(dispatcher, lang)
            return [SlotSet("language", lang)]

        # ── Valid district: check products exist ──────────────────────────
        products = (
            df[df["district name"] == district_found]["product group name"]
            .dropna().unique().tolist()
        )

        if not products:
            say(dispatcher,
                "No products are currently available in " + district_found.title() +
                ". Please try a different district.\n\n"
                "Available: Bhadohi, Pilibhit, Pratapgarh, Rae Bareli, Rampur, "
                "Saharanpur, Sambhal, Sant Kabeer Nagar, Shahjahanpur", lang)
            return [SlotSet("language", lang)]

        # ── Success: advance to Node 2 ────────────────────────────────────
        product_list = build_product_list(products, lang)

        if lang == "hi":
            dispatcher.utter_message(text=(
                "✅ " + district_found.title() + " में उपलब्ध उत्पाद:\n\n"
                + product_list
                + "\n\nआप कौन सा उत्पाद ढूंढ रहे हैं?\n"
                "या NO कहें वापस जाने के लिए।"
            ))
        else:
            say(dispatcher,
                "✅ Products available in " + district_found.title() + ":\n\n"
                + product_list
                + "\n\nWhich product are you looking for?\n"
                "Or say NO to go back.", lang)

        return [
            SlotSet("district", district_found),
            SlotSet("product", None),
            SlotSet("results_shown", False),
            SlotSet("language", lang),
        ]


# ── Node 2: Product ──────────────────────────────────────────────────────────

class ActionHandleProduct(Action):
    """
    NODE 2 — Product collection, validation, and retailer search (Node 3).

    Valid product + retailers found → display results, set results_shown=True.
    Valid product + no stock        → inform user, re-ask product (stay Node 2).
    Invalid product                 → call _reprompt_product(), no slot changes.
    No district set                 → redirect back to Node 1.

    Context retention guarantee:
      On product validation failure, ONLY the language slot is updated.
      The district slot is NEVER touched by this action on failure.
    """
    def name(self): return "action_handle_product"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ):
        user_message = tracker.latest_message.get("text", "").strip()
        lang = get_lang(tracker, user_message)
        district_found = tracker.get_slot("district")

        metadata = tracker.latest_message.get("metadata", {})
        farmer_lat = metadata.get("farmer_lat")
        farmer_lon = metadata.get("farmer_lon")

        # Guard: district must be set before product can be collected
        if not district_found:
            say(dispatcher,
                "Please tell me your district first.\n"
                "Available: Bhadohi, Pilibhit, Pratapgarh, Rae Bareli, Rampur, "
                "Saharanpur, Sambhal, Sant Kabeer Nagar, Shahjahanpur", lang)
            return [SlotSet("language", lang)]

        try:
            df = load_data()
            product_found = find_product(user_message)

            # INVALID PRODUCT → re-prompt Node 2, preserve district
            if not product_found:
                _reprompt_product(dispatcher, district_found, lang, df)
                return [SlotSet("language", lang)]

            # Check stock availability
            filtered = df[
                (df["district name"] == district_found)
                & (df["product group name"] == product_found)
                & (df["quantity(mt.)"] > 0)
            ]

            if filtered.empty:
                products = (
                    df[df["district name"] == district_found]["product group name"]
                    .dropna().unique().tolist()
                )
                product_list = build_product_list(products, lang)
                product_display = display_product_name(product_found, lang)

                if lang == "hi":
                    dispatcher.utter_message(text=(
                        "❌ माफ़ करें! " + product_display
                        + " " + district_found.title() + " में उपलब्ध नहीं है।\n\n"
                        "यहाँ उपलब्ध उत्पाद:\n\n" + product_list
                        + "\n\nकृपया ऊपर से एक उत्पाद चुनें।\n"
                        "या NO कहें जिला बदलने के लिए।"
                    ))
                else:
                    say(dispatcher,
                        "❌ Sorry! " + product_display
                        + " is not available in " + district_found.title()
                        + ".\n\nAvailable products:\n\n" + product_list
                        + "\n\nPlease choose one of the products above.\n"
                        "Or say NO to change district.", lang)

                return [
                    SlotSet("product", None),
                    SlotSet("language", lang),
                ]

            # ── Node 3: Results ───────────────────────────────────────────
            product_display = display_product_name(product_found, lang)
            table_html = build_retailer_table(filtered, lang, farmer_lat, farmer_lon)

            if farmer_lat and farmer_lon:
                if lang == "hi":
                    header = ("आपके नजदीकी " + district_found.title() + " में "
                              + product_display + " बेचने वाले विक्रेता (दूरी के अनुसार):\n")
                    footer = ("\nदूसरा उत्पाद खोजने के लिए उत्पाद का नाम टाइप करें।\n"
                              "जिला बदलने के लिए 'जिला बदलें' कहें।\n"
                              "बाहर निकलने के लिए 'अलविदा' कहें।")
                else:
                    header = ("Nearest retailers selling " + product_display
                              + " in " + district_found.title() + " (sorted by distance):\n")
                    footer = ("\nType another product to search again.\n"
                              "Or say 'change district' to go back.\n"
                              "Or say 'goodbye' to exit.")
            else:
                if lang == "hi":
                    header = (district_found.title() + " में " + product_display
                              + " बेचने वाले विक्रेता:\n")
                    footer = ("\nदूसरा उत्पाद खोजने के लिए उत्पाद का नाम टाइप करें।\n"
                              "जिला बदलने के लिए 'जिला बदलें' कहें।\n"
                              "बाहर निकलने के लिए 'अलविदा' कहें।")
                else:
                    header = ("Retailers selling " + product_display
                              + " in " + district_found.title() + ":\n")
                    footer = ("\nType another product to search again.\n"
                              "Or say 'change district' to go back.\n"
                              "Or say 'goodbye' to exit.")

            dispatcher.utter_message(text=header + table_html + footer)
            return [
                SlotSet("product", product_found),
                SlotSet("results_shown", True),
                SlotSet("language", lang),
            ]

        except Exception as e:
            say(dispatcher,
                "Something went wrong: " + str(e)
                + "\n\nPlease type the product name again.", lang)
            return [SlotSet("language", lang)]


# ── Flow 1b: Inline district + product ──────────────────────────────────────

class ActionSearchProductByDistrict(Action):
    """
    Flow 1b — User mentions both district + product in a single message
    (e.g. "urea in bhadohi").
    """
    def name(self): return "action_search_product_by_district"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ):
        user_message = tracker.latest_message.get("text", "").strip()
        lang = get_lang(tracker, user_message)

        try:
            df = load_data()
            all_districts = df["district name"].dropna().unique().tolist()

            district_found = None
            product_found = None

            for entity in tracker.latest_message.get("entities", []):
                if entity["entity"] == "district" and not district_found:
                    district_found = entity["value"].lower().strip()
                if entity["entity"] == "product" and not product_found:
                    product_found = entity["value"].lower().strip()

            if not district_found:
                district_found = find_district(user_message, all_districts)
            if not product_found:
                product_found = find_product(user_message)

            if not district_found:
                district_found = tracker.get_slot("district")

            if not district_found:
                _reprompt_district(dispatcher, lang)
                return [SlotSet("language", lang)]

            if not product_found:
                district_products = (
                    df[df["district name"] == district_found]["product group name"]
                    .dropna().unique().tolist()
                )
                if not district_products:
                    say(dispatcher,
                        "No products found in " + district_found.title()
                        + ". Try another district.", lang)
                    return [SlotSet("language", lang)]

                product_list = build_product_list(district_products, lang)
                say(dispatcher,
                    "✅ Products available in " + district_found.title() + ":\n\n"
                    + product_list + "\n\nWhich product are you looking for?", lang)
                return [
                    SlotSet("district", district_found),
                    SlotSet("product", None),
                    SlotSet("results_shown", False),
                    SlotSet("language", lang),
                ]

            filtered = df[
                (df["district name"] == district_found)
                & (df["product group name"] == product_found)
                & (df["quantity(mt.)"] > 0)
            ].copy()

            if filtered.empty:
                _reprompt_product(dispatcher, district_found, lang, df)
                return [
                    SlotSet("district", district_found),
                    SlotSet("product", None),
                    SlotSet("language", lang),
                ]

            metadata = tracker.latest_message.get("metadata", {})
            farmer_lat = metadata.get("farmer_lat")
            farmer_lon = metadata.get("farmer_lon")

            product_display = display_product_name(product_found, lang)
            table_html = build_retailer_table(filtered, lang, farmer_lat, farmer_lon)

            if farmer_lat and farmer_lon:
                header = (
                    "Nearest retailers selling " + product_display
                    + " in " + district_found.title() + " (sorted by distance):\n"
                    if lang == "en" else
                    district_found.title() + " में " + product_display
                    + " बेचने वाले नजदीकी विक्रेता (दूरी के अनुसार):\n"
                )
            else:
                header = (
                    "Retailers selling " + product_display
                    + " in " + district_found.title() + ":\n"
                    if lang == "en" else
                    district_found.title() + " में " + product_display
                    + " बेचने वाले विक्रेता:\n"
                )

            footer = (
                "\nType another product name to search again.\n"
                "Or say 'change district' to search a different district.\n"
                "Or say 'goodbye' to exit."
                if lang == "en" else
                "\nदूसरा उत्पाद खोजने के लिए उत्पाद का नाम टाइप करें।\n"
                "जिला बदलने के लिए 'जिला बदलें' कहें।\n"
                "बाहर निकलने के लिए 'अलविदा' कहें।"
            )

            dispatcher.utter_message(text=header + table_html + footer)
            return [
                SlotSet("district", district_found),
                SlotSet("product", product_found),
                SlotSet("results_shown", True),
                SlotSet("language", lang),
            ]

        except Exception as e:
            say(dispatcher,
                "Something went wrong while searching: " + str(e) + "\n\nPlease try again.", lang)
            return [SlotSet("language", lang)]


# ── Flow 2: Near-me (auto-location) ─────────────────────────────────────────

class ActionSearchProductNearMe(Action):
    """
    Flow 2 — User requests retailers near their GPS location.
    """
    def name(self): return "action_search_product_near_me"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ):
        user_message = tracker.latest_message.get("text", "").strip()
        lang = get_lang(tracker, user_message)
        metadata = tracker.latest_message.get("metadata", {})
        farmer_lat = metadata.get("farmer_lat")
        farmer_lon = metadata.get("farmer_lon")

        if not farmer_lat or not farmer_lon:
            say(dispatcher,
                "📍 To find retailers near you, I need your location.\n\n"
                "Please enable location access in your browser and try again.\n"
                "Or, you can type a district name to search manually.\n\n"
                "Available districts: Bhadohi, Pilibhit, Pratapgarh, Rae Bareli, "
                "Rampur, Saharanpur, Sambhal, Sant Kabeer Nagar, Shahjahanpur", lang)
            return [SlotSet("language", lang)]

        try:
            df = load_data()
            product_found = None

            for entity in tracker.latest_message.get("entities", []):
                if entity["entity"] == "product" and not product_found:
                    product_found = entity["value"].lower().strip()

            if not product_found:
                product_found = find_product(user_message)
            if not product_found:
                product_found = tracker.get_slot("product")

            district_from_conv = tracker.get_slot("district")

            if not product_found:
                if district_from_conv:
                    district_products = (
                        df[df["district name"] == district_from_conv]["product group name"]
                        .dropna().unique().tolist()
                    )
                    if district_products:
                        product_list = build_product_list(district_products, lang)
                        say(dispatcher,
                            "❌ Sorry, I didn't recognise a product in your message.\n\n"
                            "Available products in " + district_from_conv.title() + ":\n\n"
                            + product_list + "\n\nWhich product are you looking for near you?", lang)
                        return [SlotSet("language", lang)]

                all_products = df["product group name"].dropna().unique().tolist()
                product_list = build_product_list(all_products, lang)
                say(dispatcher,
                    "❌ Sorry, I didn't recognise a product in your message.\n\n"
                    "Please tell me which product you are looking for near you:\n"
                    + product_list, lang)
                return [SlotSet("language", lang)]

            if district_from_conv:
                filtered = df[
                    (df["district name"] == district_from_conv)
                    & (df["product group name"] == product_found)
                    & (df["quantity(mt.)"] > 0)
                ].copy()
                location_context = " in " + district_from_conv.title()
            else:
                filtered = df[
                    (df["product group name"] == product_found)
                    & (df["quantity(mt.)"] > 0)
                ].copy()
                location_context = " near you"

            if filtered.empty:
                product_display = display_product_name(product_found, lang)
                if district_from_conv:
                    say(dispatcher,
                        "❌ Sorry! " + product_display
                        + " is not available in " + district_from_conv.title()
                        + ".\n\nTry a different product or district.", lang)
                else:
                    say(dispatcher,
                        "❌ Sorry! " + product_display
                        + " is not currently available near you.\n\nTry a different product.", lang)
                return [
                    SlotSet("product", None),
                    SlotSet("language", lang),
                ]

            product_display = display_product_name(product_found, lang)
            header = (
                "🛒 आपके नजदीकी" + location_context + " में "
                + product_display + " बेचने वाले विक्रेता:\n\n"
                if lang == "hi" else
                "🛒 Nearest retailers selling " + product_display + location_context + ":\n\n"
            )
            footer = (
                "\nType another product to search nearby.\n"
                "Or type a district name to search there.\n"
                "Or say 'goodbye' to exit."
                if lang == "en" else
                "\nदूसरा उत्पाद खोजने के लिए उत्पाद का नाम टाइप करें।\n"
                "या जिले का नाम टाइप करें।\n"
                "बाहर निकलने के लिए 'अलविदा' कहें।"
            )
            table_html = build_retailer_table(filtered, lang, farmer_lat, farmer_lon)
            dispatcher.utter_message(text=header + table_html + footer)

            return [
                SlotSet("product", product_found),
                SlotSet("district", district_from_conv),
                SlotSet("results_shown", True),
                SlotSet("language", lang),
            ]

        except Exception as e:
            say(dispatcher, "Something went wrong: " + str(e) + "\n\nPlease try again.", lang)
            return [SlotSet("language", lang)]


# ── Flow 1b alt: Smart search ────────────────────────────────────────────────

class ActionSmartSearch(Action):
    """
    Smart search — district + product hinted together in Hindi/Hinglish.
    Same validation contract as ActionSearchProductByDistrict.
    """
    def name(self): return "action_smart_search"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ):
        user_message = tracker.latest_message.get("text", "").strip()
        lang = get_lang(tracker, user_message)
        metadata = tracker.latest_message.get("metadata", {})
        farmer_lat = metadata.get("farmer_lat")
        farmer_lon = metadata.get("farmer_lon")

        try:
            df = load_data()
            districts = df["district name"].dropna().unique().tolist()
            district_found = find_district(user_message, districts) or tracker.get_slot("district")
            product_found  = find_product(user_message)

            if not district_found:
                _reprompt_district(dispatcher, lang)
                return [SlotSet("language", lang)]

            if not product_found:
                products = (
                    df[df["district name"] == district_found]["product group name"]
                    .dropna().unique().tolist()
                )
                product_list = build_product_list(products, lang)
                say(dispatcher,
                    "✅ Products available in " + district_found.title() + ":\n\n"
                    + product_list + "\n\nWhich product are you looking for?", lang)
                return [
                    SlotSet("district", district_found),
                    SlotSet("product", None),
                    SlotSet("results_shown", False),
                    SlotSet("language", lang),
                ]

            filtered = df[
                (df["district name"] == district_found)
                & (df["product group name"] == product_found)
                & (df["quantity(mt.)"] > 0)
            ]

            if filtered.empty:
                _reprompt_product(dispatcher, district_found, lang, df)
                return [
                    SlotSet("district", district_found),
                    SlotSet("product", None),
                    SlotSet("language", lang),
                ]

            product_display = display_product_name(product_found, lang)
            table_html = build_retailer_table(filtered, lang, farmer_lat, farmer_lon)

            header = (
                "Nearest retailers selling " + product_display
                + " in " + district_found.title() + " (sorted by distance):\n"
                if farmer_lat else
                "Retailers selling " + product_display
                + " in " + district_found.title() + ":\n"
            )
            footer = (
                "\nType another product to search again.\n"
                "Or say 'change district' to go back.\n"
                "Or say 'goodbye' to exit."
            )
            dispatcher.utter_message(text=header + table_html + footer)
            return [
                SlotSet("district", district_found),
                SlotSet("product", product_found),
                SlotSet("results_shown", True),
                SlotSet("language", lang),
            ]

        except Exception as e:
            say(dispatcher, "Something went wrong: " + str(e), lang)
            return [SlotSet("language", lang)]


# ── Context-aware fallback ───────────────────────────────────────────────────

class ActionHandleFallback(Action):
    """
    Context-aware fallback — fired on nlu_fallback intent (low NLU confidence)
    OR when input is gibberish/emoji/out-of-domain text during any flow step.

    Decision logic (three-state):
    ─────────────────────────────
    State 1 — district is None (user at Node 1):
        → Re-prompt Node 1 (ask for district again)
        → No slot changes at all

    State 2 — district is set, results_shown is False (user at Node 2):
        → Re-prompt Node 2 (show product list for saved district, ask again)
        → District slot is PRESERVED, only language updated

    State 3 — results_shown is True (user just saw retailer results, Node 3):
        → Say "I didn't understand"
        → FULL RESET: district=None, product=None, results_shown=False
        → Re-prompt Node 1 (ask for district again from scratch)

    This is the ONLY place State 3 behaviour differs from the original code.
    Previously State 3 showed a next-action menu. Now it resets to Node 1.
    """
    def name(self): return "action_handle_fallback"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        district = tracker.get_slot("district")
        results_shown = tracker.get_slot("results_shown")

        # ── State 1: No district yet → re-prompt Node 1 ──────────────────
        if not district:
            _reprompt_district(dispatcher, lang)
            return [SlotSet("language", lang)]

        # ── State 3: Results already shown → FULL RESET to Node 1 ────────
        # Changed from original: used to show next-action menu.
        # Now: clears all slots and re-prompts district (Node 1).
        if results_shown:
            if lang == "hi":
                dispatcher.utter_message(text=(
                    "❌ माफ़ करें, मैं वह नहीं समझ पाया।\n\n"
                    "फिर से शुरू करते हैं।\n\n"
                    "आप किस जिले में हैं?\n"
                    "- Bhadohi\n- Pilibhit\n- Pratapgarh\n- Rae Bareli\n"
                    "- Rampur\n- Saharanpur\n- Sambhal\n"
                    "- Sant Kabeer Nagar\n- Shahjahanpur\n\n"
                    "अपने जिले का नाम टाइप करें।"
                ))
            else:
                say(dispatcher,
                    "❌ Sorry, I didn't understand that.\n\n"
                    "Let us start over.\n\n"
                    "Which district are you in?\n"
                    "- Bhadohi\n- Pilibhit\n- Pratapgarh\n- Rae Bareli\n"
                    "- Rampur\n- Saharanpur\n- Sambhal\n"
                    "- Sant Kabeer Nagar\n- Shahjahanpur\n\n"
                    "Please type your district name.", lang)
            # Full reset — all slots cleared back to initial state
            return [
                SlotSet("district", None),
                SlotSet("product", None),
                SlotSet("results_shown", False),
                SlotSet("language", lang),
            ]

        # ── State 2: District set, no results yet → re-prompt Node 2 ─────
        try:
            df = load_data()
            _reprompt_product(dispatcher, district, lang, df)
        except Exception:
            say(dispatcher,
                "❌ I didn't understand that.\n\n"
                "Please type a valid product name.\n"
                "Try: Urea, DAP, MOP, NPKS, SSP, FOM\n\n"
                "Or say 'change district' to go back.", lang)

        # Language only — district preserved, product stays None
        return [SlotSet("language", lang)]