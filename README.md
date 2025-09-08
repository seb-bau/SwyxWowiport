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
* SwyxIt!-Client (getestet mit SwyxIt! Classic 14.11)
* Server, auf dem die Serverkomponente der Anwendung läuft. Dies kann ein ein Linux- oder Windows-Server sein, wahlweise  
lokal oder in "der Cloud"

### Funktion
Die Anwendung besteht aus einem Server und beliebig vielen Clients. Der Server ruft regelmäßig die Mieterbestandsdaten
über OPENWOWI ab
 und speichert sie zwischen. Bei einem eingehenden Anruf senden die Clients die Nummer des Anrufers an den Server. Wird
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
1. OPENWOWI-API-Key in Wowiport erzeugen. Notwendige Endpunktberechtigungen: Objektdaten, Personen lesen, Vertragsdaten
mit personenbezogenen Details
2. Repository klonen (z.B. nach /opt/swyxwowiport)
3. Requirements aus swserver/requirements.txt via pip installieren (ggf. virtuelles Environment erstellen)
4. Die Konfig-Dateien aus /opt/swyxwowiport/config zu app.ini und server.ini kopieren
5. 

### Installation (Client)