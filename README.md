## SwyxIt! / Wowiport connector

Diese Anwendung ermöglicht die Integration der Swyx-/Enreach-Telefonanlage in Wowiport:
* Anzeige des anrufenden Mieters bei eingehenden Anrufen
* Auflistung und Direktzugriff auf alle aktiven Verträge des Anrufers
* Vorausgefüllte Anrufprotokoll-Maske zur schnellen Erfassung im Nachrichtencenter

![Clientseitiger Screenshot](/screenshots/client_screen.png?raw=true)

Das Fenster erscheint bei einem eingehenden Anruf in der unteren rechten Ecke des Bildschirms.

### Voraussetzungen
* Wowiport ERP (für die Ticket-Funktion muss das Nachrichtencenter aktiv sein)
* OPENWOWI-API-Key
* Instanz von Wowicache (siehe https://github.com/seb-bau/wowicache)
* SwyxIt!-Client (getestet mit SwyxIt! Classic 14.11)
* Server, auf dem die Serverkomponente der Anwendung läuft. Dies kann ein ein Linux- oder Windows-Server sein, wahlweise  
lokal oder in "der Cloud"

### Funktion
Die Anwendung besteht aus einem Server und beliebig vielen Clients. Der Server ruft regelmäßig die Mieterbestandsdaten
über OPENWOWI ab
 und speichert sie zwischen (wowicache). Bei einem eingehenden Anruf senden die Clients die Nummer des Anrufers an den Server. Wird
 die Rufnummer im Bestand gefunden, sendet der Server die Mieterdaten und die zugehörigen Vertragsinformationen an den
 Client.

### Geplante Features
* Aktuell muss die Clientkomponente manuell auf den Unternehmens-PCs verteilt werden. Geplant ist ein Installer, der
über eine Softwareverteilung automatisch verteilt werden kann
* Manchmal ist es interessant zu sehen, wann und bei wem der Anrufer zuletzt angerufen hat. Hierfür soll eine Art
Anrufprotokoll im Client entstehen

### Installation (Server)
Die Anleitung bezieht sich auf Ubuntu Server 24.04. Eine Installation auf einem Windows-Server ist möglich, wird hier 
jedoch nicht behandelt
1. Wowicache in Betrieb nehmen
2. swserver konfiguireren und starten (Flask / uwsgi)
3. ggf. systemd unit anlegen (siehe swserver/swyxwowiport.service)

Hinweis: Wer den Server nicht selbst einrichten / betreiben möchte, kann eine Installation bei mir buchen. Kontakt via https://www.bytewish.de

### Installation (Client)
Die einfachste Verteilung erfolgt über das prebuild Setup (siehe Veröffentlichungen):
setup.exe an die Clients verteilen und Silent installieren:
swclient_setup.exe /SILENT /APIKEY=XXX /WOWIURL=https://meine-firma.wowiport.de /HOST=10.10.10.10
XXX steht dabei für den API-Key, der auf dem swserver gesetzt wurde, die URL muss angepasst werden und als Host wird der swserver verwendet  
Alternativ kann die Installation auch per GUI erfolgen, dann müssen im Anschluss die entsprechenden Werte in HKLM\Software\SwyxWowiport eingetragen werden.