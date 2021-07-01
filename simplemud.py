#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Un semplice gioco Multi-User Dungeon (MUD). I giocatori possono parlare
fra loro, esaminare l'ambiente e muoversi tra le stanze.

Alcune idee sulle cose da aggiungere:
    * Più stanze da esplorare
    * Un comando 'emote', ad es. 'emote lol' -> 'Marco scoppia a ridere'
    * Un comando 'sussurra' per parlare ai singoli giocatori
    * Un comando 'urla' per gridare ai gicatori in tutte le stanze
    * Oggetti da osservare nelle stanze, ad esempio
      'guarda caminetto' -> 'Vedi un fuoco ardente e scoppiettante'
    * Oggetti da prendere, ad esempio: 'prendi sasso' -> 'Hai preso il sasso'
    * Mostri da combattere
    * Tesori da raccogliere
    * Salvare i dati dei giocatori tra le sessioni
    * Accesso (login) con password
    * Un negozio in cui comperare oggetti

autore: Mark Frimston - mfrimston@gmail.com
traduzione italiana: Massimiliano De Ruosi - massimiliano.deruosi@gmail.com
"""

import time

# importa la classe: MUD server
from mudserver import MudServer

# struttura che definisce le stanze nel gioco. Prova ad aggiungere più stanze!
stanze = {
    "Taverna": {
        "descrizione": "Sei in una confortevole taverna riscaldata da un caminetto",
        "uscite": {"esterno": "Esterno"},
    },
    "Esterno": {
        "descrizione": "Ti trovi fuori da una taverna. Sta piovendo.",
        "uscite": {"interno": "Taverna"},
    }
}

# memorizza i giocatori nel gioco
giocatori = {}

# avvia il server
mud = MudServer()

# ciclo principale del gioco. Viene eseguito all'infinito (i.e. fino a quando il programma viene terminato)
while True:

    # pausa per 1/5 di secondo a ogni ciclo, così non usiamo
    # costantemente il 100% della CPU
    time.sleep(0.2)

    # 'update' deve essere chiamato durante il ciclo per mantenere il gioco attivo e con informazioni aggiornate
    mud.update()

    # gestisci i nuovi giocatori che si sono appena connessi
    for id in mud.get_new_players():

        # aggiungi i nuovi giocatori al dizinario, notare che non hanno
        # ancora un nome.
        # La chiave dek dizionario è il numero id del giocatore. Impostiamo
        # la loro stanza a None inizialmente finché non hanno inserito un nome
        # Prova ad aggiungere ulteriori statistiche del giocatore - livello,
        # oro, inventario, ecc.
        giocatori[id] = {
            "nome": None,
            "stanza": None,
        }

        # invia ad ogni nuovo giocatore la richiesta del prorio nome
        mud.send_message(id, "Qual è il tuo nome?")

    # gestisci i giocatori disconnessi di recente
    for id in mud.get_disconnected_players():

        # se per qualunque ragione il giocatore non è nell'elenco, saltalo e
        # passa al successivo
        if id not in giocatori:
            continue

        # gestisci ogni giocatore nel gioco
        for gid, gio in giocatori.items():
            # manda a ogni giocatore un messaggio per informarlo riguardo
            # i giocatori disconnessi
            mud.send_message(gid, "{} ha lasciato il gioco".format(
                                                        giocatori[id]["nome"]))

        # rimuove il giocatore dal dizionario dei giocatori
        del(giocatori[id])

    # gestisci ogni nuovo comando mandato dai giocatori
    for id, comando, parametri in mud.get_commands():

        # se per qualunque ragione il giocatore non è nell'elenco, saltalo e
        # passa al successivo
        if id not in giocatori:
            continue

        # se un giocatore non ha ancora inserito un nome, usa questo primo comando
        # come nome e spostalo nella stanza iniziale.
        if giocatori[id]["nome"] is None:

            giocatori[id]["nome"] = comando
            giocatori[id]["stanza"] = "Taverna"

            # gestisci ogni giocatore nel gioco
            for gid, gio in giocatori.items():
                # manda a tutti i giocatori un messaggio per informarli dell'ingresso
                # del nuovo giocatore
                mud.send_message(gid, "{} è entrato nel gioco".format(
                                                        giocatori[id]["nome"]))

            # manda al nuovo giocatore un messaggio di benvenuto
            mud.send_message(id, "Benvenuto nel gioco, {}. ".format(
                                                           giocatori[id]["nome"])
                             + "Scrivi 'aiuto' per una lista dei comandi. Buon divertimento!")

            # manda al nuovo giocatore la descrizione della stanza in cui si trova
            mud.send_message(id, stanze[giocatori[id]["stanza"]]["descrizione"])

        # ogni possibile comando è gestito sotto. Prova ad aggiungere
        # nuovi comandi al gioco!

        # comando 'aiuto'
        elif comando == "aiuto":

            # restituisce al giocatore la lista dei comandi possibili
            mud.send_message(id, "Comandi:")
            mud.send_message(id, "  di <messaggio>  - di' qualcosa ad alta voce, "
                                 + "ad es. 'di Ciao'")
            mud.send_message(id, "  osserva       - Esamina il "
                                 + "circondario, ad es. 'osserva'")
            mud.send_message(id, "  vai <uscita>  - Muoviti verso l'uscita "
                                 + "specificata, ad es. 'vai esterno'")

        # comando 'di'
        elif comando == "di":

            # gestisci ogni giocatore nel gioco
            for gid, gio in giocatori.items():
                # se sono nella stessa stanze del giocatore
                if giocatori[gid]["stanza"] == giocatori[id]["stanza"]:
                    # manda loro un messaggio dicendo ciò che ha detto il giocatore
                    mud.send_message(gid, "{} says: {}".format(
                                                giocatori[id]["nome"], parametri))

        # comando 'osserva'
        elif comando == "osserva":

            # memorizza la stanza corrente del giocatore
            rm = stanze[giocatori[id]["stanza"]]

            # restituisce al giocatore la descriione della stanza corrente
            mud.send_message(id, rm["descrizione"])

            giocatoriqui = []
            # gestisci ogni giocatore nel gioco
            for gid, gio in giocatori.items():
                # se sono nella stessa stanze del giocatore
                if giocatori[gid]["stanza"] == giocatori[id]["stanza"]:
                    # ...e hanno un nome da mostrare
                    if giocatori[gid]["nome"] is not None:
                        # aggiunge il loro nome alla lista
                        giocatoriqui.append(giocatori[gid]["nome"])

            # manda al giocatore un messaggio con la lista dei giocatori nella stanza
            mud.send_message(id, "Giocatori qui: {}".format(
                                                    ", ".join(giocatoriqui)))

            # manda al giocatore un messaggio con la lista delle uscite della stanza
            mud.send_message(id, "Le uscite sono: {}".format(
                                                    ", ".join(rm["uscite"])))

        # comando 'vai'
        elif comando == "vai":

            # memorizza il nome dell'uscita
            usc = parametri.lower()

            # memorizza la stanza corrente del giocatore
            rm = stanze[giocatori[id]["stanza"]]

            # se l'uscita specificata fa parte della lista delle uscite
            if usc in rm["uscite"]:

                # gestisci ogni giocatore nel gioco
                for gid, gio in giocatori.items():
                    # se il giocatore è nella stessa stanza e non è
                    # il giocatore che invia il comando
                    if giocatori[gid]["stanza"] == giocatori[id]["stanza"] \
                            and gid != id:
                        # mandagli un messaggio che dice che il giocatore
                        # ha lasciato la stanza
                        mud.send_message(gid, "{} è andato via dall'uscita '{}'".format(
                                                      giocatori[id]["nome"], usc))

                # aggiorna la stanza corrente del giocatore a quella a cui porta l'uscita
                giocatori[id]["stanza"] = rm["uscite"][usc]
                rm = stanze[giocatori[id]["stanza"]]

                # gestisci ogni giocatore nel gioco
                for gid, gio in giocatori.items():
                    # se il giocatore è nella stessa (nuova) stanza e non è il
                    # giocatore che invia il comando
                    if giocatori[gid]["stanza"] == giocatori[id]["stanza"] \
                            and gid != id:
                        # mandagli un messaggio che dice che il giocatore
                        # è entrato nella stanza
                        mud.send_message(gid,
                                         "{} è arrivato dall'uscita '{}'".format(
                                                      giocatori[id]["nome"], usc))

                # manda al giocatore un messaggio che dice dove di trova ora
                mud.send_message(id, "Sei arrivato in '{}'".format(
                                                          giocatori[id]["stanza"]))

            # l'uscita specificata non è stata trovata nella stanza
            else:
                # restiruisce un messaggio 'uscita sconosciuta'
                mud.send_message(id, "Uscita sconosciuta: '{}'".format(usc))

        # qualche altro comando non riconosciuto
        else:
            # restituisce un messaggio 'comando sconosciuto'
            mud.send_message(id, "Comando sconosciuto: '{}'".format(comando))
