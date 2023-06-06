# Module importieren
from flask import Flask, render_template
import pymysql
from flask import jsonify
from flask import flash, request, make_response
import traceback
from contextlib import closing
from datetime import date, datetime, timedelta
from flaskext.mysql import MySQL

# Einstellungen für Flask und PyMySQL
app = Flask(__name__)
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'admin'
app.config['MYSQL_DATABASE_PASSWORD'] = 'MyP@ssw0rd!'
app.config['MYSQL_DATABASE_DB'] = 'cde2'
app.config['MYSQL_DATABASE_HOST'] = 'example.com'
mysql.init_app(app)


# Methode, um neue Daten in die Datenbank zu schreiben
@app.route('/create', methods=['POST'])
def create_entry():
    try:
        # Alle Daten vom Raspberry auslesen
        args = request.args
        _experiment_id = args.get("experiment_id")
        _datetime_str = args.get("datetime")
        _datetime = datetime.strptime(_datetime_str, '%Y-%m-%d %H:%M:%S')   # Zeitstempel Format korrogieren
        _mc_temp = args.get("mc_temp")
        _mc_humidity = args.get("mc_humidity")
        _mc_window = args.get("mc_window")
        _pi_co2 = args.get("pi_co2")
        _pi_temp = args.get("pi_temp")
        _pi_humidity = args.get("pi_humidity")

        if _experiment_id and _datetime and _mc_temp and _mc_humidity and _mc_window and _pi_co2 and _pi_temp and _pi_humidity and request.method == 'POST':
            with closing(mysql.connect()) as conn:
                with closing(conn.cursor(pymysql.cursors.DictCursor)) as cursor:
                    # SQL Befehl für Datenbank
                    sqlQuery = """
                        INSERT INTO Messwert (einheit_id, sensor_id, experiment_id, wert, zeitstempel) 
                        VALUES 
                        (1, 1, %s, %s, %s),
                        (4, 1, %s, %s, %s),
                        (2, 1, %s, %s, %s),
                        (1, 2, %s, %s, %s),
                        (4, 2, %s, %s, %s),
                        (3, 2, %s, %s, %s)
                    """
                    # Parameter für SQL Befehl
                    query_params = (
                        _experiment_id, _pi_temp, _datetime_str,
                        _experiment_id, _pi_humidity, _datetime_str,
                        _experiment_id, _pi_co2, _datetime_str,
                        _experiment_id, _mc_temp, _datetime_str,
                        _experiment_id, _mc_humidity, _datetime_str,
                        _experiment_id, _mc_window, _datetime_str
                    )
                    # SQL Befehl wird ausgeführt
                    cursor.execute(sqlQuery, query_params)
                    conn.commit()

                    # Rückmeldung, ob Datentransfer erfolgreich war
                    respone = jsonify('Data added successfully!')
                    respone.status_code = 200
            return respone
        else:
            return showMessage()
        
    except Exception as e:
        print(e)
        traceback.print_exc()
        return make_response(jsonify(error=str(e)), 500)
    

# Methode, um neue Daten in die Datenbank zu schreiben
@app.route('/search', methods=['GET'])
def search():
    try:
        # Suchparameter einlesen
        search_params = request.args.to_dict()
        valid_fields = ['Messwert.experiment_id', 'Messwert.wert', 'Messwert.sensor_id', 'Messwert.einheit_id', 'Messwert.messwert_id', 'Sensor.controller_id']
        start_date_str = search_params.pop('start_date', None)
        end_date_str = search_params.pop('end_date', start_date_str)
        valid_search_params = {k: v for k, v in search_params.items() if k in valid_fields}

        query = "SELECT Messwert.*, Sensor.controller_id FROM Messwert JOIN Sensor ON Messwert.sensor_id = Sensor.sensor_id"
        conditions = []

        if start_date_str and end_date_str:
            conditions.append("Messwert.zeitstempel BETWEEN %s AND %s")

        if valid_search_params:
            conditions += [f"{field} = %s" for field in valid_search_params.keys()]
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        params = []

        if start_date_str and end_date_str:
            params += [start_date_str, end_date_str]
        params += list(valid_search_params.values())

        with closing(mysql.connect()) as conn:
            with closing(conn.cursor(pymysql.cursors.DictCursor)) as cursor:
                print(query)
                print(tuple(params))
                cursor.execute(query, tuple(params))
                result = cursor.fetchall()

                response = jsonify(result)
                response.status_code = 200

        return response

    except Exception as e:
        print(e)
        traceback.print_exc()
        return make_response(jsonify(error=str(e)), 500)


# Methode, um den neuesten Eintrag in der Datenbank zu suchen
@app.route('/latest', methods=['GET'])
def latest():
    try:
        with closing(mysql.connect()) as conn:
            with closing(conn.cursor(pymysql.cursors.DictCursor)) as cursor:
                query = """
                    SELECT experiment_id, zeitstempel, wert
                    FROM Messwert
                    ORDER BY zeitstempel DESC
                    LIMIT 1
                """
                cursor.execute(query)
                latestRow = cursor.fetchone()
                response = jsonify(latestRow)
                response.status_code = 200
        # Letzter Eintrag wird zurückgegeben
        return response
    except Exception as e:
        print(e)
        traceback.print_exc()
        return make_response(jsonify(error=str(e)), 500)


# Methode, um einen Datensatz zu ändern. Die passende messwert_id wird hierbei benötigt
@app.route('/update', methods=['PUT'])
def update_data():
    try:
        args = request.args
        _messwert_id = args.get("messwert_id")
        _einheit_id = args.get("einheit_id")
        _sensor_id = args.get("sensor_id")
        _experiment_id = args.get("experiment_id")
        _wert = args.get("wert")
        _zeitstempel = args.get("zeitstempel")

        if _messwert_id and request.method == 'PUT':
            with closing(mysql.connect()) as conn:
                with closing(conn.cursor(pymysql.cursors.DictCursor)) as cursor:
                    sqlQuery = "UPDATE Messwert SET "
                    query_params = []
                    if _einheit_id is not None:
                        sqlQuery += "einheit_id = %s, "
                        query_params.append(_einheit_id)
                    if _sensor_id is not None:
                        sqlQuery += "sensor_id = %s, "
                        query_params.append(_sensor_id)
                    if _experiment_id is not None:
                        sqlQuery += "experiment_id = %s, "
                        query_params.append(_experiment_id)
                    if _wert is not None:
                        sqlQuery += "wert = %s, "
                        query_params.append(_wert)
                    if _zeitstempel is not None:
                        sqlQuery += "zeitstempel = %s, "
                        query_params.append(_zeitstempel)
                    sqlQuery = sqlQuery[:-2] + " WHERE messwert_id = %s"
                    query_params.append(_messwert_id)

                    cursor.execute(sqlQuery, query_params)
                    conn.commit()
                    respone = jsonify('Data updated successfully!')
                    respone.status_code = 200
            return respone
        else:
            return showMessage()
        
    except Exception as e:
        print(e)
        traceback.print_exc()
        return make_response(jsonify(error=str(e)), 500)

# Methode, um einen Datensatz zu löschen. Die passende messwert_id wird hierbei benötigt
@app.route('/delete', methods=['DELETE'])
def delete_data():
    try:
        args = request.args
        _messwert_id = args.get("messwert_id")

        if _messwert_id and request.method == 'DELETE':
            with closing(mysql.connect()) as conn:
                with closing(conn.cursor(pymysql.cursors.DictCursor)) as cursor:
                    sqlQuery = "DELETE FROM Messwert WHERE messwert_id = %s"
                    cursor.execute(sqlQuery, (_messwert_id))
                    conn.commit()
                    response = jsonify('Data deleted successfully!')
                    response.status_code = 200
            return response
        else:
            return showMessage()
        
    except Exception as e:
        print(e)
        traceback.print_exc()
        return make_response(jsonify(error=str(e)), 500)

# Fehlerbehandlung
@app.errorhandler(404)
def showMessage(error=None):
    message = {
        'status': 404,
        'message': 'Record not found: ' + request.url,
        'error': str(error)
    }
    respone = jsonify(message)
    respone.status_code = 404
    return respone



if __name__ == '__main__':
	app.run()