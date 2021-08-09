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
import pickle
import os

# importa la classe: MUD server
from mudserver import MudServer

# se esiste il file 'stanze.p' contenente il database delle stanze, aprilo
if os.path.isfile("stanze.p"):
    stanze = pickle.load( open( "stanze.p", "rb" ) )
# ...altrimenti crea una struttura che definisce le stanze nel gioco e salvala
# nel file 'stanze.p'
else:
    stanze = {
        "Taverna": {
            "descrizione": "Sei in una confortevole taverna " 
            + "riscaldata da un caminetto",
            "uscite": {"Esterno",},
            "zona": "città"
        },
        "Esterno": {
            "descrizione": "Ti trovi fuori da una taverna. Sta piovendo.",
            "uscite": {"Taverna",},
            "zona": "strada"
        }
    }
    pickle.dump( stanze, open( "stanze.p", "wb") )

# 'giocatori' contiene i giocatori connessi nel gioco, la key è l'id della
# connessione, es.: {0: {"nome": "max", "stanza": "Taverna"}, ...}
# 'registro_giocatori' contiene i giocatori registrati, la key è il nome del
# giocatore, ad es. {"max": {"stanza": "Taverna"}, ...}
giocatori = {}
# se esiste il file 'registro_giocatori.p' contenente il database dei giocatori
# registrati, aprilo
if os.path.isfile("registro_giocatori.p"):
    registro_giocatori = pickle.load(open( "registro_giocatori.p", "rb" ) )
# ...altrimenti crea e salva il registro vuoto, che verrà popolato non appena
# si connetteranno i primi giocatori
else:
    registro_giocatori = {}
    pickle.dump(registro_giocatori, open( "registro_giocatori.p", "wb") )

bestiario = {
    "ratto gigante": {"zone": {"strada", "dungeon"}},
    "lupo selvatico": {"zone": {"foresta"}},
    "scheletro": {"zone": {"dungeon"}},
}

# inizializza il timer che scandisce la creazione di nuove creature nelle stanze
timer_creature = 0

# avvia il server
mud = MudServer()

# ciclo principale del gioco. Viene eseguito all'infinito (i.e. fino a quando
# il programma viene terminato)
while True:

    # pausa per 1/5 di secondo a ogni ciclo, così non usiamo
    # costantemente il 100% della CPU
    time.sleep(0.2)

    # 'update' deve essere chiamato durante il ciclo per mantenere il gioco
    # attivo e con informazioni aggiornate
    mud.update()

    # gestisci i nuovi giocatori che si sono appena connessi
    for id in mud.get_new_players():

        # aggiungi i nuovi giocatori al dizionario, notare che non hanno
        # ancora un nome.
        # La chiave del dizionario è il numero id del giocatore. Impostiamo
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

    # gestisci la creazione delle creature. Scelte e design:
    # 1) la creatura è vincolata alla stanza, massimo una creatura per stanza
    # 2) ogni stanza appartiene a una zona
    # 3) ogni tipo di creatura compare solo in determinate zone
    # 3) le creature non sono persistenti
    for nome_sta, sta in stanze.items():
        # se nella stanza c'è già una creatura, non ne aggiungo altre
        if "creatura" in sta.keys() and sta["creatura"]:
            pass
        else:
            for tipo, creatura in bestiario.items():
                # se: 1) la stanza ha una zona
                #     2) la zona della stanza fa parte di quelle della creatura
                #     3) il timer per la creazione delle creature è superato
                #        (es. con cicli di 0.2s, 30*5 = 30s)
                if ("zona" in sta.keys()
                        and sta["zona"] in creatura["zone"]
                        and timer_creature > 30*5):
                    # aggiungo la creatura alla stanza
                    sta["creatura"] = {"tipo": tipo}
                    timer_creature = 0
                    # gestisci ogni giocatore nel gioco
                    for gid, gio in giocatori.items():
                        # se sono nella stessa stanza di un giocatore...
                        if nome_sta == giocatori[gid]["stanza"]:
                            # ...gli annuncio la comparsa della creatura
                            mud.send_message(
                                gid, "una creatura è apparsa all'improvviso!")
    timer_creature += 1

    # gestisci ogni nuovo comando mandato dai giocatori
    for id, comando, parametri in mud.get_commands():

        # se per qualunque ragione il giocatore non è nell'elenco, saltalo e
        # passa al successivo
        if id not in giocatori:
            continue

        # se un giocatore non ha ancora inserito un nome, usa questo primo
        # comando come nome e verifica se fa parte dei giocatori registrati
        if giocatori[id]["nome"] is None:

            giocatori[id]["nome"] = comando
            # se il giocatore non viene trovato nel registro, va aggiunto
            if comando not in registro_giocatori.keys():
                registro_giocatori[comando] = {"stanza": "Taverna"}
                pickle.dump(
                    registro_giocatori,
                    open( "registro_giocatori.p", "wb") )
            # aggiorna i dati del giocatore connesso copiandoli dal registro
            giocatori[id]["stanza"] = registro_giocatori[comando]["stanza"]
            
            # gestisci ogni giocatore nel gioco
            for gid, gio in giocatori.items():
                # manda a tutti i giocatori un messaggio per informarli
                # dell'ingresso del nuovo giocatore
                mud.send_message(gid, "{} è entrato nel gioco".format(
                                                        giocatori[id]["nome"]))

            # manda al nuovo giocatore un messaggio di benvenuto
            mud.send_message(id, "Benvenuto nel gioco, {}. ".format(
                                                    giocatori[id]["nome"])
                + "Scrivi 'aiuto' per una lista dei comandi. "
                + "Buon divertimento!")

            # manda al nuovo giocatore la descrizione della stanza corrente
            mud.send_message(id, stanze[giocatori[id]["stanza"]]["descrizione"])

        # ogni possibile comando è gestito sotto. Prova ad aggiungere
        # nuovi comandi al gioco!

        # comando 'aiuto'
        elif comando == "aiuto":

            # restituisce al giocatore la lista dei comandi possibili
            mud.send_message(id, "Comandi:")
            mud.send_message(id, "  di <messaggio>    - di' qualcosa ad alta "
                + "voce, ad es. 'di Ciao'")
            mud.send_message(id, "  osserva           - Esamina il "
                + "circondario, ad es. 'osserva'")
            mud.send_message(id, "  vai <uscita>      - Muoviti verso l'uscita "
                + "specificata, ad es. 'vai esterno'")
            mud.send_message(id, "  crea <stanza>     - Crea nella stanza "
                + "corrente una nuova uscita che porta alla stanza indicata. "
                + "Se la stanza non esiste ne crea una nuova, ad es. "
                + "'crea Bosco'")
            mud.send_message(id, "  descrivi <testo>  - modifica la"
                + "descrizione della stanza corrente, ad es. 'descrivi Un "
                + "fitto bosco di faggio'")
            mud.send_message(id, "  cancella          - cancella la stanza "
                + "corrente")
            mud.send_message(id, "  zona              - visualizza o cambia la "
                + "zona della stanza corrente, ad es. 'zona', oppure: "
                + "'zona città'")

        # comando 'di'
        elif comando == "di":

            # gestisci ogni giocatore nel gioco
            for gid, gio in giocatori.items():
                # se sono nella stessa stanza del giocatore
                if giocatori[gid]["stanza"] == giocatori[id]["stanza"]:
                    # manda loro un messaggio dicendo ciò che ha detto il
                    # giocatore
                    mud.send_message(gid, "{} dice: {}".format(
                        giocatori[id]["nome"], parametri))

        # comando 'osserva'
        elif comando == "osserva":

            # memorizza la stanza corrente del giocatore
            sta = stanze[giocatori[id]["stanza"]]

            # restituisce al giocatore la descriione della stanza corrente
            mud.send_message(id, sta["descrizione"])

            giocatoriqui = []
            # gestisci ogni giocatore nel gioco
            for gid, gio in giocatori.items():
                # se sono nella stessa stanze del giocatore
                if giocatori[gid]["stanza"] == giocatori[id]["stanza"]:
                    # ...e hanno un nome da mostrare
                    if giocatori[gid]["nome"] is not None:
                        # aggiunge il loro nome alla lista
                        giocatoriqui.append(giocatori[gid]["nome"])

            # manda al giocatore un messaggio con la lista dei giocatori nella
            # stanza
            mud.send_message(id, "Giocatori qui: {}".format(
                ", ".join(giocatoriqui)))

            # manda al giocatore un messaggio con il nome della creatura nella
            # stanza, se presente
            if "creatura" in sta.keys() and sta["creatura"]:
                mud.send_message(id, "Creature qui: {}".format(
                    sta["creatura"]["tipo"]))

            # manda al giocatore un messaggio con la lista delle uscite della
            # stanza
            mud.send_message(id, "Le uscite sono: {}".format(
                ", ".join(sta["uscite"])))

        # comando 'vai'
        elif comando == "vai":

            # memorizza il nome dell'uscita
            usc = parametri

            # memorizza la stanza corrente del giocatore
            sta = stanze[giocatori[id]["stanza"]]

            # se l'uscita specificata fa parte della lista delle uscite
            if usc in sta["uscite"]:

                # gestisci ogni giocatore nel gioco
                for gid, gio in giocatori.items():
                    # se il giocatore è nella stessa stanza e non è
                    # il giocatore che invia il comando
                    if giocatori[gid]["stanza"] == giocatori[id]["stanza"] \
                            and gid != id:
                        # mandagli un messaggio che dice che il giocatore
                        # ha lasciato la stanza
                        mud.send_message(
                            gid,
                            "{} è andato via verso: '{}'".format(
                                giocatori[id]["nome"], usc))

                # aggiorna la stanza corrente del giocatore a quella a cui
                # porta l'uscita
                giocatori[id]["stanza"] = usc
                registro_giocatori[giocatori[id]["nome"]]["stanza"] = usc
                pickle.dump(
                    registro_giocatori,
                    open( "registro_giocatori.p", "wb") )

                sta = stanze[usc]

                # gestisci ogni giocatore nel gioco
                for gid, gio in giocatori.items():
                    # se il giocatore è nella stessa (nuova) stanza e non è il
                    # giocatore che invia il comando
                    if giocatori[gid]["stanza"] == usc and gid != id:
                        # mandagli un messaggio che dice che il giocatore
                        # è entrato nella stanza
                        mud.send_message(
                            gid,
                            "{} è arrivato da: '{}'".format(
                                giocatori[id]["nome"], usc))

                # manda al giocatore un messaggio che dice dove di trova ora
                mud.send_message(id, "Sei arrivato in '{}'".format(usc))

            # l'uscita specificata non è stata trovata nella stanza
            else:
                # restiruisce un messaggio 'uscita sconosciuta'
                mud.send_message(id, "Uscita sconosciuta: '{}'".format(usc))

        # comando 'crea'
        elif comando == "crea":
            usc = parametri
            # memorizza il nome della stanza corrente del giocatore
            nome_sta = giocatori[id]["stanza"]
            sta = stanze[nome_sta]
            if usc in sta["uscite"]:
                mud.send_message(id, "Impossibile creare "
                    + "l'uscita: '{}': esiste già!".format(usc))
            else:
                # aggiungo la nuova uscita alla stanza corrente
                sta["uscite"].add(usc)
                # controllo che la stanza destinazione dell'uscita non esista
                # già: in quel caso il comando aggiunge semplicemente un nuovo
                # percorso dalla stanza corrente...
                if not usc in stanze:
                    # ...se invece non esiste, creo la nuova stanza
                    stanze[usc] = {
                        "uscite":{nome_sta,},
                        "descrizione": 'Un posto sconosciuto'}
                # rendo persistenti i cambiamenti
                pickle.dump( stanze, open( "stanze.p", "wb") )
                # avverto tutti i giocatori che è stata creata la nuova uscita.
                mud.send_message(id, "Nella stanza '{}'".format(nome_sta)
                    + " è stata creata l'uscita: '{}'".format(usc))

        # comando 'descrivi'
        elif comando == "descrivi":
            desc = parametri
            # memorizza il nome della stanza corrente del giocatore
            nome_sta = giocatori[id]["stanza"]
            sta = stanze[nome_sta]
            if len(desc) == 0:
                mud.send_message(id, "Nessuna descrizione fornita!")
            else:
                # (sovra)scrive la descrizione della stanza corrente
                sta["descrizione"] = desc
                # rendo persistenti i cambiamenti
                pickle.dump( stanze, open( "stanze.p", "wb") )
                # avverto tutti i giocatori che è stata creata la nuova uscita.
                mud.send_message(id, "Nella stanza '{}'".format(nome_sta)
                    + "la descrizione è cambiata")

        # comando 'zona'
        elif comando == "zona":
            nome_zona = parametri
            # memorizza il nome della stanza corrente del giocatore
            nome_sta = giocatori[id]["stanza"]
            sta = stanze[nome_sta]
            if len(nome_zona) == 0:
                if "zona" in sta.keys() and sta["zona"]:
                    mud.send_message(id, "zona: {}".format(sta["zona"]))
                else:
                    mud.send_message(id, "nessuna zona definita per la stanza")
            else:
                # (sovra)scrive la zona della stanza corrente
                sta["zona"] = nome_zona
                # rendo persistenti i cambiamenti
                pickle.dump( stanze, open( "stanze.p", "wb") )
                # avverto il giocatore che la zona è cambiata
                mud.send_message(id, "La stanza '{}' ora ".format(nome_sta)
                    + "appartiene alla zona: '{}'".format(nome_zona))

        # comando 'cancella'
        elif comando == "cancella":
            # memorizza il nome della stanza corrente del giocatore
            nome_sta = giocatori[id]["stanza"]
            sta = stanze[nome_sta]
            uscite = sta["uscite"]
            if len(uscite) > 1:
                mud.send_message(id, "Impossibile cancellare la stanza: c'è "
                    + "più di una uscita!")
            else:
                # aggiorna la stanza corrente del giocatore con l'unica uscita
                for usc in uscite:
                    giocatori[id]["stanza"] = usc
                    stanze[usc]["uscite"].remove(nome_sta)
                mud.send_message(id,
                    "Sei stato trasportato nella stanza: '{}'".format(usc))
                # elimino stanza corrente
                del stanze[nome_sta]
                # rendo persistenti i cambiamenti
                pickle.dump( stanze, open( "stanze.p", "wb") )
                # avverto tutti i giocatori che è stata cancellata la stanza
                mud.send_message(id,
                    "La stanza '{}' è stata cancellata".format(nome_sta))

        # qualche altro comando non riconosciuto
        else:
            # restituisce un messaggio 'comando sconosciuto'
            mud.send_message(id, "Comando sconosciuto: '{}'".format(comando))
