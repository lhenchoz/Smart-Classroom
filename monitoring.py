# Module importieren
import requests
import time
from datetime import datetime
import smtplib
from email.message import EmailMessage

reset_value = 0

# Nachricht erstellen
msg = EmailMessage()
msg['Subject'] = '!!! AUSFALL DER DATENERHEBUNG !!!'
msg['From'] = 'SYSTEMINFO CDE2'
msg['To'] = 'example@domain.com'
msg['Importance'] = 'high'
msg.set_content('Bei der Datenerhebung hat sich ein Fehler ereignet. Bitte umgehend das Setup prüfen.')

while True:
    try:
        # Letzte Messung abrufen
        post_url = 'http://192.168.0.1:80/latest'
        response = requests.get(post_url)
        latest_datetime = datetime.strptime(response.json()['zeitstempel'], '%a, %d %b %Y %H:%M:%S %Z')

        # Aktuelles Datum und Uhrzeit abrufen und Differenz berechnen
        current_datetime = datetime.now()
        delta = current_datetime - latest_datetime

        # Überprüfen, ob die Differenz größer als 60 Sekunden ist
        if delta.total_seconds() > 60:
            if reset_value == 0:
                
                # Eine Verbindung zum SMTP-Server herstellen und anmelden
                with smtplib.SMTP_SSL('example.com', 465) as smtp:
                    smtp.login('example@domain.com', 'MyP@ssw0rd!')

                    # E-Mail-Nachricht senden
                    smtp.send_message(msg)

                # 15 Minuten lang bis zur nächsten Überprüfung warten
                reset_value = 15
            else:
                # Reset-Wert um 1 verringern
                reset_value -= 1
        else:
            # Reset-Wert zurücksetzen
            reset_value = 0

        # Eine Minute lang warten
        time.sleep(60)

    except IOError:
        pass