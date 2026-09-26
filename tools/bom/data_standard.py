"""Dati BOM Base Standard → bom/base.html.

Ogni riga: (id, gruppo, componente, q.tà etichetta, q.tà numerica, candidate, specifica,
€/cad, kg/cad, dove, classe stato, stato).
dove: "M" = sulla macchina, "C" = quadro/unità esterne, "A" = accessorio (escluso dai totali).
Dopo una modifica: python3 tools/bom/build.py
"""
PAGE = "bom/base.html"
EXTERNAL_LABEL = "quadro"

G=[
("A · Struttura e riferimenti",[
("MC-BAS-001","Structure","Telaio a scala","1",1,"2 longheroni Y + 4 traverse, tubi Al 40×60 / 120×60 sp. 3 (D034), saldato e lavorato","Telaio di precisione a scala (D027): longheroni sotto le guide Y con sedi lavorate, traverse fronte / BF / posteriore (porta le spalle) / motore; traversa posteriore estesa sotto il BK Y; massa dal CAD di dettaglio v1",180,5.98,"M","design","CAD v1"),
("MC-GAN-001","Structure","Trave gantry","1",1,"Custom box Al 80×140, pareti 4 / faccia guide 6 (D034), canale vite","Ponte fisso (D006), interasse guide X 110 mm (D015), centro guide a 246 mm (D027); massa dal CAD di dettaglio v1, da ridisegnare",150,4.66,"M","design","CAD v1"),
("MC-GAN-002","Structure","Spalle gantry","2",2,"Custom Al, scatolate 40 × 120 sp. 4, flangia ICD 12 (D034)","Alte 176 mm sulla traversa posteriore (D027), scatolate (D029, D030); sede rialzi (D007); massa dal CAD di dettaglio v1",60,0.98,"M","design","CAD v1"),
("MC-Z-001","Structure","Slitta Z","1",1,"Custom Al 12 mm, 150 × 160 a canale con ali anteriori 10 × 35","Porta i 4 pattini HGH15CA Z e la master ToolDock (D027); ali sopra il piano del coupling (D030); massa dal CAD di dettaglio v1",70,0.9,"M","design","CAD v1"),
("MC-TBL-001","Workholding","Tavola Y / tooling plate","1",1,"Al tooling plate 10 mm, tasche e boss pieni","Tavola mobile Y (D006), 450×350 utile; pelle 6 mm, boss Ø16 × 10 mm attorno ai fori M6 e ai riferimenti (D018); massa confermata dal mule v1",100,2.96,"M","design","CAD v1"),
("MC-XC-001","Structure","Carrello X","1",1,"Custom Al 15 mm, 170 × 530 + torre, a canale con ali anteriori 10 × 45","Porta pattini X, guide Z, vite, supporti e motore Z (D027); ali fuori dalla slitta e dal corridoio di docking (D030); massa dal CAD di dettaglio v1",110,3.27,"M","design","CAD v1"),
("MC-BRK-001","Structure","Staffe chiocciole, motori e supporti","1 set",1,"Custom Al, 7 pezzi","Staffe chiocciola X e Y, piastrina chiocciola Z 16 mm (D031), staffa motore Z, spessori BK/BF X, 2 piastre ponte BK/BF Z (CAD di dettaglio v1); piastre motore X e Y saldate su trave e telaio",45,0.73,"M","design","CAD v1"),
("MC-HW-001","Structure","Fasteners + dowel pins","1 set",1,"ISO high-strength","~311 elementi dalla tabella del CAD di dettaglio (base/cad-parts.html): viti ISO 4762, spine ISO 8734, 63 inserti M6, O-ring, molle a tazza",40,0.6,"M","source","TO SOURCE"),
("MC-TBL-002","Workholding","Inserti M6 + boccole R1/R2","1 set",1,"63 inserti filettati M6 in acciaio + 2 boccole Ø8 H7","Filetto utile 9 mm nei boss; R1 (50, 50) tonda, R2 (400, 50) asola (ICD v4, D018)",25,0.08,"M","source","TO SOURCE"),
]),
("B · Cinematica XYZ",[
("MC-LIN-151","X","Guide lineari HGR15","2 rails",2,"HIWIN HGR15 class","Sulla trave, 640 mm (D019), interasse ≥ 110 mm (D015)",37,0.93,"M","source","TO SOURCE"),
("MC-LIN-152","X","Pattini HGH15CA","4",4,"HIWIN HGH15CA class","2 pattini per rail; precarico ZA, 365 N/µm (D015, D022)",15,0.18,"M","source","TO SOURCE"),
("MC-LIN-155","Y","Guide lineari MGN15","2 rails",2,"HIWIN MGN15 class","Nel basamento sotto la tavola, 630 mm (D019), interasse ~300 mm (D008, D015)",32,0.63,"M","source","TO SOURCE"),
("MC-LIN-156","Y","Pattini MGN15H","4",4,"HIWIN MGN15H class","2 pattini per rail, versione lunga, precarico Z1 (202 N/µm, D022); 0,09 kg da scheda HIWIN",12,0.09,"M","source","TO SOURCE"),
("MC-LIN-153","Z","Guide lineari HGR15","2 rails",2,"HIWIN HGR15 class","310 mm (D019), corsa Z 120–140 mm",25,0.45,"M","source","TO SOURCE"),
("MC-LIN-154","Z","Pattini HGH15CA","4",4,"HIWIN HGH15CA class","4 pattini complessivi",15,0.18,"M","source","TO SOURCE"),
("MC-BS-1605X","X","Ball screw X","1",1,"SFU1605 C7","590 mm totali, estremità BK/BF comprese (D019); precarico/errore passo da qualificare",55,1.28,"M","validate","TO VALIDATE"),
("MC-BS-1605Y","Y","Ball screw Y","1",1,"SFU1605 C7","Vite singola centrale sotto la tavola (D006), 490 mm totali (D019)",55,1.12,"M","validate","TO VALIDATE"),
("MC-BS-1204Z","Z","Ball screw Z","1",1,"SFU1204 C7","260 mm totali (D019)",45,0.43,"M","validate","TO VALIDATE"),
("MC-BKBF-001","XYZ","Supporti BK12/BF12","3 set",3,"BK/BF matched class","Supporti cuscinetto per le tre viti",22,0.5,"M","source","TO SOURCE"),
("MC-CPL-001","XYZ","Giunti motore-vite","3",3,"Zero/low backlash bellows class","Da evitare giunti elicoidali economici",15,0.1,"M","source","TO SOURCE"),
("MC-MOT-001","XYZ","Motori NEMA23 closed-loop ~2 Nm","3",3,"StepperOnline 2 Nm class","Motore + encoder sulla macchina",40,1.2,"M","design","CANDIDATE"),
("MC-DRV-001","XYZ","Driver closed-loop","3",3,"CL57T class, ~48 V","Nel quadro esterno",20,0.3,"C","design","CANDIDATE"),
]),
("C · Spindle base",[
("MC-SP-001","Spindle","Spindle HF Ø45 · 650 W S1","1",1,"Riferimento SycoTec 5045 AC-ER11 · 2002 5400; OEM equivalente da qualificare","Ø45 × 180 mm, 1,6 kg, 650 W S1 / 1,28 kW, 6.000–60.000 rpm, 180 V 3,5 A S1, ER11 fino a Ø8, runout ≤ 1,5 µm; raffreddamento dal mount e aria di tenuta 30 l/min (D030). Prezzo = TARGET OEM, non SycoTec",300,1.6,"M","design","TO QUALIFY"),
("MC-SP-002","Spindle","Inverter HF","1",1,"Inverter per spindle asincrono, fino a 1 kHz, 180 V 3~","Riferimento e@syDrive 4638 / Control Techniques HS30 (catalogo SycoTec); prezzo TARGET OEM; nel quadro esterno",250,1.2,"C","source","TO SOURCE"),
("MC-SP-006","Spindle","Contattore uscita spindle","1",1,"Contattore AC-3 con contatto ausiliario","Apre P1–P3 a valle di VFD/driver prima dello sgancio della testa (ICD v4, D020)",25,0.2,"C","design","TO DESIGN"),
("MC-SP-007","Spindle","Aria di tenuta spindle","1 set",1,"Filtro-regolatore, elettrovalvola 24 V, flussostato, raccordi Ø6","30 ± 5 l/min sul passaggio Ø6 del ToolDock (ICD v4, D030); aria da rete o compressore esterno, non inclusi; TARGET",45,0.4,"C","design","TO DESIGN"),
("MC-SP-008","Spindle","Circuito camicia di raffreddamento","1 set",1,"Pompa 24 V, radiatore con ventola, serbatoio, tubi","Mandata e ritorno sulle 2 porte Ø4 del ToolDock (ICD v4, D030); TARGET",60,0.9,"C","design","TO DESIGN"),
("MC-SP-003","Spindle","Mount spindle a tazza con camicia","1",1,"Custom Al 60 × 60, collare sul Ø45 h6, camicia di raffreddamento","Dal receiver al collare: tazza chiusa con finestra per il connettore M23 a 90° (D030); massa dal CAD di dettaglio v1",60,0.47,"M","design","CAD v1"),
("MC-SP-005","Tooling","ER collet starter set","1",1,"Precision collets class","Starter tooling only",25,0.2,"M","source","TO SOURCE"),
]),
("D · ToolDock (identico sulle tre basi)",[
("MC-TD-001","ToolDock","Master kinematic plate","1",1,"Custom 3-point kinematic interface, scatolata 120 × 40 sp. 8 con sella a U","Sotto la slitta Z, scatolata (D029, D030); sella a U incollata/bullonata alle ali della slitta (D031, mule v3); massa dal CAD di dettaglio v1",150,0.95,"M","critical","CAD v1"),
("MC-TD-002","ToolDock","Base spindle receiver","1",1,"Custom receiver plate","Receiver della testa spindle Standard, 96 × 96 × 15; massa dal CAD di dettaglio v1",80,0.33,"M","design","CAD v1"),
("MC-TD-003","ToolDock","Automatic clamp","1",1,"Pull-stud comune (ICD v4)","Pacco molle ≥ 1,6 kN (classe S), sgancio passivo con camma 3:1 (D016)",100,0.4,"M","critical","CAD v1"),
("MC-TD-004","ToolDock","Hybrid connector set","1",1,"Power + signal + ID","Quick-connect; pneumatica/fluidi predisposti",120,0.3,"M","critical","CRITICAL DESIGN"),
("MC-TD-005","ToolDock","Module ID","1",1,"EEPROM / coded ID","Identificazione automatica del modulo",30,0.02,"M","design","TO DESIGN"),
("MC-TD-007","ToolDock","Connettore dati","1",1,"Blind-mate a contatti a molla, schermato","Ethernet 1000BASE-T (4 coppie) + CAN FD + encoder RS-422 differenziale (ICD v4, D020)",60,0.05,"M","design","TO SOURCE"),
]),
("E · Controllo (quadro esterno)",[
("MC-CTRL-001","Control","Motion controller","1",1,"Mesa 7i96S","Ethernet LinuxCNC motion/I-O baseline, comune alle tre basi",160,0.2,"C","validate","I/O REVIEW"),
("MC-CTRL-003","Control","Espansione I/O","1",1,"Scheda Mesa su porta di espansione 7i96S (modello da confermare)","≥ +16 ingressi / +8 uscite 24 V: home, probe, setter, conferme ToolDock, sensori testa, interlock (ICD v4)",90,0.2,"C","validate","I/O REVIEW"),
("MC-CTRL-004","Control","Interfaccia CAN FD","1",1,"Adattatore USB–CAN FD","Bus moduli ToolDock (ICD v4, D020)",40,0.05,"C","source","TO SOURCE"),
("MC-CTRL-002","Compute","Fanless mini PC","1",1,"x86 LinuxCNC, 2 porte Ethernet","Porta 1 dedicata alla Mesa, porta 2 per il bus dati ToolDock (D017)",150,0.8,"C","source","TO SOURCE"),
("MC-PWR-001","Power","48 V PSU","1",1,"Mean Well LRS-350-48","Motion supply",60,0.9,"C","source","TO SOURCE"),
("MC-PWR-002","Power","24 V PSU","1",1,"Mean Well HDR-100-24","~92 W (24 V × 3,83 A): I/O, sensori, logica ToolDock; 40 W garantiti ai moduli (ICD v4, D022)",45,0.35,"C","source","TO SOURCE"),
("MC-PWR-003","Power","48 V MODULE AUX","1",1,"Mean Well LRS-150-48","Linea 48 V dedicata ai moduli ToolDock, separata dal motion (ICD v4, D020)",40,0.6,"C","source","TO SOURCE"),
("MC-SAFE-001","Safety","E-stop + contactor chain","1 set",1,"Industrial safety hardware","Arresto energia motion/process secondo safety design finale",80,0.5,"C","design","TO DESIGN"),
("MC-IO-001","I/O","Relays / terminal blocks / protection","1 set",1,"DIN rail industrial","Fusibili, interruttori, relè, morsetti",80,0.7,"C","source","TO SOURCE"),
("MC-EL-BOX","Electrical","Quadro elettrico esterno","1",1,"DIN cabinet","Controller, PSU, driver, VFD; separato dalla macchina",80,2.5,"C","design","TO DESIGN"),
]),
("F · Cablaggio, sensori e metrologia",[
("MC-CAB-001","Electrical","Cavi schermati macchina–quadro","1 set",1,"Motion + spindle + I/O","EMC-aware routing",90,1.0,"M","source","TO SOURCE"),
("MC-CHAIN-001","Mechanical","Drag chains","1 set",1,"Low-profile cable chain","X/Z sul ponte; Y solo se il cablaggio tavola lo richiede",45,0.5,"M","source","TO SOURCE"),
("MC-SNS-001","Sensing","Home/limit sensors","4",4,"Inductive industrial class","XYZ home + limite",8,0.05,"M","source","TO SOURCE"),
("MC-PROBE-001","Metrology","XYZ touch probe","1",1,"Wired probe class","Work offset / edge finding",45,0.2,"M","design","TO QUALIFY"),
("MC-TOOL-001","Metrology","Tool length setter","1",1,"Wired setter class","Tool length reference",55,0.3,"M","design","TO QUALIFY"),
]),
("G · Accessori (non inclusi nei totali)",[
("MC-ENC-001","Enclosure","Cabina opzionale","1",1,"Telaio indipendente + pannelli PC 4 mm + porta con interlock","Stessa cabina della Light Core; agganciata al basamento, mai al ponte; LED, attacco aspirazione Ø100, vasca trucioli, fonoassorbente; variante laser-ready da qualificare per ogni modulo laser (lunghezza d'onda, protezione ottica, interlock, verifica delle fughe); prezzo TARGET a lotto 50 (D025)",280,40.8,"A","design","TO DESIGN"),
("MC-RS-001","Clearance","Rialzi spalle spinati","1 set",1,"Custom Al blocks +75 mm","Clearance manuale riferita da spine (D007); accessorio, non montato di serie (D008)",60,2.52,"A","design","CAD v1"),
("MC-TD-006","ToolDock","Magazine indicizzato","1",1,"2–4 posti, indicizzazione motorizzata","Sul ponte; presenta la testa in un\'unica posizione di docking; forcelle con sensore di cattura, camma di sgancio 3:1 (D016, D021)",200,2.0,"A","design","TO DESIGN"),
]),
]
