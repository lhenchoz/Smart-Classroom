# Module importieren
import time
import digitalio
import adafruit_dht
import board
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
import grove_ultrasonic_ranger

# Einstellungen für Übertragung an den Raspberry Pi
ble = BLERadio()
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)

# Grove Sensoren configurieren
dht = adafruit_dht.DHT11(board.D5)  # nRF52840, Grove D2 Anschluss
sonar = grove_ultrasonic_ranger.GroveUltrasonicRanger(sig_pin=board.D9) # nRF52840, Grove D4 Anscluss

# Diverse Variabeln definieren
response = False    # Auf Anfrage vom Raspberry Pi warten
w_status = False    # False bedeutet, dass das Fenster geschlossen ist



while True:
    ble.start_advertising(advertisement)

    while not ble.connected:    # Auf Verbindung warten
        print("Waiting to connect")
        time.sleep(1)
    print("Connected")

    while ble.connected:
        try:
            time.sleep(5)   # Verzögerung von 5 Sekunden zwischen Übertragungen von Daten
            temp = dht.temperature  # Temperatur vom Sensor auslesen
            humidity = dht.humidity # Luftfeuchtigkeit vom Sensor auslesen
            sonar_distance = sonar.distance 

            uart.write((str(temp) + "," + str(humidity) + "," + str(sonar_distance)).encode("utf-8"))   # Daten an Raspberry Pi senden
            print("send")

        except RuntimeError as e:
            continue