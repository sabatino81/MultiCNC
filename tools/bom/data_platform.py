"""Dati BOM Platform Pack (D026) → bom/platform-pack.html.

Upgrade montabile dal cliente che porta la Light Core al profilo elettrico Platform
della ICD v4 (cambio testa automatico, Mesa + LinuxCNC, closed-loop, bus dati).
Stesso formato di riga delle BOM delle basi. Prezzi: TARGET a lotto da 50 (D023).
Dopo una modifica: python3 tools/bom/build.py
"""
PAGE = "bom/platform-pack.html"
EXTERNAL_LABEL = "quadro"

G=[
("A · Closed-loop sugli assi",[
("PP-ENC-001","XYZ","Encoder a innesto","3",3,"Encoder magnetico ABZ differenziale 1000 linee","Si monta sul secondo albero dei NEMA17 encoder-ready della Light Core: i motori restano (D026). Da qualificare in coppia con il driver: prova prioritaria",12,0.05,"M","critical","TO QUALIFY · COPPIA"),
("PP-DRV-001","XYZ","Driver closed-loop","3",3,"CL42T class, ingresso encoder ABZ","Nel nuovo quadro; deve accettare davvero l'ABZ differenziale di un encoder esterno e chiudere l'anello su un motore non suo: da scegliere insieme all'encoder",15,0.2,"C","critical","TO QUALIFY · COPPIA"),
]),
("B · Controllo Mesa + LinuxCNC",[
("MC-CTRL-001","Control","Motion controller","1",1,"Mesa 7i96S","Stesso controller di Standard e Pro",140,0.2,"C","validate","I/O REVIEW"),
("MC-CTRL-003","Control","Espansione I/O","1",1,"Scheda Mesa su porta di espansione 7i96S (modello da confermare)","≥ +16 ingressi / +8 uscite 24 V (ICD v4, profilo Platform)",75,0.2,"C","validate","I/O REVIEW"),
("MC-CTRL-004","Control","Interfaccia CAN FD","1",1,"Adattatore USB–CAN FD","Bus moduli ToolDock",30,0.05,"C","source","TO SOURCE"),
("MC-CTRL-002","Compute","Fanless mini PC","1",1,"x86 LinuxCNC, 2 porte Ethernet","Opzionale se il cliente usa un proprio PC compatibile LinuxCNC (−€120)",120,0.8,"C","source","TO SOURCE"),
]),
("C · Alimentazione e sicurezza",[
("MC-PWR-002","Power","24 V PSU","1",1,"Mean Well HDR-100-24","~92 W: I/O, sensori, logica ToolDock; 40 W garantiti ai moduli (ICD v4)",35,0.35,"C","source","TO SOURCE"),
("MC-PWR-003","Power","48 V MODULE AUX","1",1,"Mean Well LRS-150-48","Linea 48 V moduli separata dal motion; il 48 V motion LRS-200-48 della Core resta",30,0.6,"C","source","TO SOURCE"),
("MC-SP-006","Spindle","Contattore uscita spindle","1",1,"Contattore AC-3 con contatto ausiliario","Apre P1–P3 a valle del driver BLDC prima dello sgancio automatico (D020); il driver BLDC della Core resta",18,0.2,"C","design","TO DESIGN"),
("PP-EL-BOX","Electrical","Quadro DIN + catena E-stop","1",1,"DIN cabinet, relè di sicurezza, morsetti","Sostituisce il quadro compatto Core; E-stop e interlock cabina (D025) sul relè di sicurezza",70,1.8,"C","design","TO DESIGN"),
]),
("D · ToolDock automatico",[
("MC-TD-003","ToolDock","Automatic clamp","1",1,"Pull-stud comune (ICD v4)","Pacco molle ≥ 0,5 kN (classe L), sgancio passivo con camma 3:1 (D016); si monta nelle sedi già lavorate della master Core",60,0.4,"M","critical","CRITICAL DESIGN"),
("MC-TD-004","ToolDock","Hybrid connector set","1",1,"Power + signal + ID, disegno MultiCNC","Sostituisce il connettore circolare manuale Core",60,0.3,"M","critical","CRITICAL DESIGN"),
("MC-TD-007","ToolDock","Connettore dati","1",1,"Blind-mate schermato, 18 contatti + schermo","Ethernet 1000BASE-T + CAN FD + encoder RS-422 (ICD v4, profilo Platform)",45,0.05,"M","design","TO SOURCE"),
]),
("E · Cablaggio e metrologia",[
("PP-CAB-001","Electrical","Cavi dati e ibrido macchina–quadro","1 set",1,"Cablaggi preassemblati schermati","Si affiancano ai cavi Core, che restano (motori con poli encoder già previsti)",35,0.5,"M","source","TO SOURCE"),
("MC-PROBE-001","Metrology","XYZ touch probe","1",1,"Wired probe class","Work offset / edge finding; incluso nel pacchetto",30,0.2,"M","design","TO QUALIFY"),
]),
("F · Accessori (non inclusi nei totali)",[
("MC-TD-006","ToolDock","Magazine indicizzato","1",1,"2–4 posti, indicizzazione motorizzata","Sul ponte; richiede il Platform Pack (D016, D021)",200,2.0,"A","design","TO DESIGN"),
]),
]
