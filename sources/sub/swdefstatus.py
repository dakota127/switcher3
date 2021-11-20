# coding: utf-8
#  Global Variable StatusInfo für Switcher 3--------------------
#   Status (Klein) Info Switcher
#   ist List of List - wird gefüllt und dann in ein JSON konvertiert (was einen String ergibt)
#   dieser String wird vom Switcher an den Client übergeben ,
#   dieser wandelt das Json Object wieder in einen Python List um.
#

                
info_klein = [
               
                ["Datum/Zeit", " " ],
                ["Wochentag", " "  ],
                ["Nächste", " " ],
                ["Letzte"," "],
                ["Temperatur Innen", " " ],       
                ["Temperatur Aussen", " " ],
                
                ]


#-------------------------------------
#  Global Variable StatusInfo für Switcher3 --------------------
#   Status Info Switcher
#   ist List of List - wird gefüllt und dann in ein JSON konvertiert (was einen String ergibt)
#   dieser String wird vom Switcher an den Client übergeben ,
#   dieser wandelt das Json Object wieder in einen Python List um.
#

info_gross = [
            
                ["Version / Dosen", " " ],              # index 0
                ["Start", " "],                         # 1
                ["Laufzeit Tage", " " ],                # 2
                ["Total Schaltaktionen", " "],			# 3
                ["Woche / Adjust (Min)", " "],           # 4
                ["Zuhause", " " ],                      # 5
                ["File-ID", " " ],                      # 6   
                ["Testmode / Debug"," " ],                # 7           
                ["Heute", " " ],                        # 8  
                ["Aktueller Tag", " " ],                # 9
                ["Aktionen an diesem Tag", " " ],       # 10  
                ["Davon ausgeführt", " " ],             # 11
                ["Wartend bis"," " ],                   # 12
                ["Nächste", " " ],                     # 13
                ["Letzte"," " ],                       # 14
                ["Wetter"," " ],                        # 15
                ["Reset Manuelle", " " ],               # 16
                ["Host Info", " "],                     # 17
                
                ]                
#-------------------------------------
#  Global Variable StatusInfo für Switcher-Daemon --------------------
# Status Info Switcher fuer Wetter
#   ist List of List - wird gefüllt und dann in ein JSON konvertiert (was einen String ergibt)
#   dieser String wird vom Switcher an den Client übergeben ,
#   dieser wandelt das Json Object wieder in einen Python List um.
#

status_wetter_innen = [
               ["Temperatur Innen", " " ],
               ["Feuchtigkeit Innen"," " ],
               ["Messung am", " " ],              
               ["Max.Temp. Innen", "" ],
               ["Gemessen am", "" ], 
               ["Min.Temp. Innen", "" ],
               ["Gemessen am", "" ], 
               ["Max.Feucht. Innen", "" ],
               ["Gemessen am", "" ], 
               ["Min.Feucht. Innen", "" ],
               ["Gemessen am", "" ], 
               ["Batterie Innen", ""],  
                ["Sensorstatus", ""],  
                ["Dauer ms", ""],                          

                ]

status_wetter_aussen = [
               ["Temperatur Aussen", "" ],
               ["Feuchtigkeit Aussen","" ],
               ["Messung am", "" ],              
               ["Max.Temp. Aussen", "" ],
               ["Gemessen am", "" ], 
               ["Min.Temp. Aussen", "" ],
               ["Gemessen am", "" ], 
               ["Max.Feucht. Aussen", "" ],
               ["Gemessen am", "" ], 
               ["Min.Feucht. Aussen", "" ],
               ["Gemessen am", "" ], 
               ["Batterie Aussen", ""],            
                ["Sensorstatus", ""],  
                ["Dauer ms", ""],                          

                ]

#-                
#-------------------------------------


