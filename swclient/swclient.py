import sys
import platform
import webbrowser
import requests
import winreg
import customtkinter
from tkinter import CENTER
from datetime import datetime

# ---------------------------
# Config
# ---------------------------

KEY_PATH = r"Software\SwyxWowiport"
REQUIRED_STRINGS = ("wowi_url", "api_key", "host")
NUMERIC_KEYS = ("app_width", "app_height", "sub_xpos", "sub_ypos")

DEFAULTS = {
    "app_width": 300,
    "app_height": 400,
    "sub_xpos": 10,
    "sub_ypos": 80,
}

HTTP_TIMEOUT = 5  # seconds


# ---------------------------
# Helper Functions
# ---------------------------

def open_url(ourl: str) -> None:
    webbrowser.open(ourl, new=0, autoraise=True)


def read_registry_values() -> dict:
    values = DEFAULTS.copy()

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, KEY_PATH, 0, winreg.KEY_READ) as key:
            for name in REQUIRED_STRINGS:
                try:
                    val, rtype = winreg.QueryValueEx(key, name)
                    # noinspection PyTypeChecker
                    values[name] = str(val)
                except FileNotFoundError:
                    print(f"Missing registry value: {name}")
                    sys.exit(1)

            for name in NUMERIC_KEYS:
                try:
                    val, rtype = winreg.QueryValueEx(key, name)
                    if rtype == winreg.REG_DWORD:
                        values[name] = int(val)
                    else:
                        values[name] = int(str(val))
                except (FileNotFoundError, ValueError, TypeError):
                    # Fallback to defaults
                    pass
    except FileNotFoundError:
        print(f"Registry-Key {KEY_PATH} not found.")
        sys.exit(1)

    return values


def fetch_caller_info(phost: str, papi_key: str, phone: str, client: str) -> dict | None:
    url = f"{phost.rstrip('/')}/caller_info"
    headers = {"Authorization": f"Bearer {papi_key}"}
    params = {"phone": phone, "client": client}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=HTTP_TIMEOUT)
    except requests.RequestException as ex:
        print(f"http error: {ex}")
        return None

    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        print(f"unexpected http status: {resp.status_code}")
        return None

    if "client_disabled" in resp.text:
        return None

    try:
        return resp.json()
    except ValueError:
        print("Invalid json")
        return None


def normalize_caller(arg: str) -> str:
    if arg.startswith("00"):
        return arg[1:]
    return arg


def make_label(master, text, font, pady=0):
    lbl = customtkinter.CTkLabel(master=master, text=text, font=font, anchor=CENTER)
    lbl.pack(pady=pady)
    return lbl


def make_button(master, text, url):
    btn = customtkinter.CTkButton(master=master, text=text,
                                  command=lambda: open_url(url))
    btn.pack()
    return btn


# ---------------------------
# Main application run
# ---------------------------

if len(sys.argv) <= 1:
    print("missing caller argument")
    sys.exit(0)

# Show popup only if the caller is an external number. Ignore if number too short
caller_raw = sys.argv[1]
if len(caller_raw) < 3:
    sys.exit(0)

caller = normalize_caller(caller_raw)
client_name = platform.node()

vals = read_registry_values()
app_width = vals["app_width"]
app_height = vals["app_height"]
sub_xpos = vals["sub_xpos"]
sub_ypos = vals["sub_ypos"]
wowi_url = vals["wowi_url"].rstrip("/")
api_key = vals["api_key"]
host = vals["host"].rstrip("/")

# backend call
rjson = fetch_caller_info(host, api_key, caller, client_name)

# Prepare view info
caller_name = "Unbekannt"
address_street = ""
address_city = ""

if rjson:
    last = rjson.get("LastName") or ""
    first = rjson.get("FirstName") or ""
    caller_name = f"{last}, {first}".strip(", ").strip()
    addr = rjson.get("Address") or {}
    address_street = addr.get("street") or ""
    city = addr.get("city") or ""
    postcode = addr.get("postcode") or ""
    address_city = f"{postcode} {city}".strip()

# ---------------------------
# UI
# ---------------------------

customtkinter.set_appearance_mode("dark")
root = customtkinter.CTk()
root.title("Anrufer-Info")
root.resizable(False, False)
root.attributes("-topmost", True)

# try:
#     root.attributes("-toolwindow", True)
# except Exception as e:
#     print(str(e))
#     pass

# Position bottom right (relative)
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
xpos = screen_w - (sub_xpos + app_width)
ypos = screen_h - (sub_ypos + app_height)
root.geometry(f"{app_width}x{app_height}+{xpos}+{ypos}")

# Content
make_label(root, f"Anruf ({datetime.now().strftime('%d.%m.%y %H:%M:%S')}) von:", ("Arial", 14), pady=2)
make_label(root, caller_name or "Unbekannt", ("Arial", 25), pady=0)
make_label(root, f"({caller})", ("Arial", 15), pady=4)
make_label(root, "", ("Arial", 8), pady=0)
make_label(root, address_street, ("Arial", 16), pady=0)
make_label(root, address_city, ("Arial", 16), pady=0)

if rjson:
    make_label(root, "", ("Arial", 10), pady=0)
    make_button(root, "Ticket erstellen",
                f"{wowi_url}/CallProtocol?PhoneNumber={caller}")

    contracts = rjson.get("Contracts")
    if not contracts:
        make_label(root, "", ("Arial", 10), pady=0)
        make_button(root, f"Person\n{rjson.get('IdNum')}",
                    f"{wowi_url}/open/Person/{rjson.get('Id')}")
    else:
        for entry in contracts:
            make_label(root, "", ("Arial", 5), pady=0)
            cid = entry.get("Id")
            cidnum = entry.get("IdNum")
            if cid:
                make_button(root, f"Vertrag\n{cidnum}",
                            f"{wowi_url}/open/LicenseAgreement/{cid}")

root.mainloop()
