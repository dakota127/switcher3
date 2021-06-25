#!/usr/bin/python
# coding: utf-8
# 
# ***********************************************************
# 	Class Dose 
#   
#   enkapsuliert alles, was eine Steckdose ausmacht.
#   Variablen zu Status der Dose und Methoden zum Verändern/Abfragen dieser Stati.
#
#   diese Class erbt von der MyPrint Class
#   
#   folgende public methods stehen zur Verfügung:
#       display_anzahl()
#       display_status()
#       set_zuhause()
#       set_nichtzuhause()
#       set_manuell()
#       set_auto_virtuell()
#       set_wiestatus()
#       reset_manuell()
#       set_auto()
#       show_status()
#       set_zimmer()
#       get_zimmer()
#       aktor_callback()
#
#   private functions:
#       _stat_list()
#       _message_out()
#   
#   Juli 2018, extended Februar 2021
#   by Peter K. Boxler
#************************************************
#


from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.myconfig import ConfigRead
import os
from datetime import date, datetime, timedelta

# -- Konstanten -----------------------------
DEBUG_LEVEL0 = 0
DEBUG_LEVEL1 = 1
DEBUG_LEVEL2 = 2
DEBUG_LEVEL3 = 3      
WAIT_STATUS_MELDUNG = 3         # von früher, muss nun klein ein   


# messages to frontend
TOFE_DONEDEV    = 1
TOFE_DONESWITCH = 2
TOFE_INITDEV    = 3
TOFE_RESET_ALL  = 9

configfile_name = "swconfig.ini"
config_section = "dose"                # look up values in this section
progname = "dose "

EXSTAT      = ["Aus","Ein"]
SCHPRIO     = ["Typ0","Typ1","Typ2"]
SCHMODUS    = ["auto","manuell"]
SCHART      = ["fill","Test (5 LED)","Funk","Smart","Funk2","Funk3"]  # element zero ist filler

# ***** Variables *****************************
#   Struktur (Liste) der Daten, die aus dem Configfile swconfig.ini gelesen werden
#   hier die defaultwerte der 'variablen'
#
#   Achtung:
#   Schaltart 1 ist für Testumgebung. 
#   wenn eine dose 1 schaltart 1 hat, müssen die anderen Dosen auch schaltart 1 haben
#   script sorgt dafür (mit Warnung), dass dies eingehalten wird.
#   Amsonsten ist schaltart frei wählbar

cfglist_dos = {
        "dose_1_schaltprio"     : 1,
        "dose_2_schaltprio"     : 1,
        "dose_3_schaltprio"     : 1,
        "dose_4_schaltprio"     : 1,
        "dose_5_schaltprio"     : 1,  
        "dose_6_schaltprio"     : 1,
       
        "dose_1_schaltart"      : 1,
        "dose_2_schaltart"      : 1,
        "dose_3_schaltart"      : 1,
        "dose_4_schaltart"      : 1,
        "dose_5_schaltart"      : 1,  
        "dose_6_schaltart"      : 1,
#                                         
        "debug_schalt"  : 1,
        }

#--------------------------------------------------
class Dose(MyPrint):
    ' klasse dose '
    dosenzahler=0           # Class variable Anzahl Dosen
#
    def __init__(self, dose,testmode_in,debug_in, config_filename_in, mqtt_status_in, mqttc_in, callback_function):   # Init Methode der Dose, setzt Instanz Variablen
        self.errorcode = 8          # initwert, damit beim Del des Aktors richtig gehandelt wird
        self.nummer = Dose.dosenzahler      
        self.status_intern = 0          # interner Status der Dose, gemäss programmierten Aktionen
        self.status_extern = 0          # externer Status der Dosen (für Status-Anzeige)
                                        # die folgenden drei variablen beeinflussen die Art und weise des schaltens der Dose
        self.schaltart = 0              # technische schaltart, bestimmt den Aktor, der benutzt werden muss
        self.schaltmodus = 0            # 0=auto, 1=manuell
        self.schaltprio = 0             # 1: normal, 2: dose schalten ohne berücksichtigung zuhause/nicht zuhause 

        self.zuhause = False            # False=abwesend, True=zuhause
        self.debug = debug_in
        self.zimmer_name = ""      
        Dose.dosenzahler += 1           # erhögen dosenzahler
        self.status_extern = 0
        self.configfile = config_filename_in          
        self.dosen_nummer = Dose.dosenzahler
        self.myprint (DEBUG_LEVEL2 ,progname + "dose{} dosen_init called, debug: {}  testmode: {}".format (self.dosen_nummer,debug_in,testmode_in))
        self.testmode = testmode_in
        self.mqttc = mqttc_in           # instanz mqtt client
        self.callback = callback_function
        self.mqtt_connect = mqtt_status_in
        self.msg_variante = 1           # default wert Test Pyload
        self.subscribe = 0
        self.time_last_aktion = datetime.now()         # zeit merken 
        self.e = []
        self.debug_level2_mod = DEBUG_LEVEL2
        self.tmp = 0
        self.schalt = ""                # hilfsfeld   
        self.schalton = 0                  # anzahl schaltvorgänge ON
        self.schaltoff = 0                 # anzahl schaltvorgänge OFF 
 # nun schaltart für die Dosen  aus config holen
       
       
        self.myprint (DEBUG_LEVEL2 ,progname + "dose{} init called, configfile: {}". format(dose, self.configfile))
        config = ConfigRead(debug_level = debug_in)      # instanz der ConfigRead Class    
       
        
        ret=config.config_read(self.configfile,config_section,cfglist_dos)
        if ret > 0:
            self.myprint (DEBUG_LEVEL2 ,progname +  "dosen init: config_read hat retcode: {}".format (ret))
            self.errorcode=99
            return None


        tmp = 0

        try:
        # input comes from configfile

            self.schalt = "dose_" + str(self.dosen_nummer) + "_schaltart"
            self.schalt = cfglist_dos[self.schalt]           # suche den Wert von schaltart aus Config-file
            self.tmp = "dose_" + str(self.dosen_nummer) + "_schaltprio"
            self.schaltprio = int(cfglist_dos[self.tmp])           # suche den Wert von modus aus Config-file
            tmp = int(cfglist_dos["debug_schalt"])            # suche den Wert von debug_schalt aus Config-file
      
        except KeyError :
            self.myprint (DEBUG_LEVEL1 ,progname + "dosen init: KeyError in cfglist_dos, check values!")   
            self.schalt = "1,1,1"           # default value in case of error
            self.schaltprio = 1             # default value
        
        if tmp > 0:
            self.debug_level2_mod  =  DEBUG_LEVEL0
            self.myprint (DEBUG_LEVEL0 ,progname + "dose{} alle schaltaktionen werden logged (in configfile)".format(self.dosen_nummer))

        if self.schaltprio == 2 :
            self.myprint (DEBUG_LEVEL1 ,progname + "dose{} hat modus_1 = 2".format(self.dosen_nummer))

            
            
         # schaltart auswerten....   
        if len(self.schalt) == 0:
            self.myprint (DEBUG_LEVEL1 ,progname + "dose{} Schaltart ungültig, nehme default 1".format(self.dosen_nummer))
            self.schalt = "1,1,1"
        if len(self.schalt) == 1:
            self.schaltart  = int(self.schalt)    
        if len(self.schalt) > 1:
            self.e=self.schalt.split(",")
        if len(self.e) > 1:
            self.schaltart = int(self.e[0])
            self.msg_variante = int(self.e[1])
        if len(self.e) > 2: 
            self.subscribe = int(self.e[2])
            
            
        if  self.schaltart == 3:
            self.myprint (DEBUG_LEVEL1 ,progname +"dose{} Schaltart: {}, MQTT_status: {}, msg_var:{}, subscribe:{}".format(self.dosen_nummer,self.schaltart, self.mqtt_connect, self.msg_variante, self.subscribe))
        else:
            self.myprint (DEBUG_LEVEL1 ,progname +  "dose{} Schaltart: {}".format(self.dosen_nummer,self.schaltart))
        
        
        if self.testmode:
            self.myprint (DEBUG_LEVEL1 ,progname + "dose{} nehme Schaltart 1, Testmode ist Ja !".format(self.dosen_nummer))
            self.schaltart = 1
        
        # schaltart 3 benötigt mqtt und das muss zu diesem Zeitpunkt ok und connected sein, 
        # falls nicht, nehmen wir schaltart 1 (led)
        if self.schaltart == 3 and self.mqtt_connect == False:
            self.myprint (DEBUG_LEVEL0 ,progname + "dose{} nehme Schaltart 1 da MQTT nicht definiert oder fehlerhaft ist !".format(self.dosen_nummer))
            self.schaltart = 1
                
# plausicheck 
        if  self.dosen_nummer > 4 :
            if self.schaltart == 1 or self.schaltart == 3:     # dosennummer 5 und ev. 6 dürfen nicht schaltart 2 haben (Funksteckdosen)
                pass
            else:  
                self.myprint (DEBUG_LEVEL0 ,progname + "dose{} darf nur Schaltart 3 oder 1 haben, nehme 1".format(self.dosen_nummer))
                self.schaltart = 1;

            
        if self.schaltart == 1:
            import sub.swc_aktor_1                      # import actor 1 class
            self.myaktor=sub.swc_aktor_1.Aktor_1(self.dosen_nummer,self.debug,self.configfile)          # Instanz der Aktor Class erstellenb
        elif self.schaltart == 2:
            import sub.swc_aktor_2                      # import actor 2 class
            self.myaktor=sub.swc_aktor_2.Aktor_2(self.dosen_nummer,self.debug,self.configfile)          # Instanz der Aktor Class erstellenb
        elif self.schaltart == 3:
            import sub.swc_aktor_3                      # import actor 3 class        
            self.myaktor=sub.swc_aktor_3.Aktor_3(self.dosen_nummer,self.debug,self.msg_variante,self.subscribe,self.configfile, self.mqttc, self.aktor_callback)          # Instanz der Aktor Class erstellenb
        elif self.schaltart == 4:
            import sub.swc_aktor_4                      # import actor 4 class       
            self.myaktor=sub.swc_aktor_4.Aktor_4(self.dosen_nummer,self.debug,self.configfile)          # Instanz der Aktor Class erstellenb
        elif self.schaltart == 5:
            import sub.swc_aktor_5                      # import actor 5 class        
            self.myaktor=sub.swc_aktor_5.Aktor_5(self.dosen_nummer,self.debug,self.configfile)          # Instanz der Aktor Class erstellenb

        else:
            self.myprint (DEBUG_LEVEL2 ,progname +  "dose{} falsche Schaltart {}".format (self.dosen_nummer,self.schaltart))
            self.myprint (DEBUG_LEVEL2 ,progname +  "dose{} Nehme Default-Schaltart 1".format (self.dosen_nummer))
            import sub.swc_aktor_1 
            self.myaktor=swc_aktor_1.Aktor_1(self.dosen_nummer,self.debug)          # Instanz der Aktor Class erstellenb
           

        if self.myaktor.errorcode == 99:
            self.myprint (DEBUG_LEVEL2 ,progname +  "Aktor: {} meldet Fehler {}".format (self.dosen_nummer, self.myaktor.errorcode))	 
            raise RuntimeError('---> Switcher ernsthafter Fehler, check switcher3.log <----')

        self.time_last_aktion =  datetime.now()         # zeit merken 

        self.myprint (DEBUG_LEVEL0 ,progname + "object created: {}".format(self.myaktor))

        self.myprint (DEBUG_LEVEL2 ,progname +  "dose{} ausschalten (init dose), schaltart: {}".format (self.dosen_nummer, self.schaltart))
        self.myaktor.schalten(0,  self.debug_level2_mod)
        self.errorcode = 0          # init der Dose ok 


#-------------------------------------------
# __repr__ function dose
# 
    def __repr__ (self):

        rep = "Dose (" + str(self.dosen_nummer) + "," + self.zimmer_name + "," + SCHART[self.schaltart] + "," + SCHPRIO[self.schaltprio] + ")"
        return (rep)


#-------------------------------------------
# private function assemble status list for dose
    def _stat_list(self):

        # assemble a list containing all status Info of the dose
        # and return this list to the caller
        dos_list =[]
        dos_list.append (self.dosen_nummer)
        dos_list.append (self.status_extern)                    # externer status
        dos_list.append (EXSTAT[self.status_extern])            # externer status
        dos_list.append (self.status_intern)
        dos_list.append (EXSTAT[self.status_intern])
        dos_list.append (self.schaltmodus)
        dos_list.append (SCHMODUS[self.schaltmodus])            # auto/manuell
        dos_list.append (SCHPRIO[self.schaltprio] + " / " + SCHART[self.schaltart])   # Typ0= nur manuell, Typ1 = normal, Typ2 = immer
        dos_list.append (SCHART[self.schaltart])                # 1 bis 5
        dos_list.append (self.zimmer_name)
        dos_list.append (self.schalton)
        dos_list.append (self.schaltoff)
        dos_list.append (0)                     # reserve
      #  print ("sta_list:{}".format(dos_list))

        return (dos_list)           # return this list to caller
    

# ---- private Funktion _message_out() ------------------------------
# ,
    def _message_out(self):


        self.callback (self._stat_list())      # notfy calller that dose was switched

# Funktion dispay_anzahl()  gibt die Anzahl der instantiierten Dosen zurück
#--------------------------------------------------------------------------
    def display_anzahl(self):
        return(Dose.dosenzahler)

# Funktion dispay_anzahl()  gibt status aus auf stdout
#--------------------------------------------------------------------------
    def display_status(self):
       self.myprint (DEBUG_LEVEL2, "Dose:{} Status intern {} Status extern {} Modus {} Zuhause {}".format (self.nummer, self.status_intern,self.status_extern,self.schaltmodus, self.zuhause))

# Funktion self._count_schalt()  zähnle anzahl schlatvorgänge
#--------------------------------------------------------------------------
    def _count_schalt(self,how):
        if how == 1:
            self.schalton += 1
        else:
            self.schaltoff += 1    

# Funktion set_zuhause()  schaltet dose aus, falls Modus nicht manuell ist, setzt externen Status
#--------------------------------------------------------------------------
    def set_zuhause(self):
# 
        self.zuhause=True
        self.myprint (self.debug_level2_mod ,  "dose{} set_zuhause called, zuhause aktuell: {}" .format (self.dosen_nummer, self.zuhause))
        if self.schaltmodus == 1: 
            return            # wenn modus manuell mach nichts weiter

        if self.schaltprio == 2 or self.schaltprio == 0: 
            return            # wenn prio 0 oder 2 mach nichts weiter, dose wir von zuhause/nicht zuhause nicht beeinflusst
       
        self.time_last_aktion =  datetime.now()         # zeit merken 
        
        self.status_extern=0
        self.myprint (self.debug_level2_mod, "dose {} ausschalten, schaltart: {}".format (self.dosen_nummer, self.schaltart))
        self.myaktor.schalten(0,  self.debug_level2_mod)
        self._count_schalt(0)            # zählen schaltvorgänge

        self._message_out()        # notfy calller that dose was switched
    
# ---- Funktion set_dosen_nichtzuhause ------------------------------
#      schaltet die Dose ein, falls interner Status 1 ist - aber nicht, wenn Modus =manuell ist 
    def set_nichtzuhause(self):

        self.zuhause=False
        self.myprint (self.debug_level2_mod ,  "dose{} set_nicht zuhause called, zuhause aktuell: {}" .format (self.dosen_nummer, self.zuhause))

        if self.schaltmodus == 1: 
            return   # manuell, wir machen nichts
        if self.schaltprio == 2 or self.schaltprio == 0: 
            return            # wenn prio 0 oder 2 mach nichts weiter, dose wir von zuhause/nicht zuhause nicht beeinflusst
       
        self.time_last_aktion =  datetime.now()         # zeit merken 
            
        if self.status_intern==1:
            self.status_extern=1
            self.myprint (self.debug_level2_mod, "dose {} einschalten, schaltart: {}".format (self.dosen_nummer, self.schaltart))
            self.myaktor.schalten(1,  self.debug_level2_mod)
            self._count_schalt(1)            # zählen schaltvorgänge
            self._message_out()      # notfy calller that dose was switched      # notfy calller that dose was switched
            
        else:
            self.status_extern=0
            self.myprint (self.debug_level2_mod, "dose {} ausschalten, schaltart: {}".format (self.dosen_nummer, self.schaltart))
            self.myaktor.schalten(0,  self.debug_level2_mod)
            self._count_schalt(0)            # zählen schaltvorgänge
            self._message_out()      # notfy calller that dose was switched

# ---- Funktion set_dosen_wiestatus ------------------------------
#      schaltet die Dose ein, falls interner Status 1 ist - aber nicht, wenn Modus =manuell ist 
    def set_wiestatus(self):
# 
        self.myprint (self.debug_level2_mod ,  "dose{} set_dose_wiestatus called, zuhause: {}" .format (self.dosen_nummer, self.zuhause))
        if self.schaltmodus == 1: 
            return   # manuell, wir machen nichts

        self.time_last_aktion =  datetime.now()         # zeit merken 
            
        if self.status_intern==1:
            self.status_extern=1
            self.myprint (self.debug_level2_mod, "dose{} einschalten, schaltart: {}".format (self.dosen_nummer, self.schaltart))
            self.myaktor.schalten(1,  self.debug_level2_mod)
            self._count_schalt(1)            # zählen schaltvorgänge
        else:
            self.status_extern=0
            self.myprint (self.debug_level2_mod, "dose{} ausschalten, schaltart: {}".format (self.dosen_nummer, self.schaltart))
            self.myaktor.schalten(0,  self.debug_level2_mod)
            self._count_schalt(0)            # zählen schaltvorgänge
        self._message_out()      # notfy calller that dose was switched

# ---- Funktion toggle dosen manuell ------------------------------
#      schaltet die Dose um , setzt Modus auf manuell
#      zuhause spielt hier keine Rolle, da ja manuell geschaltet wird.
    def set_toggle(self):

        self.myprint (self.debug_level2_mod ,  "dose{} set_toggle called, zuhause: {}".format (self.dosen_nummer,self.zuhause))
    
        if (self.status_extern == 0 ):
            self.status_extern = 1 
        else:
            self.status_extern = 0

        self.schaltmodus = 1
        self.time_last_aktion =  datetime.now()         # zeit merken 

        self.myprint (self.debug_level2_mod, "dose{} manuell toggle , schaltart: {}".format (self.dosen_nummer, self.schaltart))
        self.myaktor.schalten(self.status_extern,  self.debug_level2_mod)
        self._count_schalt(self.status_extern)            # zählen schaltvorgänge
        # notify caller that dose has switched
        self._message_out()

        


# ---- Funktion set_dosen_manuell ------------------------------
#      schaltet die Dose gemäss Parameter how ein/aus, setzt Modus auf manuell
#       Parameter how= 1 für ein, 0 für aus
    def set_manuell(self, how):

        self.myprint (self.debug_level2_mod ,  "dose{} set_manuell called, how: {}  zuhause: {}".format (self.dosen_nummer,how, self.zuhause))
    
        self.status_extern = how
        self.schaltmodus = 1
        self.time_last_aktion =  datetime.now()         # zeit merken 

        self.myprint (self.debug_level2_mod, "dose{} manuell schalten , schaltart: {}".format (self.dosen_nummer, self.schaltart))
        self.myaktor.schalten(how,  self.debug_level2_mod)
        self._count_schalt(how)            # zählen schaltvorgänge
         #  self.swinterface.interface_out (1, self.dosen_nummer, self.status_extern , self.schaltmodus)   
        self._message_out()      # notfy calller that dose was switched
        
# ---- Funktion reset manuell ------------------------------
#   setzt Modus auf Auto (0) und schaltet Dose gemäss dem aktuellen internen Status
    def reset_manuell(self):
        self.myprint (self.debug_level2_mod,  "dose{} reset_manuell called, modus: {}, status_intern: {}".format (self.dosen_nummer, self.schaltmodus, self.status_intern))
        if self.schaltmodus == 0 or self.schaltprio == 0:
            return                  # wir behandlen nur Dosen mit modus manuell, und prio 0 werden auch nicht behandelt
        self.time_last_aktion =  datetime.now()         # zeit merken 
            
        self.schaltmodus = 0
        if self.status_intern == 1:   
            self.status_extern = 1
            self.myprint (self.debug_level2_mod , "dose{} reset_manuell: einschalten , schaltart: {}".format (self.dosen_nummer, self.schaltart))
            self.myaktor.schalten(1,  self.debug_level2_mod)
            self._count_schalt(1)            # zählen schaltvorgänge
        else:
            self.status_extern = 0
            self.myprint (self.debug_level2_mod , "dose{} reset_manuell: ausschalten , schaltart: {}".format (self.dosen_nummer, self.schaltart))
            self.myaktor.schalten(0,  self.debug_level2_mod)
            self._count_schalt(0)            # zählen schaltvorgänge
         #  self.swinterface.interface_out (1,self.dosen_nummer, self.status_extern , self.schaltmodus)   
        self._message_out()     # notfy calller that dose was switched
          
 
# ---- Funktion set_auto,  ------------------------------
#   schaltet dose gemäss how, jedoch nur, wenn Modus 'Auto' ist (bei Modus 'Manuell' wird nicht geschaltet)  
    def set_auto(self, how):
# how= 1 für ein, 0 für aus
        self.myprint (self.debug_level2_mod ,  "dose{} set_auto called, how: {}  modus: {}  zuhause: {}".format (self.dosen_nummer,how,self.schaltmodus,self.zuhause))
   
        if self.schaltprio == 0: 
            return            # wenn prio 0 machen wir gar nichts, diese Dosen werden nur manuell geschaltet
 
        self.status_intern = how      # interner status wird in jedem Fall nachgeführt
 
        if self.zuhause :
            if self.schaltprio == 1:    # solche dosen werden auto geschaltet
                return                 # wenn jemand da ist wird bloss interner status nachgeführt
    
        if self.schaltmodus == 0:           # Nur wirklich schalten, wenn modus auto ist - externer status nachführen
            self.status_extern=how
            self.time_last_aktion =  datetime.now()         # zeit merken 

            self.myprint (DEBUG_LEVEL2,  "dose{} auto schalten {}".format (self.dosen_nummer, how))
            self.myaktor.schalten(how,  self.debug_level2_mod)
            self._count_schalt(how)            # zählen schaltvorgänge

            # now that the actor switched a device we need to inform 
            self._message_out()
            
            return 


# ---- Funktion set_auto_virtuell,  ------------------------------
#   schaltet dose nicht, setzt aber internen Status gemäss how
#   wird bei der Abarbeitung der vergangenen Aktionen des Tages benutzt im Switcher
#   bei Funk wollen wir nicht so lange funken, bis alles abgearbeitet ist
    def set_auto_virtuell(self, how):
# how= 1 für ein, 0 für aus
        self.myprint (DEBUG_LEVEL2,  "dose{} set_auto_virtuell called, how: {}  modus: {}".format (self.dosen_nummer,how,self.schaltmodus))
        if self.schaltprio == 0: 
            return            # wenn prio 0 machen wir gar nichts, diese Dosen werden nur manuell geschaltet

        self.status_intern=how      # interner status wird in jedem Fall nachgeführt


# ---- Callback Aktor ------------------------------
#   der smart switch hat eine statusmeldung (ON oder OFF) gesendet.
#   Voraussetzung: der smart switch sendet immer eine statusmeldung, sowohl wenn vom switcher geschaltet,
#   als auch, wenn von Hand an der dose geschaltet. Wir müssen die beiden Dinge aber irgendwie unterscheiden.
#   dies machen wir so:
#   statusmeldungen, die innerhalb von 30 sekunden kommen, nachdem switcher2 selbst geschaltet hat,
#   werden ignoriert. Dies, weil der Switcher (also die Dose) den internen/externen Status bereits selbst gesetzt hat.
#   statusmeldungen hingegen, die mehr als 30 sekunden später eintreffen, werden betrachtet als von HAND AN DER DOSE
#   geschaltet. Dies kann ja irgendwann passieren. In diesen Fall wird der status der dose verändert.
#   ist etwas krude, tut aber den Dienst.
    def aktor_callback(self, client, userdata, message):
        
        payload = message.payload.decode()      # payload ist ON oder OFF
        time_new =  datetime.now() 
        delta = time_new - self.time_last_aktion
        delta = int(delta.seconds)     # delta in sekunden
        self.myprint (DEBUG_LEVEL1,  "dose{} aktor_callback() called, payload: {}, zeit seit letzter aktion: {} sek.".format (self.dosen_nummer, payload, delta))
        if delta > WAIT_STATUS_MELDUNG:
        
            if payload == "ON" :
                self.status_extern = 1          # dose wurde eingeschaltet
                self.schaltmodus = 1            # sie ist manuell eingeschaltet
                self.myprint (DEBUG_LEVEL2,  "dose{} aktor_callback() setze dose ein/maunell ".format (self.dosen_nummer))
            if payload == "OFF" :
                self.myprint (DEBUG_LEVEL2,  "dose{} aktor_callback() setze dose aus/maunell ".format (self.dosen_nummer))
                self.status_extern = 0          # dose wurde ausgeschaltet
                self.schaltmodus = 1            # schaltmodus nun manuell
            self._message_out()        # notfy calller that dose was switched    
        else:
             self.myprint (DEBUG_LEVEL1,  "dose{} aktor_callback() Meldung von Dose gekommen, Zeitdiff kleiner als: {} sek, mache nichts".format(self.dosen_nummer,WAIT_STATUS_MELDUNG))
 

# ---- Funktion set Zimmer ------------------------------
#       setzen Zimmer Name
    def set_zimmer(self,namezimmer):
        self.myprint (DEBUG_LEVEL2,  "dose{} set_zimmer called: {}".format (self.dosen_nummer,namezimmer))
        
        self.zimmer_name=namezimmer
            
# ---- Funktion get Zimmer ------------------------------
#       setzen Zimmer Name
    def get_zimmer(self):
        self.myprint (DEBUG_LEVEL2,  "dose{} get_zimmer called".format (self.dosen_nummer))
        
        return (self.zimmer_name)

        

# ---- Funktion show_status2 ------------------------------
#       gibt liste zurück mit values
    def show_status(self):

        self.myprint (DEBUG_LEVEL2,  "dose{} show_status called".format (self.dosen_nummer))
        
        return (self._stat_list())      #return list of statis to the caller


            
# Destruktor der Class Dose
#------------------------------------------------
    def __del__(self):
        # beenden, dose off setzen
        if self.errorcode == 0:         # bei initwert 8 wird demnach nichts gemacht
        
            del self.myaktor
        self.status_extern=0
        self.status_intern=0

#------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swc_dose.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
