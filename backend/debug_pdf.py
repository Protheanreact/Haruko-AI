import os
import sys
from pypdf import PdfReader

def analyze_pdf(filename):
    print(f"--- Analyse: {filename} ---")
    if not os.path.exists(filename):
        print("Datei nicht gefunden!")
        return

    try:
        reader = PdfReader(filename)
        print(f"Anzahl Seiten: {len(reader.pages)}")
        
        total_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                print(f"Seite {i+1}: {len(text)} Zeichen extrahiert.")
                total_text += text
                # Zeige die ersten 100 Zeichen der ersten Seite
                if i == 0:
                    print(f"Vorschau (Seite 1): {text[:100]}...")
            else:
                print(f"Seite {i+1}: KEIN Text extrahiert (Wahrscheinlich Bild/Scan).")
        
        if len(total_text.strip()) == 0:
            print("\nERGEBNIS: Diese PDF enthält KEINEN extrahierbaren Text.")
            print("Grund: Es handelt sich vermutlich um gescannte Bilder ohne OCR.")
            print("Lösung: PDF mit OCR-Software (z.B. Adobe Acrobat, Online OCR) in Text umwandeln.")
        else:
            print(f"\nERGEBNIS: PDF enthält Text ({len(total_text)} Zeichen gesamt).")
            print("Die Datei sollte von Haruko lesbar sein.")
            
    except Exception as e:
        print(f"Fehler beim Lesen der PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_pdf(sys.argv[1])
    else:
        # Default check for known problematic files
        kb_dir = os.path.join(os.path.dirname(__file__), "knowledge")
        target = os.path.join(kb_dir, "Knowledge Global.pdf")
        analyze_pdf(target)
