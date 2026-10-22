"""
TTS Verification & Test Script
Verifies both English and Tamil speech synthesis engines.
"""

import time
from src.tts_engine import TTSEngine

def test():
    print("=" * 60)
    print("  TESTING BILINGUAL TTS ENGINE (TAMIL & ENGLISH)")
    print("=" * 60)

    tts = TTSEngine(rate=160, volume=1.0)

    print("\n1. Testing English speech synthesis...")
    tts.speak("Hello! The bilingual sign language assistive system is working properly.", lang="en")
    time.sleep(4.0)

    print("\n2. Testing Tamil speech synthesis...")
    tts.speak("வணக்கம்! தமிழ் மற்றும் ஆங்கில சைகை மொழி அமைப்பு வெற்றிகரமாக செயல்படுகிறது.", lang="ta")
    time.sleep(5.0)

    print("\n3. Testing short Tamil vocabulary phrases...")
    phrases = [
        ("வணக்கம்", "Hello"),
        ("நன்றி", "Thank you"),
        ("தண்ணீர்", "Water"),
        ("உதவி", "Help")
    ]
    for ta, en in phrases:
        print(f"   -> Speaking: {ta} ({en})")
        tts.speak(ta, lang="ta")
        time.sleep(2.0)

    print("\n[Complete] TTS verification complete!")
    tts.stop()

if __name__ == "__main__":
    test()
