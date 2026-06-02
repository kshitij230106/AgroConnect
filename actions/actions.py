from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.types import DomainDict
import pandas as pd
import os
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator


PRODUCT_KEYWORDS = {
    "urea": "imported neem coated urea(45 kg)",
    "neem coated urea": "imported neem coated urea(45 kg)",
    "dap": "imported dap",
    "amm sulphate": "amm sulphate",
    "sulphate": "amm sulphate",
    "sulfate": "amm sulphate",
    "ammonium sulphate": "amm sulphate",
    "ammonium sulfate": "amm sulphate",
    "15-15-15-9": "imported 15-15-15-9",
    "15 15 15 9": "imported 15-15-15-9",
    "20-20-0-13": "imported 20-20-0-13",
    "20 20 0 13": "imported 20-20-0-13",
    "यूरिया": "imported neem coated urea(45 kg)",
    "युरिया": "imported neem coated urea(45 kg)",
    "नीम कोटेड यूरिया": "imported neem coated urea(45 kg)",
    "डीएपी": "imported dap",
    "डी ए पी": "imported dap",
    "अमोनियम सल्फेट": "amm sulphate",
    "अमोनियम सलफेट": "amm sulphate",
    "सल्फेट": "amm sulphate",
    "सलफेट": "amm sulphate",
    "யூரியா": "imported neem coated urea(45 kg)",
    "டிஏபி": "imported dap",
    "சல்பேட்": "amm sulphate",
    "அம்மோனியம் சல்பேட்": "amm sulphate",
}

DISTRICT_TRANSLATIONS = {
    # Hindi
    "तिरुपति": "tirupati",
    "गुंटूर": "guntur",
    "एलुरु": "eluru",
    "अनाकापल्ली": "anakapalli",
    "कुरनूल": "kurnool",
    "कर्नूल": "kurnool",

    "अनंतपुर": "anantapur",
    "अन्नमय्या": "annamayya",
    "बापटला": "bapatla",
    "चित्तूर": "chittoor",
    "पूर्व गोदावरी": "east godavari",
    "कोनसीमा": "konaseema",
    "कृष्णा": "krishna",
    "नंद्याल": "nandyal",
    "एनटीआर": "ntr",
    "पालनाडु": "palnadu",
    "प्रकाशम": "prakasam",
    "एसपीएसआर नेल्लोर": "spsr nellore",
    "श्री सत्य साई": "sri sathya sai",
    "पश्चिम गोदावरी": "west godavari",

    # Tamil
    "திருப்பதி": "tirupati",
    "குண்டூர்": "guntur",
    "எலூரு": "eluru",
    "அனகாபல்லி": "anakapalli",
    "கர்நூல்": "kurnool",

    "அனந்தபூர்": "anantapur",
    "அன்னமையா": "annamayya",
    "பாபட்லா": "bapatla",
    "சித்தூர்": "chittoor",
    "கிழக்கு கோதாவரி": "east godavari",
    "கோனசீமா": "konaseema",
    "கிருஷ்ணா": "krishna",
    "நந்த்யால்": "nandyal",
    "என்டிஆர்": "ntr",
    "பால்நாடு": "palnadu",
    "பிரகாசம்": "prakasam",
    "எஸ்பிஎஸ்ஆர் நெல்லூர்": "spsr nellore",
    "ஸ்ரீ சத்ய சாய்": "sri sathya sai",
    "மேற்கு கோதாவரி": "west godavari",
}

PRODUCT_DISPLAY = {
    "imported neem coated urea(45 kg)": {"hi": "यूरिया", "en": "IMPORTED NEEM COATED UREA (45 KG)"},
    "imported dap":                      {"hi": "डीएपी",  "en": "IMPORTED DAP"},
    "amm sulphate":                      {"hi": "अमोनियम सल्फेट", "en": "AMM SULPHATE"},
    "imported 15-15-15-9":               {"hi": "15-15-15-9", "en": "IMPORTED 15-15-15-9"},
    "imported 20-20-0-13":               {"hi": "20-20-0-13", "en": "IMPORTED 20-20-0-13"},
}

EXCEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "Retailer Stock Sample data.xlsx"
)

KEEP_ORIGINAL = [
    "Tirupati", "Guntur", "Eluru", "Anakapalli", "Kurnool",
    "15-15-15-9", "20-20-0-13",
]


# ── Language detection ──────────────────────────────────────

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
    if detected != "en":
        return detected
    return "en"


# ── Translation ─────────────────────────────────────────────

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


# ── Excel loader ────────────────────────────────────────────

def load_data():
    df = pd.read_excel(EXCEL_PATH)
    df.columns = [col.strip().lower() for col in df.columns]
    df["district name"] = df["district name"].astype(str).str.lower().str.strip()
    df["product name"]  = df["product name"].astype(str).str.lower().str.strip()
    df["agency name"]   = df["agency name"].astype(str).str.strip()
    df["retailer id"]   = df["retailer id"].astype(str).str.strip()
    df["company name"]  = df["company name"].astype(str).str.strip()
    df["plant name"]    = df["plant name"].astype(str).str.strip()
    df["quantity(mt.)"] = pd.to_numeric(df["quantity(mt.)"], errors="coerce").fillna(0).round(2)
    return df


# ── Retailer table builder ──────────────────────────────────

def build_retailer_table(filtered: pd.DataFrame, lang: str) -> str:
    """
    Builds an HTML table for display in the React chat bubble.
    Columns: #, Retailer ID, Agency Name, Company, Plant, Qty (MT)
    """
    if lang == "hi":
        headers = ["#", "रिटेलर ID", "एजेंसी का नाम", "कंपनी", "प्लांट", "मात्रा (MT)"]
    elif lang == "ta":
        headers = ["#", "சில்லறை ID", "நிறுவன பெயர்", "நிறுவனம்", "ஆலை", "அளவு (MT)"]
    else:
        headers = ["#", "Retailer ID", "Agency Name", "Company", "Plant", "Qty (MT)"]

    rows = ""
    for i, (_, row) in enumerate(filtered.iterrows(), 1):
        rows += f"""
        <tr>
          <td>{i}</td>
          <td>{row['retailer id']}</td>
          <td>{row['agency name']}</td>
          <td>{row['company name']}</td>
          <td>{row['plant name']}</td>
          <td>{row['quantity(mt.)']}</td>
        </tr>"""

    header_cells = "".join(f"<th>{h}</th>" for h in headers)

    table = f"""<table class="retailer-table">
  <thead><tr>{header_cells}</tr></thead>
  <tbody>{rows}
  </tbody>
</table>"""

    return table


# ── Product display helpers ─────────────────────────────────

def display_product_name(product_key: str, lang: str) -> str:
    key = product_key.lower()
    if key in PRODUCT_DISPLAY:
        return PRODUCT_DISPLAY[key].get(lang, PRODUCT_DISPLAY[key]["en"])
    return product_key.upper()


def build_product_list(products: list, lang: str) -> str:
    return "\n".join(["- " + display_product_name(p, lang) for p in sorted(products)])


# ── District / product finders ──────────────────────────────

def find_district(user_message: str, districts: list) -> str:
    lower = user_message.lower()
    for district in districts:
        if district in lower:
            return district
    for translated_name, english_name in DISTRICT_TRANSLATIONS.items():
        if translated_name in user_message:
            return english_name
    return None


def find_product(user_message: str) -> str:
    lower = user_message.lower()
    for keyword, full_name in PRODUCT_KEYWORDS.items():
        if keyword in lower or keyword in user_message:
            return full_name
    return None


# ── Actions ─────────────────────────────────────────────────

class ActionGreet(Action):
    def name(self): return "action_greet"
    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        say(dispatcher,
            "Hello! Welcome to AgroConnect. I help you find fertilizer retailers.\n\n"
            "Which district are you from?\n"
            "Available: Tirupati, Guntur, Eluru, Anakapalli, Kurnool\n\n"
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
            "Then type the product name to find retailers.", lang)
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
            "Available: Tirupati, Guntur, Eluru, Anakapalli, Kurnool", lang)
        return [SlotSet("language", lang)]


class ActionDenyDistrict(Action):
    def name(self): return "action_deny_district"
    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        say(dispatcher, "Okay! No problem. Come back anytime. Goodbye!", lang)
        return [SlotSet("district", None), SlotSet("product", None), SlotSet("language", None)]


class ActionDenyProduct(Action):
    def name(self): return "action_deny_product"
    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        say(dispatcher,
            "Okay! Do you want to search in a different district?\n"
            "Type the district name or say goodbye to exit.", lang)
        return [SlotSet("product", None), SlotSet("language", lang)]


class ActionRestartConversation(Action):
    def name(self): return "action_restart_conversation"
    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        say(dispatcher,
            "Let us start over!\n\n"
            "Which district are you looking for?\n"
            "Available: Tirupati, Guntur, Eluru, Anakapalli, Kurnool\n\n"
            "Or say NO to exit.", lang)
        return [SlotSet("district", None), SlotSet("product", None)]


class ActionHandleDistrict(Action):
    def name(self): return "action_handle_district"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict):
        user_message = tracker.latest_message.get("text", "").strip()
        lang = get_lang(tracker, user_message)

        try:
            df = load_data()
            districts = df["district name"].dropna().unique().tolist()
            district_found = find_district(user_message, districts)

            if not district_found:
                available = ", ".join(sorted([d.title() for d in districts]))
                say(dispatcher,
                    "I could not find that district.\n\n"
                    "Available districts:\n" + available +
                    "\n\nPlease type your district name.", lang)
                return [SlotSet("district", None), SlotSet("language", lang)]

            products = (
                df[df["district name"] == district_found]
                ["product name"].dropna().unique().tolist()
            )

            if not products:
                say(dispatcher,
                    "No products found in " + district_found.title() +
                    ". Try another district.", lang)
                return [SlotSet("district", None), SlotSet("language", lang)]

            product_list = build_product_list(products, lang)

            if lang == "hi":
                dispatcher.utter_message(text=(
                    district_found.title() + " में उपलब्ध उत्पाद:\n\n" +
                    product_list +
                    "\n\nआप कौन सा उत्पाद ढूंढ रहे हैं?\n"
                    "या NO कहें वापस जाने के लिए।"
                ))
            else:
                say(dispatcher,
                    "Products available in " + district_found.title() +
                    ":\n\n" + product_list +
                    "\n\nWhich product are you looking for?\n"
                    "Or say NO to go back.", lang)

            return [SlotSet("district", district_found), SlotSet("language", lang)]

        except Exception as e:
            say(dispatcher,
                "Something went wrong: " + str(e) +
                "\n\nPlease type your district again.", lang)
            return [SlotSet("district", None), SlotSet("language", lang)]


class ActionHandleProduct(Action):
    def name(self): return "action_handle_product"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict):
        user_message = tracker.latest_message.get("text", "").strip()
        lang = get_lang(tracker, user_message)
        district_found = tracker.get_slot("district")

        if not district_found:
            say(dispatcher,
                "Please tell me your district first.\n"
                "Available: Tirupati, Guntur, Eluru, Anakapalli, Kurnool", lang)
            return [SlotSet("language", lang)]

        try:
            df = load_data()
            products = (
                df[df["district name"] == district_found]
                ["product name"].dropna().unique().tolist()
            )
            product_list = build_product_list(products, lang)
            product_found = find_product(user_message)

            if not product_found:
                if lang == "hi":
                    dispatcher.utter_message(text=(
                        "माफ़ करें! '" + user_message + "' " +
                        district_found.title() + " में उपलब्ध नहीं है।\n\n"
                        "यहाँ उपलब्ध उत्पाद:\n\n" + product_list +
                        "\n\nकृपया ऊपर से एक उत्पाद चुनें।\n"
                        "या NO कहें जिला बदलने के लिए।"
                    ))
                else:
                    say(dispatcher,
                        "Sorry! '" + user_message.title() +
                        "' is not available in " + district_found.title() +
                        ".\n\nAvailable products:\n\n" + product_list +
                        "\n\nPlease type one of the above.\n"
                        "Or say NO to change district.", lang)
                return [SlotSet("language", lang)]

            filtered = df[
                (df["district name"] == district_found) &
                (df["product name"] == product_found)
            ].head(10)

            if filtered.empty:
                if lang == "hi":
                    dispatcher.utter_message(text=(
                        "माफ़ करें! " +
                        display_product_name(product_found, "hi") +
                        " " + district_found.title() +
                        " में उपलब्ध नहीं है।\n\n"
                        "यहाँ उपलब्ध उत्पाद:\n\n" + product_list +
                        "\n\nकृपया ऊपर से एक उत्पाद चुनें।\n"
                        "या NO कहें जिला बदलने के लिए।"
                    ))
                else:
                    say(dispatcher,
                        "Sorry! '" + product_found.upper() +
                        "' is not available in " + district_found.title() +
                        ".\n\nAvailable products:\n\n" + product_list +
                        "\n\nPlease type one of the above.\n"
                        "Or say NO to change district.", lang)
                return [SlotSet("product", None), SlotSet("language", lang)]

            product_display = display_product_name(product_found, lang)
            table_html = build_retailer_table(filtered, lang)

            if lang == "hi":
                header = (
                    district_found.title() + " में " +
                    product_display + " बेचने वाले विक्रेता:\n"
                )
                footer = (
                    "\nदूसरा उत्पाद खोजने के लिए उत्पाद का नाम टाइप करें।\n"
                    "जिला बदलने के लिए 'जिला बदलें' कहें।\n"
                    "बाहर निकलने के लिए 'अलविदा' कहें।"
                )
            else:
                header = (
                    "Retailers selling " + product_display +
                    " in " + district_found.title() + ":\n"
                )
                footer = (
                    "\nType another product to search again.\n"
                    "Or say change district to go back.\n"
                    "Or say goodbye to exit."
                )

            dispatcher.utter_message(text=header + table_html + footer)
            return [SlotSet("product", product_found), SlotSet("language", lang)]

        except Exception as e:
            say(dispatcher,
                "Something went wrong: " + str(e) +
                "\n\nPlease type the product name again.", lang)
            return [SlotSet("language", lang)]


class ActionSmartSearch(Action):
    def name(self): return "action_smart_search"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict):
        user_message = tracker.latest_message.get("text", "").strip()
        lang = get_lang(tracker, user_message)

        try:
            df = load_data()
            districts = df["district name"].dropna().unique().tolist()

            district_found = find_district(user_message, districts)
            product_found  = find_product(user_message)

            if not district_found and not product_found:
                say(dispatcher,
                    "I could not understand your request.\n\n"
                    "Please tell me your district first.\n"
                    "Available: Tirupati, Guntur, Eluru, Anakapalli, Kurnool", lang)
                return [SlotSet("language", lang)]

            if not district_found:
                district_found = tracker.get_slot("district")

            if not district_found:
                if product_found:
                    product_display = display_product_name(product_found, lang)
                    if lang == "hi":
                        say(dispatcher,
                            product_display + " के लिए कौन सा जिला?\n"
                            "उपलब्ध: Tirupati, Guntur, Eluru, Anakapalli, Kurnool", lang)
                    else:
                        say(dispatcher,
                            "Which district do you want " + product_display + " from?\n"
                            "Available: Tirupati, Guntur, Eluru, Anakapalli, Kurnool", lang)
                return [SlotSet("language", lang)]

            if not product_found:
                products = (
                    df[df["district name"] == district_found]
                    ["product name"].dropna().unique().tolist()
                )
                product_list = build_product_list(products, lang)
                if lang == "hi":
                    dispatcher.utter_message(text=(
                        district_found.title() + " में उपलब्ध उत्पाद:\n\n" +
                        product_list +
                        "\n\nआप कौन सा उत्पाद ढूंढ रहे हैं?"
                    ))
                else:
                    say(dispatcher,
                        "Products available in " + district_found.title() +
                        ":\n\n" + product_list +
                        "\n\nWhich product are you looking for?", lang)
                return [SlotSet("district", district_found), SlotSet("language", lang)]

            # Both found — show retailer table
            filtered = df[
                (df["district name"] == district_found) &
                (df["product name"] == product_found)
            ].head(10)

            products = (
                df[df["district name"] == district_found]
                ["product name"].dropna().unique().tolist()
            )
            product_list    = build_product_list(products, lang)
            product_display = display_product_name(product_found, lang)
            table_html      = build_retailer_table(filtered, lang)

            if filtered.empty:
                if lang == "hi":
                    dispatcher.utter_message(text=(
                        "माफ़ करें! " + product_display +
                        " " + district_found.title() +
                        " में उपलब्ध नहीं है।\n\n"
                        "यहाँ उपलब्ध उत्पाद:\n\n" + product_list +
                        "\n\nकृपया ऊपर से एक उत्पाद चुनें।"
                    ))
                else:
                    say(dispatcher,
                        "Sorry! " + product_display +
                        " is not available in " + district_found.title() +
                        ".\n\nAvailable products:\n\n" + product_list, lang)
                return [
                    SlotSet("district", district_found),
                    SlotSet("product", None),
                    SlotSet("language", lang),
                ]

            if lang == "hi":
                header = (
                    district_found.title() + " में " +
                    product_display + " बेचने वाले विक्रेता:\n"
                )
                footer = (
                    "\nदूसरा उत्पाद खोजने के लिए उत्पाद का नाम टाइप करें।\n"
                    "जिला बदलने के लिए 'जिला बदलें' कहें।\n"
                    "बाहर निकलने के लिए 'अलविदा' कहें।"
                )
            else:
                header = (
                    "Retailers selling " + product_display +
                    " in " + district_found.title() + ":\n"
                )
                footer = (
                    "\nType another product to search again.\n"
                    "Or say change district to go back.\n"
                    "Or say goodbye to exit."
                )

            dispatcher.utter_message(text=header + table_html + footer)
            return [
                SlotSet("district", district_found),
                SlotSet("product", product_found),
                SlotSet("language", lang),
            ]

        except Exception as e:
            say(dispatcher, "Something went wrong: " + str(e), lang)
            return [SlotSet("language", lang)]


class ActionHandleFallback(Action):
    def name(self): return "action_handle_fallback"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict):
        user_message = tracker.latest_message.get("text", "")
        lang = get_lang(tracker, user_message)
        district = tracker.get_slot("district")

        if not district:
            say(dispatcher,
                "I did not understand that.\n\n"
                "Please type a valid district name.\n"
                "Available: Tirupati, Guntur, Eluru, Anakapalli, Kurnool", lang)
            return [SlotSet("language", lang)]

        if lang == "hi":
            dispatcher.utter_message(text=(
                "मुझे समझ नहीं आया।\n\n"
                "कृपया उत्पाद का नाम बताइए।\n\n"
                "उदाहरण:\n"
                "- यूरिया\n- डीएपी\n- अमोनियम सल्फेट\n"
                "- 15-15-15-9\n- 20-20-0-13\n\n"
                "या 'जिला बदलें' कहें।"
            ))
        else:
            say(dispatcher,
                "I did not understand that.\n\n"
                "Please type a valid product name.\n"
                "Try: Urea, DAP, Sulphate, 15-15-15-9, 20-20-0-13\n\n"
                "Or say change district to go back.", lang)
        return [SlotSet("language", lang)]