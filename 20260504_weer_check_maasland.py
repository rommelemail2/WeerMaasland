"""
Weer Check Maasland - Zondagavond 20:00
Checkt de temperatuur voor de komende 7 dagen en stuurt een WhatsApp bericht
als een van de dagen boven de 20 graden komt.

Vereisten:
  pip install requests

Gegevens worden ingelezen via omgevingsvariabelen (GitHub Secrets).
"""

import os
import requests
from datetime import datetime

# ─────────────────────────────────────────────────
#  Gegevens via GitHub Secrets (niet aanpassen)
# ─────────────────────────────────────────────────

WHATSAPP_ACCESS_TOKEN     = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID  = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
ONTVANGER_TELEFOONNUMMER  = os.environ.get("ONTVANGER_TELEFOONNUMMER", "")

# ─────────────────────────────────────────────────
#  Instellingen
# ─────────────────────────────────────────────────

DREMPELWAARDE_GRADEN = 20  # Stuur melding als een dag boven dit aantal graden komt

# Coördinaten van Maasland, Zuid-Holland
LATITUDE  = 51.9547
LONGITUDE = 4.2539

# ─────────────────────────────────────────────────

DAGEN_NL = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]


def haal_temperaturen_op():
    """Haal de maximumtemperaturen op voor de komende 7 dagen via Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": "temperature_2m_max",
        "timezone": "Europe/Amsterdam",
        "forecast_days": 7,
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    datums       = data["daily"]["time"]
    temperaturen = data["daily"]["temperature_2m_max"]

    resultaat = []
    for datum_str, temp in zip(datums, temperaturen):
        datum    = datetime.strptime(datum_str, "%Y-%m-%d")
        dag_naam = DAGEN_NL[datum.weekday()]
        resultaat.append({"dag": dag_naam, "datum": datum_str, "temp": temp})

    return resultaat


def bouw_bericht(dagen_data):
    """Bouw het WhatsApp bericht op."""
    regels = ["🌤️ *Weerbericht Maasland – komende 7 dagen*\n"]

    for dag in dagen_data:
        temp  = dag["temp"]
        emoji = "🔥" if temp > DREMPELWAARDE_GRADEN else "🌡️"
        regels.append(f"{emoji} {dag['dag']}: {temp:.1f}°C")

    regels.append(f"\n⚠️ Een of meer dagen komen boven de {DREMPELWAARDE_GRADEN}°C!")
    return "\n".join(regels)


def stuur_whatsapp_bericht(tekst):
    """Stuur een WhatsApp bericht via de Meta Business API."""
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": ONTVANGER_TELEFOONNUMMER,
        "type": "text",
        "text": {"body": tekst},
    }

    response = requests.post(url, headers=headers, json=payload, timeout=10)

    if response.status_code == 200:
        print("✅ WhatsApp bericht succesvol verstuurd.")
    else:
        print(f"❌ Fout bij versturen: {response.status_code} – {response.text}")


def controleer_secrets():
    """Controleer of alle benodigde secrets aanwezig zijn."""
    ontbrekend = []
    if not WHATSAPP_ACCESS_TOKEN:
        ontbrekend.append("WHATSAPP_ACCESS_TOKEN")
    if not WHATSAPP_PHONE_NUMBER_ID:
        ontbrekend.append("WHATSAPP_PHONE_NUMBER_ID")
    if not ONTVANGER_TELEFOONNUMMER:
        ontbrekend.append("ONTVANGER_TELEFOONNUMMER")

    if ontbrekend:
        print(f"❌ Ontbrekende secrets: {', '.join(ontbrekend)}")
        print("   Voeg deze toe via GitHub → Settings → Secrets and variables → Actions")
        return False
    return True


def main():
    print(f"🕗 Script gestart op {datetime.now().strftime('%A %d %B %Y %H:%M')}")

    if not controleer_secrets():
        return

    try:
        dagen = haal_temperaturen_op()
    except Exception as e:
        print(f"❌ Fout bij ophalen weerdata: {e}")
        return

    # Toon alle temperaturen in de log
    print("\n📋 Temperaturen komende 7 dagen:")
    for dag in dagen:
        print(f"   {dag['dag']}: {dag['temp']}°C")

    # Controleer of een dag boven de drempelwaarde komt
    warme_dagen = [d for d in dagen if d["temp"] > DREMPELWAARDE_GRADEN]

    if warme_dagen:
        print(f"\n🌡️ {len(warme_dagen)} dag(en) boven {DREMPELWAARDE_GRADEN}°C — bericht wordt verstuurd.")
        bericht = bouw_bericht(dagen)
        stuur_whatsapp_bericht(bericht)
    else:
        print(f"\n✅ Geen dagen boven {DREMPELWAARDE_GRADEN}°C. Geen bericht verstuurd.")


if __name__ == "__main__":
    main()
