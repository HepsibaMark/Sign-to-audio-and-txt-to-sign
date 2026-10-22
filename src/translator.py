"""
Bilingual Translator Module (Tamil <-> English)
Provides high-accuracy translation, phrase mapping, phonetic guides,
and reverse token resolution for Sign Language communication.
"""

import re
from typing import Dict, List, Optional, Tuple


class BilingualTranslator:
    """Handles English-Tamil translations for gestures, sentences, and vocabulary."""

    # Core Sign Vocabulary Dictionary: English -> Tamil (Script, Transliteration, Meaning)
    SIGN_VOCABULARY: Dict[str, Dict[str, str]] = {
        'HELLO': {
            'tamil': 'வணக்கம்',
            'transliteration': 'Vanakkam',
            'category': 'Greeting',
            'description': 'Universal Tamil greeting'
        },
        'THANK YOU': {
            'tamil': 'நன்றி',
            'transliteration': 'Nandri',
            'category': 'Politeness',
            'description': 'Expression of gratitude'
        },
        'YES': {
            'tamil': 'ஆம்',
            'transliteration': 'Aam',
            'category': 'Confirmation',
            'description': 'Affirmative response'
        },
        'NO': {
            'tamil': 'இல்லை',
            'transliteration': 'Illai',
            'category': 'Negation',
            'description': 'Negative response'
        },
        'HELP': {
            'tamil': 'உதவி',
            'transliteration': 'Uthavi',
            'category': 'Emergency',
            'description': 'Request for assistance'
        },
        'WATER': {
            'tamil': 'தண்ணீர்',
            'transliteration': 'Thanneer',
            'category': 'Survival Need',
            'description': 'Drinking water requirement'
        },
        'I LOVE YOU': {
            'tamil': 'நான் உன்னை நேசிக்கிறேன்',
            'transliteration': 'Naan unnai nesikkiren',
            'category': 'Expression',
            'description': 'Universal affection'
        },
        'OK': {
            'tamil': 'சரி',
            'transliteration': 'Sari',
            'category': 'Acknowledgment',
            'description': 'Agreement or confirmation'
        },
        'PEACE': {
            'tamil': 'அமைதி',
            'transliteration': 'Amaidhi',
            'category': 'Expression',
            'description': 'Peace / Victory'
        },
        'PLEASE': {
            'tamil': 'தயவுசெய்து',
            'transliteration': 'Thayavuseithu',
            'category': 'Courtesy',
            'description': 'Polite request'
        },
        'GOOD': {
            'tamil': 'நல்லது',
            'transliteration': 'Nallathu',
            'category': 'Expression',
            'description': 'Approval / Positive state'
        },
        'BAD': {
            'tamil': 'கெட்டது',
            'transliteration': 'Kettathu',
            'category': 'Expression',
            'description': 'Disapproval / Unfavorable'
        },
        'CALL': {
            'tamil': 'அழைக்கவும்',
            'transliteration': 'Alaikkavum',
            'category': 'Action',
            'description': 'Phone call / Contact'
        },
        'FOOD': {
            'tamil': 'உணவு',
            'transliteration': 'Unavu',
            'category': 'Survival Need',
            'description': 'Food / Meal'
        },
        'HOSPITAL': {
            'tamil': 'மருத்துவமனை',
            'transliteration': 'Maruthuvamanai',
            'category': 'Emergency',
            'description': 'Medical center'
        },
        'DOCTOR': {
            'tamil': 'மருத்துவர்',
            'transliteration': 'Maruthuvar',
            'category': 'Emergency',
            'description': 'Medical physician'
        },
        'PAIN': {
            'tamil': 'வலி',
            'transliteration': 'Vali',
            'category': 'Emergency',
            'description': 'Physical pain'
        },
        'STOP': {
            'tamil': 'நிறுத்து',
            'transliteration': 'Niruthu',
            'category': 'Command',
            'description': 'Halt / Stop'
        },
        'FRIEND': {
            'tamil': 'நண்பன்',
            'transliteration': 'Nanban',
            'category': 'Relationship',
            'description': 'Friend / Companion'
        },
        'FAMILY': {
            'tamil': 'குடும்பம்',
            'transliteration': 'Kudumbam',
            'category': 'Relationship',
            'description': 'Family unit'
        }
    }

    # ASL Letters A-Z in Tamil Phonetics
    ALPHABET_TAMIL: Dict[str, Dict[str, str]] = {
        'A': {'tamil': 'ஏ', 'transliteration': 'Ae'},
        'B': {'tamil': 'பி', 'transliteration': 'Bee'},
        'C': {'tamil': 'சி', 'transliteration': 'See'},
        'D': {'tamil': 'டி', 'transliteration': 'Dee'},
        'E': {'tamil': 'ஈ', 'transliteration': 'Ee'},
        'F': {'tamil': 'எஃப்', 'transliteration': 'Eff'},
        'G': {'tamil': 'ஜி', 'transliteration': 'Jee'},
        'H': {'tamil': 'ஹெச்', 'transliteration': 'Eitch'},
        'I': {'tamil': 'ஐ', 'transliteration': 'Ai'},
        'J': {'tamil': 'ஜே', 'transliteration': 'Jay'},
        'K': {'tamil': 'கே', 'transliteration': 'Kay'},
        'L': {'tamil': 'எல்', 'transliteration': 'Ell'},
        'M': {'tamil': 'எம்', 'transliteration': 'Emm'},
        'N': {'tamil': 'என்', 'transliteration': 'Enn'},
        'O': {'tamil': 'ஓ', 'transliteration': 'Oh'},
        'P': {'tamil': 'பி', 'transliteration': 'Pee'},
        'Q': {'tamil': 'கியூ', 'transliteration': 'Kyoo'},
        'R': {'tamil': 'ஆர்', 'transliteration': 'Aar'},
        'S': {'tamil': 'எஸ்', 'transliteration': 'Ess'},
        'T': {'tamil': 'டி', 'transliteration': 'Tee'},
        'U': {'tamil': 'யூ', 'transliteration': 'Yoo'},
        'V': {'tamil': 'வி', 'transliteration': 'Vee'},
        'W': {'tamil': 'டபிள்யூ', 'transliteration': 'Double-Yoo'},
        'X': {'tamil': 'எக்ஸ்', 'transliteration': 'Exx'},
        'Y': {'tamil': 'ஒய்', 'transliteration': 'Wye'},
        'Z': {'tamil': 'இஸட்', 'transliteration': 'Izzat'}
    }

    # Common English words/phrases translated into Tamil
    COMMON_WORDS: Dict[str, str] = {
        'I': 'நான்',
        'YOU': 'நீங்கள்',
        'HE': 'அவன்',
        'SHE': 'அவள்',
        'WE': 'நாங்கள்',
        'THEY': 'அவர்கள்',
        'ME': 'என்னை',
        'MY': 'என்',
        'YOUR': 'உங்கள்',
        'NEED': 'வேண்டும்',
        'WANT': 'வேண்டும்',
        'NAME': 'பெயர்',
        'WHAT': 'என்ன',
        'WHERE': 'எங்கே',
        'HOW': 'எப்படி',
        'WHEN': 'எப்போது',
        'WHY': 'ஏன்',
        'WHO': 'யார்',
        'IS': 'இருக்கிறது',
        'ARE': 'இருக்கிறார்கள்',
        'AM': 'இருக்கிறேன்',
        'GOOD MORNING': 'காலை வணக்கம்',
        'GOOD NIGHT': 'இனிய இரவு',
        'HOW ARE YOU': 'நீங்கள் எப்படி இருக்கிறீர்கள்',
        'FINE': 'நன்றாக',
        'WELCOME': 'நல்வரவு',
        'SORRY': 'மன்னிக்கவும்'
    }

    # Reverse lookup map: Tamil word -> English sign token
    TAMIL_TO_SIGN: Dict[str, str] = {
        'வணக்கம்': 'HELLO',
        'ஹலோ': 'HELLO',
        'ஹாய்': 'HELLO',
        'நன்றி': 'THANK YOU',
        'தேங்க்ஸ்': 'THANK YOU',
        'ஆம்': 'YES',
        'ஆமாம்': 'YES',
        'சரி': 'OK',
        'ஓகே': 'OK',
        'இல்லை': 'NO',
        'வேண்டாம்': 'NO',
        'உதவி': 'HELP',
        'ஹெல்ப்': 'HELP',
        'தண்ணீர்': 'WATER',
        'தண்ணி': 'WATER',
        'நீர்': 'WATER',
        'நான் உன்னை காதலிக்கிறேன்': 'I LOVE YOU',
        'நான் உன்னை நேசிக்கிறேன்': 'I LOVE YOU',
        'லவ் யூ': 'I LOVE YOU',
        'அமைதி': 'PEACE',
        'தயவுசெய்து': 'PLEASE',
        'ப்ளீஸ்': 'PLEASE',
        'நல்லது': 'GOOD',
        'நல்ல': 'GOOD',
        'கெட்டது': 'BAD',
        'தவறு': 'BAD',
        'அழைப்பு': 'CALL',
        'போன்': 'CALL',
        'அழைக்கவும்': 'CALL',
        'மருத்துவமனை': 'HOSPITAL',
        'மருத்துவர்': 'DOCTOR',
        'வலி': 'PAIN',
        'நிறுத்து': 'STOP',
        'நண்பன்': 'FRIEND',
        'குடும்பம்': 'FAMILY',
        'உணவு': 'FOOD'
    }

    @staticmethod
    def is_tamil_script(text: str) -> bool:
        """Checks if text contains Unicode Tamil characters (U+0B80 - U+0BFF)."""
        return bool(re.search(r'[\u0b80-\u0bff]', text))

    @classmethod
    def get_sign_tamil(cls, sign_name: str) -> Tuple[str, str]:
        """
        Returns (tamil_text, transliteration) for a gesture token.
        Handles composite labels like 'HELP / GOOD', 'PEACE (V)', etc.
        """
        clean = sign_name.strip().upper()

        # Direct vocabulary hit
        if clean in cls.SIGN_VOCABULARY:
            info = cls.SIGN_VOCABULARY[clean]
            return info['tamil'], info['transliteration']

        # Composite label parsing: e.g. "HELP / GOOD"
        if " / " in clean:
            parts = clean.split(" / ")
            tamil_parts = []
            trans_parts = []
            for p in parts:
                p_clean = p.split(" ")[0].strip()
                if p_clean in cls.SIGN_VOCABULARY:
                    info = cls.SIGN_VOCABULARY[p_clean]
                    tamil_parts.append(info['tamil'])
                    trans_parts.append(info['transliteration'])
                elif p_clean in cls.ALPHABET_TAMIL:
                    info = cls.ALPHABET_TAMIL[p_clean]
                    tamil_parts.append(info['tamil'])
                    trans_parts.append(info['transliteration'])
            if tamil_parts:
                return " / ".join(tamil_parts), " / ".join(trans_parts)

        # Parenthetical format: e.g. "PEACE (V)" -> "PEACE"
        base_match = re.match(r"^([A-Z\s]+)\s*\([A-Z]\)$", clean)
        if base_match:
            base_word = base_match.group(1).strip()
            if base_word in cls.SIGN_VOCABULARY:
                info = cls.SIGN_VOCABULARY[base_word]
                return info['tamil'], info['transliteration']

        # Single ASL Letter
        if clean in cls.ALPHABET_TAMIL:
            info = cls.ALPHABET_TAMIL[clean]
            return f"எழுத்து {info['tamil']}", info['transliteration']

        # Fallback
        return clean, clean

    @classmethod
    def translate_sentence_to_tamil(cls, sentence: str) -> str:
        """
        Translates an English sentence (or sequence of gesture words) into natural Tamil.
        Example: "HELLO I NEED WATER PLEASE" -> "வணக்கம் எனக்கு தண்ணீர் வேண்டும் தயவுசெய்து"
        """
        if not sentence or not sentence.strip():
            return ""

        clean = sentence.strip().upper()

        # Check full sentence in common dictionary
        if clean in cls.COMMON_WORDS:
            return cls.COMMON_WORDS[clean]

        words = clean.split()
        translated_words = []

        i = 0
        while i < len(words):
            # Check 3-word phrase: e.g. "I LOVE YOU"
            if i + 2 < len(words):
                three_word = f"{words[i]} {words[i+1]} {words[i+2]}"
                if three_word in cls.SIGN_VOCABULARY:
                    translated_words.append(cls.SIGN_VOCABULARY[three_word]['tamil'])
                    i += 3
                    continue

            # Check 2-word phrase: e.g. "THANK YOU", "GOOD MORNING"
            if i + 1 < len(words):
                two_word = f"{words[i]} {words[i+1]}"
                if two_word in cls.SIGN_VOCABULARY:
                    translated_words.append(cls.SIGN_VOCABULARY[two_word]['tamil'])
                    i += 2
                    continue
                if two_word in cls.COMMON_WORDS:
                    translated_words.append(cls.COMMON_WORDS[two_word])
                    i += 2
                    continue

            # Single word lookup
            w = words[i]
            # Strip punctuation
            w_bare = re.sub(r'[^\w]', '', w)

            if w_bare in cls.SIGN_VOCABULARY:
                translated_words.append(cls.SIGN_VOCABULARY[w_bare]['tamil'])
            elif w_bare in cls.COMMON_WORDS:
                translated_words.append(cls.COMMON_WORDS[w_bare])
            elif w_bare in cls.ALPHABET_TAMIL:
                translated_words.append(cls.ALPHABET_TAMIL[w_bare]['tamil'])
            else:
                translated_words.append(w)

            i += 1

        return " ".join(translated_words)

    @classmethod
    def resolve_tamil_to_sign_tokens(cls, tamil_text: str) -> List[str]:
        """
        Parses Tamil input and returns matching English Sign Language tokens.
        Example: "வணக்கம் தண்ணீர் நன்றி" -> ["HELLO", "WATER", "THANK YOU"]
        """
        if not tamil_text or not tamil_text.strip():
            return []

        tokens: List[str] = []
        words = tamil_text.strip().split()

        i = 0
        while i < len(words):
            # Check 2-word Tamil phrase (e.g., "நான் உன்னை")
            if i + 2 < len(words):
                three = f"{words[i]} {words[i+1]} {words[i+2]}"
                if three in cls.TAMIL_TO_SIGN:
                    tokens.append(cls.TAMIL_TO_SIGN[three])
                    i += 3
                    continue

            if i + 1 < len(words):
                two = f"{words[i]} {words[i+1]}"
                if two in cls.TAMIL_TO_SIGN:
                    tokens.append(cls.TAMIL_TO_SIGN[two])
                    i += 2
                    continue

            w = words[i]
            # Remove punctuation
            w_clean = re.sub(r'[^\w\u0b80-\u0bff]', '', w)

            if w_clean in cls.TAMIL_TO_SIGN:
                tokens.append(cls.TAMIL_TO_SIGN[w_clean])
            else:
                # Transliterate or fingerspell phonetically
                # For words not in dictionary, we can represent with HELLO or fallback
                # or fingerspell Romanized letters
                translit = cls.transliterate_tamil_to_latin(w_clean)
                for ch in translit.upper():
                    if ch.isalpha():
                        tokens.append(ch)
            i += 1

        return tokens

    @staticmethod
    def transliterate_tamil_to_latin(text: str) -> str:
        """
        Lightweight phonetic transliteration of Tamil script into Roman characters
        so arbitrary names or unknown words can be fingerspelled in sign language.
        """
        charmap = {
            'அ': 'a', 'ஆ': 'aa', 'இ': 'i', 'ஈ': 'ee', 'உ': 'u', 'ஊ': 'oo',
            'எ': 'e', 'ஏ': 'ae', 'ஐ': 'ai', 'ஒ': 'o', 'ஓ': 'oa', 'ஔ': 'au',
            'க': 'k', 'ங': 'ng', 'ச': 's', 'ஞ': 'nj', 'ட': 't', 'ண': 'n',
            'த': 'th', 'ந': 'n', 'ப': 'p', 'ம': 'm', 'ய': 'y', 'ர': 'r',
            'ல': 'l', 'வ': 'v', 'ழ': 'zh', 'ள': 'l', 'ற': 'r', 'ன': 'n',
            'ஜ': 'j', 'ஷ': 'sh', 'ஸ': 's', 'ஹ': 'h', 'க்ஷ': 'ksh',
            '்': '', 'ா': 'aa', 'ி': 'i', 'ீ': 'ee', 'ு': 'u', 'ூ': 'oo',
            'ெ': 'e', 'ே': 'ae', 'ை': 'ai', 'ொ': 'o', 'ோ': 'oa', 'ௌ': 'au'
        }
        res = []
        for ch in text:
            res.append(charmap.get(ch, ch))
        return "".join(res)
