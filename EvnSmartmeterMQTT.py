import serial
import time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from binascii import unhexlify
import sys
import string
import paho.mqtt.client as mqtt
from gurux_dlms.GXDLMSTranslator import GXDLMSTranslator
from bs4 import BeautifulSoup

from evnkeyfile import *

# EVN Schlüssel eingeben zB. "36C66639E48A8CA4D6BC8B282A793BBB"
#evn_schluessel = "dein EVN Schlüssel"

#MQTT Verwenden (True | False)
useMQTT = False
useMYSQL = False
useFILE = False
useTASMOTA = False 

#MQTT Broker IP adresse Eingeben ohne Port!
mqttBroker = "192.168.1.10"
mqttuser =""
mqttpasswort = ""
mqttport = 1883

#Aktuelle Werte auf Console ausgeben (True | False)
printValue = True

#Comport Config/Init
comport = "/dev/ttyUSB0"


#MQTT Init
if useMQTT:
    try:
        client = mqtt.Client("SmartMeter")
        client.username_pw_set(mqttuser, mqttpasswort)
        client.connect(mqttBroker, mqttport)
    except:
        print("Die Ip Adresse des Brokers ist falsch!")
        sys.exit()
    


tr = GXDLMSTranslator()
ser = serial.Serial( port=comport,
         baudrate=2400,
         bytesize=serial.EIGHTBITS,
         parity=serial.PARITY_NONE,                   
)






while 1:
    daten = ser.read(size=282).hex()
    systemTitel = daten[22:38]
    frameCounter = daten[44:52]
    frame = daten[52:560]

    frame = unhexlify(frame)
    encryption_key = unhexlify(evn_schluessel)
    init_vector = unhexlify(systemTitel + frameCounter)


    aesgcm = AESGCM(encryption_key)
    apdu = aesgcm.encrypt(init_vector, frame, b'0').hex()
    
    try:
        xml = tr.pduToXml(apdu[:-32],)
        soup = BeautifulSoup(xml, 'html.parser')
        results_32 = soup.find_all('uint32')
        results_16 = soup.find_all('uint16')
        results_int16 = soup.find_all('int16')
    except Exception as err:
        print("Fehler beim Synchronisieren. Programm bitte ein weiteres mal Starten.")
        print()
        print("Fehler: ", format(err))
        sys.exit()
       

    

    try:
        #Wirkenergie A+ in Wattstunden
        WirkenergiePA = str(results_32[0])
        WirkenergieP = int(WirkenergiePA[WirkenergiePA.find('=')+2:WirkenergiePA.find('=')+10],16)/1000

        #Wirkenergie A- in Wattstunden
        WirkenergieNA = str(results_32[1])
        WirkenergieN = int(WirkenergieNA[WirkenergieNA.find('=')+2:WirkenergieNA.find('=')+10],16)/1000

        #Momentanleistung P+ in Watt
        MomentanleistungPA = str(results_32[2])
        MomentanleistungP = int(MomentanleistungPA[MomentanleistungPA.find('=')+2:MomentanleistungPA.find('=')+10],16)

        #Momentanleistung P- in Watt
        MomentanleistungNA = str(results_32[3])
        MomentanleistungN = int(MomentanleistungNA[MomentanleistungNA.find('=')+2:MomentanleistungNA.find('=')+10],16)

        #Spannung L1
        SpannungL1A = str(results_16[0])
        SpannungL1 = int(SpannungL1A[SpannungL1A.find('=')+2:SpannungL1A.find('=')+6],16)*0.1

        #Spannung L2
        SpannungL2A = str(results_16[1])
        SpannungL2 = int(SpannungL2A[SpannungL2A.find('=')+2:SpannungL2A.find('=')+6],16)*0.1

        #Spannung L3
        SpannungL3A = str(results_16[2])
        SpannungL3 = int(SpannungL3A[SpannungL3A.find('=')+2:SpannungL3A.find('=')+6],16)*0.1

        #Strom L1
        StromL1A = str(results_16[3])
        StromL1 = int(StromL1A[StromL1A.find('=')+2:StromL1A.find('=')+6],16)*0.01

        #Strom L2
        StromL2A = str(results_16[4])
        StromL2 = int(StromL2A[StromL2A.find('=')+2:StromL2A.find('=')+6],16)*0.01

        #Strom L3
        StromL3A = str(results_16[5])
        StromL3 = int(StromL3A[StromL3A.find('=')+2:StromL3A.find('=')+6],16)*0.01

        #Leistungsfaktor
        LeistungsfaktorA = str(results_int16[0])
        Leistungsfaktor = int(LeistungsfaktorA[LeistungsfaktorA.find('=')+2:LeistungsfaktorA.find('=')+6],16)*0.001
        
        
        if printValue:
            print('Wirkenergie+: ' + str(WirkenergieP))
            print('Wirkenergie-: ' + str(WirkenergieN))
            print('MomentanleistungP+: ' + str(MomentanleistungP))
            print('MomentanleistungP-: ' + str(MomentanleistungN))
            print('Spannung L1: ' + str(SpannungL1))
            print('Spannung L2: ' + str(SpannungL2))
            print('Spannung L3: ' + str(SpannungL3))
            print('Strom L1: ' + str(StromL1))
            print('Strom L2: ' + str(StromL2))
            print('Strom L3: ' + str(StromL3))
            print('Leistungsfaktor: ' + str(Leistungsfaktor))
            print('Momentanleistung: ' + str(MomentanleistungP-MomentanleistungN))
            print()
            print()
    
    
        #MQTT
        if useMQTT:
            client.publish("Smartmeter/WirkenergieP",WirkenergieP)
            client.publish("Smartmeter/WirkenergieN",WirkenergieN)
            client.publish("Smartmeter/MomentanleistungP",MomentanleistungP)
            client.publish("Smartmeter/MomentanleistungN",MomentanleistungN)
            client.publish("Smartmeter/Momentanleistung",MomentanleistungP - MomentanleistungN)
            client.publish("Smartmeter/SpannungL1",SpannungL1)
            client.publish("Smartmeter/SpannungL2",SpannungL2)
            client.publish("Smartmeter/SpannungL3",SpannungL3)
            client.publish("Smartmeter/StromL1",StromL1)
            client.publish("Smartmeter/StromL2",StromL2)
            client.publish("Smartmeter/StromL3",StromL3)
            client.publish("Smartmeter/Leistungsfaktor",Leistungsfaktor)
        if useFILE:
            f = open("/run/smartmeter.html", "w")
            f.write("<html><head><title>Smartmeter</title> <meta http-equiv=\"refresh\" content=\"3\"> </head>  <body>  </body></html><pre>")
            f.write("Leistung   : " + str(MomentanleistungP - MomentanleistungN) + " W\n")
            f.write("Verbraucht : " + str(WirkenergieP) + "\n")
            f.write("Eingespeist: " + str(WirkenergieN) + "\n")
            f.write("L1 : " + str(SpannungL1) + "V " + str(StromL1)+ "A\n")
            f.write("L2 : " + str(SpannungL2) + "V " + str(StromL2)+ "A\n")
            f.write("L3 : " + str(SpannungL3) + "V " + str(StromL3)+ "A\n")
            f.close()
        
        if useMYSQL:
            import mysql.connector

            mydb = mysql.connector.connect(
              host="MYSQL_HOST",
              user="MYSQL_USER",
              password="MYSQL_PW",
              database="MYSQL_DB"
            )

            mycursor = mydb.cursor()

            sql = "INSERT INTO TABELLENNAME (zeit, bezug, einspeisung, leistung, U_L1, U_L2, U_L3, I_L1, I_L2, I_L3, Leistungsfaktor) VALUES (utc_timestamp(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            val = (WirkenergieP, WirkenergieN, MomentanleistungP - MomentanleistungN, SpannungL1, SpannungL2, SpannungL3, StromL1, StromL2, StromL3, Leistungsfaktor)
            mycursor.execute(sql, val)

            mydb.commit()

            print(mycursor.rowcount, "record inserted.")

        if useTASMOTA:
            import requests
            ip = 'tasmotaipadresse'
            p = 'tasmotapasswort'
            # wenn mindestens soviel eingespeist wird - wird der Tasmota Switch eingeschaltet
            einspeisungmin = 60

            ueberschuss = 'undef'

            if ( (MomentanleistungP - MomentanleistungN) < ( - einspeisungmin ) ):
                ueberschuss = 'On'
            if ( (MomentanleistungP - MomentanleistungN) >0 ):
                ueberschuss = 'Off'
            if ( (ueberschuss != 'undef') and ( oldueberschuss != ueberschuss )):
                oldueberschuss = ueberschuss
                ret = subprocess.call([
                'curl',
                'http://' + ip + '/cm?user=admin&password=' + p + '&cmnd=Power%20' + ueberschuss
                ])

    except BaseException as err:
        print("Fehler beim Synchronisieren. Programm bitte ein weiteres mal Starten.")
        print()
        print("Fehler: ", format(err))

        sys.exit()

