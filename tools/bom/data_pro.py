"""Dati BOM Base Pro → bom/base-pro.html.

Ogni riga: (id, gruppo, componente, q.tà etichetta, q.tà numerica, candidate, specifica,
€/cad, kg/cad, dove, classe stato, stato).
dove: "M" = sulla macchina, "C" = quadro/unità esterne, "A" = accessorio (escluso dai totali).
Dopo una modifica: python3 tools/bom/build.py
"""
PAGE = "bom/base-pro.html"
EXTERNAL_LABEL = "esterno"

G=[
("A · Struttura e riferimenti",[
("MP-BAS-001","Structure","Basamento lavorato","1",1,"Scala in tubi Al 80×60 sp. 4, senza fondo, saldata e lavorata","Longheroni, traversa BF, traversa BK Y e traversa di coda; 4 sbalzi 80×60 sotto le flange ICD §5 dei montanti del lift, niente traversa anteriore (CAD v2, D037)",250,8.6,"M","design","CAD v1"),
("MP-GAN-001","Structure","Trave gantry","1",1,"Scatolato Al 100×170, faccia guide 8, pareti 4, testate 5","Ponte fisso (D006), canale vite X, staffe del Gantry Lift sul retro (CAD v2, D037)",160,5.78,"M","design","CAD v1"),
("MP-GAN-002","Structure","Spalle gantry","2",2,"Custom Al 12 mm finestrato + traversa superiore 12 × 30","Montanti del Gantry Lift dietro la trave, 4 finestre ai lati della guida, flangia ICD §5 12 mm scaricata; portano guide, viti, cinghia e motore G (CAD v2, D037)",60,2.3,"M","design","CAD v1"),
("MP-Z-001","Structure","Piastra asse Z","1",1,"Custom Al 5083 12 mm, ali 10","Guide Z + ToolDock master (CAD v2, D037)",80,1.14,"M","design","CAD v1"),
("MP-XC-001","Structure","Carrello X","1",1,"Al 12 mm, piastra + torre + ali 10","Porta pattini X, guide Z, vite, supporti e motore Z (CAD v2, D037)",120,4.39,"M","design","CAD v1"),
("MP-BRK-001","Structure","Staffe chiocciole, motori e supporti","1 set",1,"Custom Al, 7 pezzi","Staffe chiocciola X e Y, piastrina chiocciola Z, staffa motore Z, spessori BK/BF X, piastre ponte BK/BF Z (CAD di dettaglio v1, D035)",45,0.88,"M","design","CAD v1"),
("MP-TBL-001","Workholding","Tavola Y / tooling plate","1",1,"Al tooling plate 12 mm","Tavola mobile Y (D006), 450×350 utile; spessore pieno, inserti M6 per usura (D018)",120,5.01,"M","design","CAD v1"),
("MP-HW-001","Structure","Fasteners + dowel pins","1 set",1,"ISO high-strength","Viteria, spine rettificate, rondelle, inserti",50,1.0,"M","source","TO SOURCE"),
("MC-TBL-002","Workholding","Inserti M6 + boccole R1/R2","1 set",1,"63 inserti filettati M6 in acciaio + 2 boccole Ø8 H7","Filetto utile 9 mm nei boss; R1 (50, 50) tonda, R2 (400, 50) asola (ICD v4, D018)",25,0.08,"M","source","TO SOURCE"),
]),
("B · Cinematica XYZ",[
("MP-LIN-201","XY","Guide lineari HGR20","4 rails",4,"HIWIN HGR20 class","2 rail Y nel basamento + 2 rail X sulla trave, 650 mm (D019)",60,1.44,"M","source","TO SOURCE"),
("MP-LIN-202","XY","Pattini HGH20CA","8",8,"HIWIN HGH20CA class","2 pattini per rail; preload TBC",20,0.3,"M","source","TO SOURCE"),
("MP-LIN-151","Z","Guide lineari HGR15","2 rails",2,"HIWIN HGR15 class","320 mm (D019), corsa Z 120–140 mm",32,0.46,"M","source","TO SOURCE"),
("MP-LIN-152","Z","Pattini HGH15CA","4",4,"HIWIN HGH15CA class","4 pattini complessivi",15,0.18,"M","source","TO SOURCE"),
("MP-BS-1605X","X","Ball screw X","1",1,"SFU1605 C7 precaricata","590 mm totali (D019); precarico/errore passo da qualificare. Massa dal CAD: vite piena Ø16 + chiocciola (limite superiore)",55,1.12,"M","validate","TO VALIDATE"),
("MP-BS-1605Y","Y","Ball screw Y","1",1,"SFU1605 C7 precaricata","Vite singola centrale sotto la tavola (D006), 490 mm totali (D019). Massa dal CAD (limite superiore)",55,0.96,"M","validate","TO VALIDATE"),
("MP-BS-1204Z","Z","Ball screw Z","1",1,"SFU1204 C7","260 mm totali (D019). Massa dal CAD (limite superiore)",45,0.34,"M","validate","TO VALIDATE"),
("MP-BKBF-001","XYZ","Supporti BK/BF precision","3 set",3,"BK/BF matched class","Supporti cuscinetto per le tre viti",25,0.6,"M","source","TO SOURCE"),
("MP-CPL-001","XYZ","Giunti motore-vite","3",3,"Zero/low backlash bellows class","Da evitare giunti elicoidali economici",15,0.12,"M","source","TO SOURCE"),
("MP-MOT-001","XYZ","Motori NEMA23 closed-loop 3 Nm","3",3,"StepperOnline 3 Nm class","Motore + encoder sulla macchina",43,1.5,"M","design","CANDIDATE"),
("MP-DRV-001","XYZ","Driver closed-loop","3",3,"CL57T class, ~48 V","Nel quadro esterno",22,0.35,"C","design","CANDIDATE"),
]),
("C · Gantry Lift motorizzato (solo Pro)",[
("MP-GL-LIN1","Gantry Lift","Guide verticali HGR15","2 rails",2,"HIWIN HGR15 class","Una guida per montante, 350 mm (verificata D019)",30,0.51,"M","design","TO DESIGN"),
("MP-GL-LIN2","Gantry Lift","Pattini HGH15","4",4,"HIWIN HGH15 class","2 pattini per lato",15,0.18,"M","design","TO DESIGN"),
("MP-GL-BS","Gantry Lift","Viti sollevamento","2",2,"SFU1605 class","Sollevamento sincronizzato, non asse di taglio; 350 mm totali. Massa dal CAD (limite superiore)",40,0.74,"M","design","TO DESIGN"),
("MP-GL-BK","Gantry Lift","Supporti BK/BF lift","2 set",2,"BK/BF12 class","Supporto viti lift",20,0.5,"M","source","TO SOURCE"),
("MP-GL-MOT","Gantry Lift","Motore G","1",1,"NEMA23 closed-loop class","Asse di setup, non richiede precisione metrologica",43,1.5,"M","design","CANDIDATE"),
("MP-GL-DRV","Gantry Lift","Driver G","1",1,"CL57T class","Nel quadro esterno",22,0.35,"C","design","CANDIDATE"),
("MP-GL-SYNC","Gantry Lift","Sincronizzazione","1 set",1,"HTD belt + pulleys + shaft","Sincronizza le due viti verticali; massa dal CAD (pulegge piene, cinghia, giunto)",50,0.88,"M","design","TO DESIGN"),
("MP-GL-LOCK","Gantry Lift","Locking + references","1 set",1,"Custom clamp / wedge / dowel","Scarica il lift durante la lavorazione; staffe trave a C (D037)",100,1.96,"M","critical","CRITICAL DESIGN"),
]),
("D · Spindle base",[
("MP-SP-001","Spindle","Spindle 1.5 kW ER16","1",1,"Water-cooled 80 mm class","~24k rpm; runout da bench-test; testa entro il carico ToolDock di 7 kg",160,4.5,"M","design","TO QUALIFY"),
("MP-SP-002","Spindle","VFD vector","1",1,"1.5 kW class","RS485/analog; nel quadro esterno",120,1.5,"C","source","TO SOURCE"),
("MC-SP-006","Spindle","Contattore uscita spindle","1",1,"Contattore AC-3 con contatto ausiliario","Apre P1–P3 a valle di VFD/driver prima dello sgancio della testa (ICD v4, D020)",25,0.2,"C","design","TO DESIGN"),
("MP-SP-003","Spindle","Spindle mount","1",1,"Custom machined clamp","Receiver-compatible con ToolDock",40,1.07,"M","design","CAD v1"),
("MP-SP-004","Cooling","Cooling loop","1",1,"Pump + radiator + reservoir","Unità esterna a circuito chiuso",60,2.5,"C","source","TO SOURCE"),
("MP-SP-005","Tooling","ER16 collet starter set","1",1,"Precision collets class","Starter tooling only",30,0.3,"M","source","TO SOURCE"),
]),
("E · ToolDock (identico sulle tre basi)",[
("MC-TD-001","ToolDock","Master kinematic plate","1",1,"Stessa parte della Standard","Montata sul carrello Z",150,0.96,"M","critical","CRITICAL DESIGN"),
("MC-TD-002","ToolDock","Base spindle receiver","1",1,"Receiver ICD comune, 110 × 110 per il mount Ø80","Stesso accoppiamento, pull-stud e porte della Standard; più largo (110, limite ICD) per le viti del mount dello spindle Ø80 (CAD v1)",80,0.45,"M","design","CAD v1"),
("MC-TD-003","ToolDock","Automatic clamp","1",1,"Pull-stud comune (ICD v4)","Pacco molle ≥ 3,8 kN (classe P), sgancio passivo con camma 3:1 (D016)",100,0.4,"M","critical","CRITICAL DESIGN"),
("MC-TD-004","ToolDock","Hybrid connector set","1",1,"Stessa parte della Standard","Power + signal + ID",120,0.3,"M","critical","CRITICAL DESIGN"),
("MC-TD-005","ToolDock","Module ID","1",1,"Stessa parte della Standard","Identificazione automatica",30,0.02,"M","design","TO DESIGN"),
("MC-TD-007","ToolDock","Connettore dati","1",1,"Blind-mate a contatti a molla, schermato","Ethernet 1000BASE-T (4 coppie) + CAN FD + encoder RS-422 differenziale (ICD v4, D020)",60,0.05,"M","design","TO SOURCE"),
]),
("F · Controllo (quadro esterno)",[
("MC-CTRL-001","Control","Motion controller","1",1,"Mesa 7i96S","Comune alle tre basi; I/O da verificare con il lift",160,0.2,"C","validate","I/O REVIEW"),
("MC-CTRL-003","Control","Espansione I/O","1",1,"Scheda Mesa su porta di espansione 7i96S (modello da confermare)","≥ +16 ingressi / +8 uscite 24 V: home, probe, setter, conferme ToolDock, sensori testa, interlock (ICD v4)",90,0.2,"C","validate","I/O REVIEW"),
("MC-CTRL-004","Control","Interfaccia CAN FD","1",1,"Adattatore USB–CAN FD","Bus moduli ToolDock (ICD v4, D020)",40,0.05,"C","source","TO SOURCE"),
("MC-CTRL-002","Compute","Fanless mini PC","1",1,"x86 LinuxCNC, 2 porte Ethernet","Porta 1 dedicata alla Mesa, porta 2 per il bus dati ToolDock (D017)",150,0.8,"C","source","TO SOURCE"),
("MP-PWR-001","Power","48 V PSU","1",1,"Mean Well LRS-600-48","Motion supply, 4 assi",70,1.3,"C","source","TO SOURCE"),
("MC-PWR-002","Power","24 V PSU","1",1,"Mean Well HDR-100-24","~92 W (24 V × 3,83 A): I/O, sensori, logica ToolDock; 40 W garantiti ai moduli (ICD v4, D022)",45,0.35,"C","source","TO SOURCE"),
("MP-PWR-003","Power","48 V MODULE AUX","1",1,"Mean Well LRS-350-48","Linea 48 V dedicata ai moduli ToolDock, separata dal motion (ICD v4, D020)",60,0.8,"C","source","TO SOURCE"),
("MC-SAFE-001","Safety","E-stop + contactor chain","1 set",1,"Industrial safety hardware","Arresto energia motion/process",80,0.5,"C","design","TO DESIGN"),
("MP-IO-001","I/O","Relays / terminal blocks / protection","1 set",1,"DIN rail industrial","Fusibili, interruttori, relè, morsetti",90,0.8,"C","source","TO SOURCE"),
("MP-EL-BOX","Electrical","Quadro elettrico esterno","1",1,"DIN cabinet","Controller, PSU, driver, VFD separato",80,3.0,"C","design","TO DESIGN"),
]),
("G · Cablaggio, sensori e metrologia",[
("MP-CAB-001","Electrical","Cavi schermati macchina–quadro","1 set",1,"Motion + spindle + I/O","EMC-aware routing, 4 assi",100,1.2,"M","source","TO SOURCE"),
("MP-CHAIN-001","Mechanical","Drag chains","1 set",1,"Low-profile cable chain","X/Z sul ponte + escursione lift",50,0.6,"M","source","TO SOURCE"),
("MC-SNS-001","Sensing","Home/limit sensors","6",6,"Inductive industrial class","XYZ + gantry lift reference",8,0.05,"M","source","TO SOURCE"),
("MC-PROBE-001","Metrology","XYZ touch probe","1",1,"Wired probe class","Work offset / edge finding",45,0.2,"M","design","TO QUALIFY"),
("MC-TOOL-001","Metrology","Tool length setter","1",1,"Wired setter class","Tool length reference",55,0.3,"M","design","TO QUALIFY"),
]),
("H · Accessori (non inclusi nei totali)",[
("MP-ENC-001","Enclosure","Cabina opzionale Pro","1",1,"Telaio indipendente rinforzato + pannelli PC 5 mm + porta con interlock","Più alta per il Gantry Lift e lo spindle ad acqua; agganciata al basamento, mai al ponte; LED, aspirazione Ø100, vasca trucioli e MQL; prezzo TARGET a lotto 50 (D025)",380,18.0,"A","design","TO DESIGN"),
("MC-TD-006","ToolDock","Magazine indicizzato","1",1,"2–4 posti, indicizzazione motorizzata","Sul ponte; presenta la testa in un\'unica posizione di docking; forcelle con sensore di cattura, camma di sgancio 3:1 (D016, D021)",200,2.0,"A","design","TO DESIGN"),
]),
]
