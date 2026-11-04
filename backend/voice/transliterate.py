"""
JARVIS Roman Urdu to Nastaliq / Urdu Script Phonetic Transliteration Engine
Converts Roman Urdu sentences (e.g. 'Ji Akmal bhai, main sun raha hoon') into
phonetically accurate Urdu script so Edge-TTS ('ur-PK-AsadNeural') sounds like
a 100% natural, broadcast-quality Pakistani human male presenter for FREE.
"""

import re
from typing import Dict, List

# High-frequency dictionary mapping for Roman Urdu to authentic Urdu Script
ROMAN_TO_URDU_WORDS: Dict[str, str] = {
    # Greetings & Honorifics
    "assalam": "السلام",
    "assalam-o-alaikum": "السلام علیکم",
    "assalamoalaikum": "السلام علیکم",
    "alaikum": "علیکم",
    "o": "",
    "akmal": "اَکمل",
    "bhai": "بھائی",
    "sir": "سر",
    "sahab": "صاحب",
    "shukriya": "شکریہ",
    "welcome": "خوش آمدید",
    "hukum": "حکم",

    # Pronouns & Prepositions
    "main": "میں",
    "mein": "میں",
    "aap": "آپ",
    "tum": "تم",
    "hum": "ہم",
    "mera": "میرا",
    "meri": "میری",
    "mere": "میرے",
    "apka": "آپ کا",
    "apki": "آپ کی",
    "apke": "آپ کے",
    "aapka": "آپ کا",
    "aapki": "آپ کی",
    "aapke": "آپ کے",
    "tumhara": "تمہارا",
    "yeh": "یہ",
    "ye": "یہ",
    "woh": "وہ",
    "wo": "وہ",
    "is": "اِس",
    "us": "اُس",
    "ka": "کا",
    "ki": "کی",
    "ke": "کے",
    "ko": "کو",
    "se": "سے",
    "par": "پر",
    "per": "پر",
    "pe": "پر",
    "tak": "تک",

    # Auxiliary Verbs
    "hai": "ہے",
    "hain": "ہیں",
    "hoon": "ہوں",
    "ho": "ہو",
    "tha": "تھا",
    "the": "تھے",
    "thi": "تھی",
    "hoga": "ہوگا",
    "hogi": "ہوگی",
    "hoge": "ہوگے",
    "honge": "ہوں گے",

    # Conversational Markers
    "ji": "جی",
    "jee": "جی",
    "haan": "ہاں",
    "nahi": "نہیں",
    "nahe": "نہیں",
    "theek": "ٹھیک",
    "thik": "ٹھیک",
    "acha": "اچھا",
    "achha": "اچھا",
    "bohot": "بہت",
    "bahut": "بہت",
    "bilkul": "بالکل",
    "zaroor": "ضرور",
    "kya": "کیا",
    "kaise": "کیسے",
    "kese": "کیسے",
    "kaisa": "کیسا",
    "kyun": "کیوں",
    "kahan": "کہاں",
    "kab": "کب",
    "kitna": "کتنا",
    "kitni": "کتنی",
    "kitne": "کتنے",

    # Action Verbs
    "kar": "کر",
    "karo": "کرو",
    "kardo": "کر دو",
    "karein": "کریں",
    "kijiye": "کیجیے",
    "karna": "کرنا",
    "kiya": "کیا",
    "krna": "کرنا",
    "kr": "کر",
    "kro": "کرو",
    "krdo": "کر دو",
    "kren": "کریں",
    "sun": "سن",
    "suno": "سنو",
    "sunayein": "سنائیں",
    "bolo": "بولو",
    "boliye": "بولیے",
    "batao": "بتاؤ",
    "btao": "بتاؤ",
    "bataiye": "بتائیے",
    "dekho": "دیکھو",
    "dekhein": "دیکھیں",
    "dikhao": "دکھاؤ",
    "chalao": "چلاؤ",
    "kholo": "کھولو",
    "khol": "کھول",
    "band": "بند",
    "rok": "روک",
    "roko": "روکو",
    "chahiye": "چاہیے",
    "chaiye": "چاہیے",
    "sakta": "سکتا",
    "sakti": "سکتی",
    "sakte": "سکتے",
    "diya": "دیا",
    "diye": "دیے",
    "gaya": "گیا",
    "gayi": "گئی",
    "gaye": "گئے",
    "raha": "رہا",
    "rahi": "رہی",
    "rahe": "رہے",

    # Tech & Common English loanwords in Urdu
    "jarvis": "جاروِس",
    "system": "سسٹم",
    "computer": "کمپیوٹر",
    "screen": "اسکرین",
    "code": "کوڈ",
    "files": "فائلز",
    "file": "فائل",
    "folder": "فولڈر",
    "project": "پروجیکٹ",
    "browser": "براؤزر",
    "chrome": "کروم",
    "youtube": "یوٹیوب",
    "google": "گوگل",
    "weather": "موسم",
    "temperature": "درجہ حرارت",
    "timer": "ٹائمر",
    "alarm": "الارم",
    "reminder": "ریمائنڈر",
    "open": "اوپن",
    "close": "کلوز",
    "search": "سرچ",
    "start": "شروع",
    "stop": "اسٹاپ",
    "online": "آن لائن",
    "offline": "آف لائن",
    "details": "تفصیلات",
    "report": "رپورٹ",
    "ready": "تیار",
    "active": "ایکٹیو",
    "tests": "ٹیسٹس",
    "status": "اسٹیٹس",
    "volume": "والیم",
    "percent": "فیصد",
    "percentage": "فیصد",
    "degrees": "ڈگری",
    "celsius": "سینٹی گریڈ",
}

# Multi-character digram transliteration mapping
PHONETIC_DIGRAPHS = [
    ("kh", "کھ"),
    ("gh", "غ"),
    ("sh", "ش"),
    ("ch", "چ"),
    ("th", "تھ"),
    ("bh", "بھ"),
    ("ph", "پھ"),
    ("dh", "دھ"),
    ("jh", "جھ"),
    ("ai", "ے"),
    ("ee", "ی"),
    ("oo", "و"),
    ("aa", "ا"),
]

PHONETIC_CHAR_MAP = {
    'a': 'ا', 'b': 'ب', 'p': 'پ', 't': 'ت', 'j': 'ج', 'c': 'ک',
    'd': 'د', 'r': 'ر', 'z': 'ز', 's': 'س', 'f': 'ف', 'q': 'ق',
    'k': 'ک', 'g': 'گ', 'l': 'ل', 'm': 'م', 'n': 'ن', 'w': 'و',
    'v': 'و', 'h': 'ہ', 'y': 'ی', 'e': 'ے', 'i': 'ی', 'o': 'و', 'u': 'و'
}


def _transliterate_word(word: str) -> str:
    """Transliterate a single Roman Urdu word into Urdu characters."""
    w_clean = word.lower().strip()
    if not w_clean:
        return ""

    # 1. Exact match in high-frequency dictionary
    if w_clean in ROMAN_TO_URDU_WORDS:
        return ROMAN_TO_URDU_WORDS[w_clean]

    # If it's pure numbers, keep digits
    if re.match(r'^\d+$', w_clean):
        return w_clean

    # 2. Digraph replacement
    res = w_clean
    for dig, rep in PHONETIC_DIGRAPHS:
        res = res.replace(dig, rep)

    # 3. Single character replacement for remaining Latin letters
    final_chars = []
    for ch in res:
        if ch in PHONETIC_CHAR_MAP:
            final_chars.append(PHONETIC_CHAR_MAP[ch])
        else:
            final_chars.append(ch)

    return "".join(final_chars)


def roman_to_urdu(text: str) -> str:
    """
    Convert a Roman Urdu sentence into proper Urdu script for natural TTS synthesis.
    Preserves punctuation marks and existing Urdu characters.
    """
    if not text:
        return ""

    # If text is already mostly Urdu script (>40% Urdu unicode), return as is
    urdu_chars = sum(1 for ch in text if '\u0600' <= ch <= '\u06FF')
    if len(text) > 0 and (urdu_chars / len(text)) > 0.4:
        return text

    # Tokenize words while preserving punctuation
    tokens = re.findall(r"[\w'-]+|[^\w\s]|\s+", text)
    result_tokens = []

    for tok in tokens:
        if tok.isspace() or re.match(r'^[^\w\s]+$', tok):
            result_tokens.append(tok)
        else:
            result_tokens.append(_transliterate_word(tok))

    return "".join(result_tokens).strip()


def prepare_speech_text(text: str, is_roman_urdu: bool = False) -> tuple[str, str]:
    """
    Prepare text and select the optimal human voice:
    Returns (processed_text, voice_id).
    
    - If Urdu / Roman Urdu -> Transliterates to Urdu script and uses 'ur-PK-AsadNeural' (Rich, human male presenter).
    - If English -> Cleans English text and uses 'en-US-ChristopherNeural' (Deep, warm, natural human male voice).
    """
    if not text or not text.strip():
        return "", "en-US-ChristopherNeural"

    # Check if text contains Roman Urdu or native Urdu
    is_urdu = is_roman_urdu
    if not is_urdu:
        from backend.voice.text_to_speech import is_urdu_text
        is_urdu = is_urdu_text(text)

    if is_urdu:
        transliterated = roman_to_urdu(text)
        # Ensure diacritics for Akmal
        transliterated = re.sub(r'\bاکمل\b', 'اَکمل', transliterated)
        return transliterated, "ur-PK-AsadNeural"
    else:
        return text, "en-US-ChristopherNeural"


URDU_TO_ROMAN_DICT: Dict[str, str] = {
    # Platforms & Tech
    "یوٹیوب": "youtube",
    "گوگل": "google",
    "کروم": "chrome",
    "بک مارک": "bookmark",
    "بک مارکس": "bookmarks",
    "بکمارک": "bookmark",
    "بکمارکس": "bookmarks",
    "ہسٹری": "history",
    "اکاؤنٹ": "account",
    "اکاؤنٹس": "accounts",
    "پروفائل": "profile",
    "پروفائلز": "profiles",
    "ویب سائٹ": "website",
    "ویب": "web",
    "واٹس ایپ": "whatsapp",
    "واٹسایپ": "whatsapp",
    "میسج": "message",
    "میسجز": "messages",
    "اسٹیٹس": "status",
    "سٹیٹس": "status",
    "کال": "call",
    "ورسل": "vercel",
    "ویرسل": "vercel",
    "گٹ ہب": "github",
    "ایل ایم ایس": "lms",
    "وی یو": "vu",

    # Actions
    "سرچ": "search",
    "پلے": "play",
    "اوپن": "open",
    "کھولو": "kholo",
    "کھول": "khol",
    "بند": "close",
    "چلاؤ": "chalao",
    "چلا": "chala",
    "لگاؤ": "lagao",
    "لگا": "laga",
    "سنو": "sunao",
    "سناؤ": "sunao",
    "دکھاؤ": "dikhao",
    "دیکھو": "dekho",
    "دیکھ": "dekh",
    "ڈھونڈو": "dhoondo",
    "چیک": "check",
    "انالائز": "analyze",
    "تجزیہ": "analyze",
    "ڈیلیٹ": "delete",
    "مٹاؤ": "mitao",
    "بھیجو": "bhejo",
    "بھیج": "bhej",
    "سیو": "save",
    "محفوظ": "save",

    # Common words & helpers
    "کرو": "karo",
    "کر": "kar",
    "دو": "do",
    "دیجیے": "dijiye",
    "کیجیے": "kijiye",
    "گانا": "song",
    "گانے": "songs",
    "نظم": "song",
    "نعت": "naat",
    "پر": "per",
    "پہ": "pe",
    "میں": "mein",
    "سے": "se",
    "کو": "ko",
    "کا": "ka",
    "کی": "ki",
    "کے": "ke",
    "اور": "aur",
    "یا": "ya",
    "یہ": "ye",
    "وہ": "wo",
    "میرا": "mera",
    "میری": "meri",
    "میرے": "mere",
    "آپ": "aap",
    "تم": "tum",
    "ہم": "hum",
    "کیا": "kya",
    "کتنے": "kitne",
    "کتنا": "kitna",
    "کتنی": "kitni",
    "کون": "kaun",
    "کونسا": "kaunsa",
    "کونسے": "kaunse",
    "کہاں": "kahan",
    "ہے": "hai",
    "ہیں": "hain",
    "تھا": "tha",
    "تھی": "thi",
    "تھے": "thay",
    "پہلا": "pehla",
    "دوسرا": "dosra",
    "تیسرا": "teesra",
    "چوتھا": "chautha",
    "یار": "yar",
    "بھائی": "bhai",
    "اکمل": "akmal",
    "رانا": "rana"
}


def normalize_urdu_to_roman(text: str) -> str:
    """Normalize Urdu script into Roman Urdu if incoming speech was transcribed in Arabic/Urdu script."""
    if not text:
        return ""
    urdu_chars = sum(1 for ch in text if '\u0600' <= ch <= '\u06FF')
    if urdu_chars == 0:
        return text

    res = text
    multi_words = sorted([k for k in URDU_TO_ROMAN_DICT if " " in k], key=len, reverse=True)
    for mw in multi_words:
        res = re.sub(r'\b' + re.escape(mw) + r'\b', URDU_TO_ROMAN_DICT[mw], res)

    tokens = res.split()
    converted = []
    for tok in tokens:
        clean_tok = re.sub(r'[^\w\s]', '', tok)
        if clean_tok in URDU_TO_ROMAN_DICT:
            converted.append(URDU_TO_ROMAN_DICT[clean_tok])
        else:
            converted.append(tok)

    return " ".join(converted)
