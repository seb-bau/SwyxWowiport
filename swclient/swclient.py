import os
import requests
import platform
from tkinter import *
from dotenv import dotenv_values
import customtkinter
import sys
import webbrowser


def open_url(ourl: str) -> None:
    webbrowser.open(ourl, new=0, autoraise=True)


if len(sys.argv) == 1:
    exit()

curr_dir = os.path.abspath(os.path.dirname(__file__))
settings = dotenv_values(os.path.join(curr_dir, ".env"))

app_width = int(settings.get("app_width", 300))
app_height = int(settings.get("app_height", 400))
sub_xpos = int(settings.get("sub_xpos", 10))
sub_ypos = int(settings.get("sub_ypos", 80))
wowi_url = settings.get("wowi_url")

app_xpos_rel = app_width * -1 - sub_xpos
app_ypos_rel = app_height * -1 - sub_ypos
api_key = settings.get("key")
caller = sys.argv[1]
if len(caller) < 3:
    exit()

# Normalisierung für das WOwiport Protokollfenster
if caller.startswith("00"):
    caller = caller[1:]

host = settings.get("host")
client_name = platform.node()

url = f"{host}/caller_info"
params = {
    'phone': caller,
    'client': client_name
}

payload = {}
headers = {
    f'Authorization': f'Bearer {api_key}'
}

response = requests.request("GET", url, headers=headers, data=payload, params=params)
caller_name = "Unbekannt"
address_street = ""
address_city = ""
rjson = None
if response.status_code == 200:
    rjson = response.json()
    caller_name = f"{rjson.get('LastName')}"
    if rjson.get('FirstName') is not None and len(rjson.get('FirstName')) > 0:
        caller_name = f"{caller_name}, {rjson.get('FirstName')}"
    if rjson.get('Address') is not None:
        address_street = f"{rjson.get('Address').get('street')}"
        address_city = f"{rjson.get('Address').get('postcode')} {rjson.get('Address').get('city')}"

customtkinter.set_appearance_mode("dark")
root = customtkinter.CTk()
root.resizable(False, False)
root.configure(toolwindow=True)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

xpos = screen_width + app_xpos_rel
ypos = screen_height + app_ypos_rel

root.geometry('%dx%d+%d+%d' % (app_width, app_height, xpos, ypos))

top_label = customtkinter.CTkLabel(master=root, text="Anruf von:", font=("Arial", 18))
top_label.configure(anchor=CENTER)
top_label.pack()

caller_label = customtkinter.CTkLabel(master=root, text=caller_name,
                                      font=("Arial", 25))
caller_label.configure(anchor=CENTER)
caller_label.pack()

address_label = customtkinter.CTkLabel(master=root, text=f"({caller})", font=("Arial", 15))
address_label.configure(anchor=CENTER)
address_label.pack()

space_label = customtkinter.CTkLabel(master=root, text="", font=("Arial", 16))
space_label.configure(anchor=CENTER)
space_label.pack()

address_label = customtkinter.CTkLabel(master=root, text=address_street, font=("Arial", 16))
address_label.configure(anchor=CENTER)
address_label.pack()

city_label = customtkinter.CTkLabel(master=root, text=address_city, font=("Arial", 16))
city_label.configure(anchor=CENTER)
city_label.pack()

if rjson is not None:

    space_label = customtkinter.CTkLabel(master=root, text="", font=("Arial", 10))
    space_label.configure(anchor=CENTER)
    space_label.pack()

    mybutton = customtkinter.CTkButton(master=root, text=f"Ticket erstellen",
                                       command=lambda: open_url(f"{wowi_url}/CallProtocol?PhoneNumber={caller}"))
    mybutton.configure(anchor=CENTER)
    mybutton.pack()

    space_label = customtkinter.CTkLabel(master=root, text="", font=("Arial", 10))
    space_label.configure(anchor=CENTER)
    space_label.pack()

    mybutton = customtkinter.CTkButton(master=root, text=f"Person\n{rjson.get('IdNum')}",
                                       command=lambda: open_url(f"{wowi_url}/open/Person/{rjson.get('Id')}"))
    mybutton.configure(anchor=CENTER)
    mybutton.pack()

    contracts = rjson.get('Contracts')
    for entry in contracts:
        space_label = customtkinter.CTkLabel(master=root, text="", font=("Arial", 10))
        space_label.configure(anchor=CENTER)
        space_label.pack()

        conbutton = customtkinter.CTkButton(master=root, text=f"Vertrag\n{entry.get('IdNum')}",
                                            command=lambda: open_url(f"{wowi_url}/open/LicenseAgreement"
                                                                     f"/{entry.get('Id')}"))
        conbutton.configure(anchor=CENTER)
        conbutton.pack()

root.title("Anrufer-Info")
root.mainloop()
