from flask import Flask, request, jsonify, json
from dotenv import dotenv_values
from wowicache.models import WowiCache, UseUnit, Person, Contractor, Communication, Address, Contract
from sqlalchemy import or_, and_
from datetime import datetime
from datetime import date
import sqlite3
import os
import sys
import logging
import graypy


def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    app.logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))


app = Flask(__name__)
settings = dotenv_values(os.path.join(app.root_path, ".env"))

log_method = settings.get("log_method", "file").lower()
log_level = settings.get("log_level", "info").lower()
log_levels = {'debug': 10, 'info': 20, 'warning': 30, 'error': 40, 'critical': 50}
app.logger.setLevel(log_levels.get(log_level, 20))
sys.excepthook = handle_unhandled_exception
if log_method == "file":
    logging.basicConfig(filename=os.path.join(app.root_path, "log", "swserver.log"))
elif log_method == "graylog":
    graylog_host = settings.get("graylog_host", "127.0.0.1")
    graylog_port = int(settings.get("graylog_port", 12201))
    handler = graypy.GELFUDPHandler(graylog_host, graylog_port)
    app.logger.addHandler(handler)

search_base = settings.get("search_base", "person").lower()
prefer_contract_address_str = settings.get("prefer_contract_address")
prefer_contract_address = False
if prefer_contract_address_str is not None and len(prefer_contract_address_str) > 0:
    if prefer_contract_address_str.lower() == "true":
        prefer_contract_address = True

prefer_use_unit_type = settings.get("prefer_use_unit_type")

app.logger.info("swserver started.")


def get_token(header):
    try:
        prefix = 'Bearer'
        bearer, _, token = header.partition(' ')
        if bearer != prefix:
            return None
        return token
    except AttributeError:
        return None


@app.route('/caller_info', methods=['GET'])
def caller_info():
    phone = request.args.get("phone")
    if phone is None or len(phone) == 0:
        app.logger.warning(f"phone arg missing. Client {request.remote_addr}, args {' '.join(request.args)}")
        return 'phone arg missing', 400

    clientname = request.args.get("client")
    if clientname is None or len(clientname) == 0:
        app.logger.warning(f"client arg missing. Client {request.remote_addr}, args {' '.join(request.args)}")
        return 'client arg missing', 400

    db_path = os.path.join(app.root_path, "data", "data.sqlite3")
    if not os.path.isfile(db_path):
        app.logger.critical("Database not found.")
        return 'Database error (not found)', 500

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    query = "SELECT enabled FROM clients WHERE hostname=?"
    cur.execute(query, (clientname,))

    clientrow = cur.fetchone()
    if not clientrow:
        query = "INSERT INTO clients(hostname) VALUES(?)"
        cur.execute(query, (clientname,))
        con.commit()
        clientrow = [1]

    con.close()

    if int(clientrow[0]) != 1:
        app.logger.info(f"Client {clientname} ({request.remote_addr}) is disabled.")
        return 'client_disabled', 200

    db = WowiCache(settings.get("db_connection_string"))

    phone = phone.replace(' 49', '0')
    app.logger.debug(f"Client {clientname} ({request.remote_addr}) submitted phone number {phone}")
    app.logger.debug(f"Search Base: {search_base}")

    comm_found: Communication
    comm_found = db.session.query(Communication).filter(and_(or_(Communication.communication_type_id == 1,
                                                                 Communication.communication_type_id == 3)),
                                                        Communication.content.like(f'%{phone}%')).first()
    if not comm_found:
        app.logger.debug("No entry found.")
        return 'caller_not_found', 404

    first_person: Person
    first_person = db.session.query(Person).get(comm_found.person_id)

    if first_person.is_natural_person:
        first_name = first_person.first_name
        last_name = first_person.last_name
    else:
        first_name = first_person.long_name2
        last_name = first_person.long_name1

    if first_person.addresses is not None:
        first_address: Address
        first_address = first_person.addresses[0]
        addr = {
            'street': first_address.street_complete,
            'postcode': first_address.postcode,
            'city': first_address.town
        }
    else:
        addr = None

    # Alle Verträge zur Person durchlaufen
    address_overwritten_by_contract = False
    contract_list = []
    cont: Contractor
    contractors_found = db.session.query(Contractor).filter(Contractor.person_id == first_person.internal_id).all()
    for cont in contractors_found:
        tcontract: Contract
        tcontract = cont.contract
        end_of_contract = tcontract.contract_end
        if end_of_contract is not None:
            if type(end_of_contract) == str:
                eoc = datetime.strptime(str(end_of_contract), "%Y-%m-%d")
            else:
                eoc = end_of_contract
            if date.today() > eoc:
                continue
        if prefer_contract_address:
            overwrite_address = True
            use_unit_obj: UseUnit
            use_unit_obj = cont.use_unit
            if use_unit_obj is not None:
                if address_overwritten_by_contract:
                    use_unit_type = use_unit_obj.use_unit_usage_type
                    if use_unit_type != prefer_use_unit_type:
                        overwrite_address = False

                if overwrite_address:
                    address_overwritten_by_contract = True
                    addr = {
                        'street': use_unit_obj.street_complete,
                        'postcode': use_unit_obj.postcode,
                        'city': use_unit_obj.town,
                        'position': use_unit_obj.description_of_position
                    }

        t_contract = {
            "Id": cont.contract_id,
            "IdNum": cont.contract.id_num
        }
        contract_list.append(t_contract)

    ret_dict = {
        "IdNum": first_person.id_num,
        "Id": first_person.internal_id,
        "FirstName": first_name,
        "LastName": last_name,
        "Address": addr,
        "Contracts": contract_list

    }
    app.logger.debug(f"Returned entry: {ret_dict}")
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
            cur.execute(query, (clid,))
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
            cur.execute(query, (clid,))
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
