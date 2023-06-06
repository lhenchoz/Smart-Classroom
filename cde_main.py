# Module importieren
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from scd30_i2c import SCD30
from datetime import datetime
import requests
import logging

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename="log.txt")

# Übertragung vorbereiten
try:
    ble = BLERadio()
    scd30 = SCD30()
except Exception as e:
    logging.error("Error while preparing transmission: " + str(e))
else:
    logging.info("Transmission prepared")

uart_connection = None

while True:
    logging.info("________Main loop iteration________")

    # Bluetoothverbindung mit dem Miktocontroller starten
    if not uart_connection:
        logging.info("Trying to connect...")
        for adv in ble.start_scan(ProvideServicesAdvertisement):
            if UARTService in adv.services:
                try:
                    uart_connection = ble.connect(adv)
                except Exception as e:
                    logging.error("Error while connecting: " + str(e))
                else:
                    logging.info("Connected")
                    break

        ble.stop_scan()

    # Weiterverfahren, falls die Verbindung geklappt hat
    if uart_connection and uart_connection.connected:
        uart_service = uart_connection[UARTService]

        while uart_connection.connected:
            # Daten vom Mikrocontroller empfangen
            response = uart_service.readline().decode("utf-8")

            if response:
                logging.info("Received response: " + response)

                # Daten vom SCD30-Sensoren lesen
                if scd30.get_data_ready():
                    try:
                        measurement = scd30.read_measurement()
                    except Exception as e:
                        logging.error("Error while reading measurement: " + str(e))
                    else:
                        logging.info("Received measurement: " + str(measurement))

                    if measurement:
                        response_split = response.split(",")
                        exp_id = 1                      		                    # Experiment-ID
                        mc_temp = response_split[0] 		                        # Temperatur vom Mikrocontroller
                        mc_humidity = int(response_split[1]) - 3	                # Luftfeuchtigkeit vom Mikrocontroller, korrigiert um -3 Prozent
                        mc_window = response_split[2]   		                    # Entfernung am UV-Sensor vom Mikrocontroller
                        pi_co2 = measurement[0]         		                    # CO2 vom Raspberry Pi
                        pi_temp = int(measurement[1]) - 3  		                    # Temperatur vom Raspberry Pi, korrigiert um -3 Grad
                        pi_humidity = int(measurement[2]) - 5   	                # Luftfeuchtigkeit vom Raspberry Pi, korrigiert um -5 Prozent
                        datetime_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Aktuelles Datum und Uhrzeit

                        # Daten an die API senden
                        try:
                            post_url = ('http://192.168.0.1:80/create' + "?experiment_id=" + str(exp_id) + "&datetime=" + str(datetime_now) + "&mc_temp=" + str(mc_temp) + "&mc_humidity=" + str(mc_humidity) + "&mc_window=" + str(mc_window) + "&pi_co2=" + str(pi_co2) + "&pi_temp=" + str(pi_temp) + "&pi_humidity=" + str(pi_humidity))
                            requests.post(post_url)
                        except Exception as e:
                            logging.error("Error while posting url: " + str(e))
                        else:
                            logging.info("Data sent to database")


        # Neuverbindung nach Verbindungsabbruch
        logging.info("Connection lost")
        uart_connection = None
