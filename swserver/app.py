from flask import Flask, request, jsonify, json
from dotenv import dotenv_values
from wowipy.wowipy import WowiPy, Contractor, Person
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
settings = dotenv_values(os.path.join(app.root_path, ".env"))

# Wowiport-Daten einlesen
wowi_host = settings.get("wowi_host")
wowi_user = settings.get("wowi_user")
wowi_pass = settings.get("wowi_pass")
wowi_key = settings.get("wowi_key")

wowi = WowiPy(wowi_host, wowi_user, wowi_pass, wowi_key)
# catalogs = wowi.get_communication_catalogs()
cache_contractors = settings.get("cache_contractors")
cache_use_units = settings.get("cache_use_units")
cache_use_persons = settings.get("cache_persons")

search_base = settings.get("search_base", "person").lower()
prefer_contract_address_str = settings.get("prefer_contract_address")
prefer_contract_address = False
if prefer_contract_address_str is not None and len(prefer_contract_address_str) > 0:
    if prefer_contract_address_str.lower() == "true":
        prefer_contract_address = True

prefer_use_unit_type = settings.get("prefer_use_unit_type")

wowi.cache_from_disk(cache_type=wowi.CACHE_CONTRACTORS, file_name=cache_contractors)
wowi.cache_from_disk(cache_type=wowi.CACHE_USE_UNITS, file_name=cache_use_units)
wowi.cache_from_disk(cache_type=wowi.CACHE_PERSONS, file_name=cache_use_persons)


def get_token(header):
    try:
        prefix = 'Bearer'
        bearer, _, token = header.partition(' ')
        if bearer != prefix:
            return None
        return token
    except AttributeError:
        return None


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/caller_info', methods=['GET'])
def caller_info():
    # Rückgabe-JSON in etwa:
    # {
    #   "idNum": "012345",
    #   "id": 123,
    #   "firstName": "Vorname",
    #   "lastName": "Nachname",
    #   "address": {
    #       "street": "Bla",
    #   },
    #   "contracts": {
    #       (vertrag)
    #   },
    #   "last_call": "2022-12-13",
    #   "last_call_recipient": "Sachbearbeiter",
    #   "last_call_reason": "Grund des Anrufs" (falls Wowiport Ticket)
    phone = request.args.get("phone")
    if phone is None or len(phone) == 0:
        return 'phone arg missing', 400

    clientname = request.args.get("client")
    if clientname is None or len(clientname) == 0:
        return 'client arg missing', 400

    db_path = os.path.join(app.root_path, "data", "data.sqlite3")
    if not os.path.isfile(db_path):
        return 'Database error (not found)', 500

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    query = "SELECT enabled FROM clients WHERE hostname=?"
    cur.execute(query, (clientname, ))

    clientrow = cur.fetchone()
    if not clientrow:
        query = "INSERT INTO clients(hostname) VALUES(?)"
        cur.execute(query, (clientname, ))
        con.commit()
        clientrow = [1]

    con.close()

    if int(clientrow[0]) != 1:
        return 'client_disabled', 200

    # DIe Normalisierung der Telefonnummern wird bereits in der entsprechenden Methode
    # von WowiPy übernommen

    phone = phone.replace(' 49', '0')
    print(phone)
    first_person: Person
    if search_base == "contractor":
        caller_found = wowi.search_contractor(search_phone=phone, allow_duplicates=True)
        if len(caller_found) > 0:
            first_contractor: Contractor
            first_contractor = caller_found[0]
            first_person = first_contractor.person
        else:
            return 'caller_not_found', 404
    else:
        caller_found = wowi.search_person(search_phone=phone)
        if len(caller_found) > 0:
            first_person = caller_found[0]
        else:
            return 'caller_not_found', 404

    if first_person.is_natural_person:
        if first_person.natural_person is not None:
            first_name = first_person.natural_person.first_name
            last_name = first_person.natural_person.last_name
        else:
            first_name = None
            last_name = None
    else:
        if first_person.legal_person is not None:
            first_name = first_person.legal_person.long_name2
            last_name = first_person.legal_person.long_name1
        else:
            first_name = None
            last_name = None

    if first_person.addresses is not None:
        first_address = first_person.addresses[0]
        addr = {
            'street': first_address.street_complete,
            'postcode': first_address.zip_,
            'city': first_address.town
        }
    else:
        addr = None

    # Alle Verträge zur Person durchlaufen
    address_overwritten_by_contract = False
    contract_list = []
    cont: Contractor
    contractors_found = wowi.get_contractors(person_id=first_person.id_, use_cache=True)
    for cont in contractors_found:
        if cont.end_of_contract is not None:
            if type(cont.end_of_contract) == str:
                eoc = datetime.strptime(str(cont.end_of_contract), "%Y-%m-%d")
            else:
                eoc = cont.end_of_contract
            if datetime.today() > eoc:
                print(f"{eoc} liegt nach {datetime.today()}")
                continue
        if prefer_contract_address:
            overwrite_address = True
            use_unit_idnum = cont.use_unit.use_unit_number
            use_unit_obj = wowi.get_use_units(use_unit_idnum=use_unit_idnum)
            if use_unit_obj is not None and len(use_unit_obj) > 0:
                if address_overwritten_by_contract:
                    use_unit_type = use_unit_obj[0].current_use_unit_type.use_unit_usage_type.name
                    if use_unit_type != prefer_use_unit_type:
                        overwrite_address = False

                if overwrite_address:
                    address_overwritten_by_contract = True
                    addr = {
                        'street': use_unit_obj[0].estate_address.street_complete,
                        'postcode': use_unit_obj[0].estate_address.zip_,
                        'city': use_unit_obj[0].estate_address.town,
                        'position': use_unit_obj[0].description_of_position
                    }

        t_contract = {
            "Id": cont.license_agreement_id,
            "IdNum": cont.license_agreement
        }
        contract_list.append(t_contract)

    ret_dict = {
        "IdNum": first_person.id_num,
        "Id": first_person.id_,
        "FirstName": first_name,
        "LastName": last_name,
        "Address": addr,
        "Contracts": contract_list

    }

    return jsonify(ret_dict)


@app.route('/clients/<client_id>', methods=['GET', 'POST'])
@app.route('/clients', methods=['GET', 'POST'])
def clients(client_id: str = None):
    clid = 0
    if client_id is not None:
        try:
            clid = int(client_id)
        except ValueError:
            return 'Invalid client id', 400

    db_path = os.path.join(app.root_path, "data", "data.sqlite3")
    if not os.path.isfile(db_path):
        return 'Database error (not found)', 500

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    if request.method.upper() == 'GET':
        if clid > 0:
            query = "SELECT * FROM clients WHERE id=? ORDER BY id"
            cur.execute(query, (clid, ))
        else:
            query = "SELECT * FROM clients ORDER BY id"
            cur.execute(query)

        ret_arr = []
        rows = cur.fetchall()

        for row in rows:
            if int(row[3]) == 1:
                t_active = True
            else:
                t_active = False

            t_dict = {
                'id': row[0],
                'hostname': row[1],
                'ip': row[2],
                'active': t_active,
                'date_crated': row[4],
                'date_updated': row[5]
            }
            ret_arr.append(t_dict)
        con.close()
        return jsonify(ret_arr)

    if request.method.upper() == 'POST':
        rjson = json.loads(request.data)
        if clid > 0:
            pass
            # Client update
            query = "SELECT 1 FROM clients WHERE id=?"
            cur.execute(query, (clid, ))
            if not cur.fetchone():
                return 'client_id_not_found', 404

            query = "UPDATE clients SET "
            value_added = False
            active_bool = rjson.get("active")
            if active_bool is not None:
                if active_bool:
                    active_int = 1
                else:
                    active_int = 0

                query = f"{query}enabled={active_int}, "
                value_added = True

            hostname = rjson.get("hostname")
            if hostname is not None:
                query = f"{query}hostname='{hostname}', "
                value_added = True
            ip = rjson.get("ip")
            if ip is not None:
                query = f"{query}ip='{ip}', "
                value_added = True

            if not value_added:
                return 'no_change_value', 400

            query = f"{query} date_updated=CURRENT_TIMESTAMP WHERE id={clid}"
            try:
                cur.execute(query)
                con.commit()
            except sqlite3.Error as e:
                con.close()
                return 'sql error: %s' % (' '.join(e.args)), 500

            con.close()
            return {'id': clid}, 202

        else:
            # Neuer Client
            if "hostname" not in rjson.keys():
                return "missing hostname", 400

            active_bool = rjson.get("active")
            if active_bool is None:
                active_bool = True

            if active_bool:
                active_int = 1
            else:
                active_int = 0

            query = "INSERT INTO clients(hostname, ip, enabled) VALUES(?, ?, ?)"
            try:
                cur.execute(query, (rjson.get("hostname"), rjson.get("ip"), active_int))
                con.commit()
            except sqlite3.Error as e:
                con.close()
                return 'sql error: %s' % (' '.join(e.args)), 500

            con.close()
            return {'id': cur.lastrowid}, 201


@app.before_request
def before_request():
    client_endpoints = [
        'caller_info'
    ]

    admin_endpoints = [
        'clients'
    ]

    current_endpoint = request.endpoint
    r_key = get_token(request.headers.get('Authorization'))

    if current_endpoint in client_endpoints:
        if settings['client_key'] != r_key and settings['admin_key'] != r_key:
            return "Unauthorized.", 401
    elif current_endpoint in admin_endpoints:
        if settings['admin_key'] != r_key:
            return "Unauthorized.", 401


if __name__ == '__main__':
    app.run()
