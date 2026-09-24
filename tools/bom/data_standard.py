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
("MC-BAS-001","Structure","Basamento lavorato","1",1,"Custom Al 6061 nervato, ottimizzato","Nervature ottimizzate (D008), sedi guide Y lavorate; lunghezza ~corsa Y + tavola",200,3.5,"M","design","TO DESIGN"),
("MC-GAN-001","Structure","Trave gantry","1",1,"Custom box Al ~80×100","Ponte fisso (D006), sezione scatolata",130,2.5,"M","design","TO DESIGN"),
("MC-GAN-002","Structure","Spalle gantry","2",2,"Custom Al 5083 15 mm alleggerito","Spinate al basamento; sede rialzi (D007)",45,1.0,"M","design","TO DESIGN"),
("MC-Z-001","Structure","Piastra asse Z","1",1,"Custom Al 5083 12–15 mm","Guide Z + ToolDock master",60,0.6,"M","design","TO DESIGN"),
("MC-TBL-001","Workholding","Tavola Y / tooling plate","1",1,"Al tooling plate 8 mm con tasche","Tavola mobile Y (D006), tasche sul retro (D008), 450×350 utile; reference pattern comune alle tre basi",100,2.5,"M","design","TO DESIGN"),
("MC-HW-001","Structure","Fasteners + dowel pins","1 set",1,"ISO high-strength","Viteria, spine rettificate, inserti",40,0.6,"M","source","TO SOURCE"),
]),
("B · Cinematica XYZ",[
("MC-LIN-151","XY","Guide lineari MGN15","4 rails",4,"HIWIN MGN15 class","2 rail Y nel basamento + 2 rail X sulla trave, ~600 mm (D008)",30,0.6,"M","source","TO SOURCE"),
("MC-LIN-152","XY","Pattini MGN15H","8",8,"HIWIN MGN15H class","2 pattini per rail, versione lunga; preload TBC",12,0.15,"M","source","TO SOURCE"),
("MC-LIN-153","Z","Guide lineari HGR15","2 rails",2,"HIWIN HGR15 class","~250 mm, corsa Z 120–140 mm",20,0.36,"M","source","TO SOURCE"),
("MC-LIN-154","Z","Pattini HGH15CA","4",4,"HIWIN HGH15CA class","4 pattini complessivi",15,0.18,"M","source","TO SOURCE"),
("MC-BS-1605X","X","Ball screw X","1",1,"SFU1605 C7","~600 mm; precarico/errore passo da qualificare",55,1.3,"M","validate","TO VALIDATE"),
("MC-BS-1605Y","Y","Ball screw Y","1",1,"SFU1605 C7","Vite singola centrale sotto la tavola (D006), ~550 mm",55,1.2,"M","validate","TO VALIDATE"),
("MC-BS-1204Z","Z","Ball screw Z","1",1,"SFU1204 C7","Vite compatta per asse Z",45,0.45,"M","validate","TO VALIDATE"),
("MC-BKBF-001","XYZ","Supporti BK12/BF12","3 set",3,"BK/BF matched class","Supporti cuscinetto per le tre viti",22,0.5,"M","source","TO SOURCE"),
("MC-CPL-001","XYZ","Giunti motore-vite","3",3,"Zero/low backlash bellows class","Da evitare giunti elicoidali economici",15,0.1,"M","source","TO SOURCE"),
("MC-MOT-001","XYZ","Motori NEMA23 closed-loop ~2 Nm","3",3,"StepperOnline 2 Nm class","Motore + encoder sulla macchina",40,1.2,"M","design","CANDIDATE"),
("MC-DRV-001","XYZ","Driver closed-loop","3",3,"CL57T class, ~48 V","Nel quadro esterno",20,0.3,"C","design","CANDIDATE"),
]),
("C · Spindle base",[
("MC-SP-001","Spindle","Spindle base 0.5–0.8 kW","1",1,"ER11, air-cooled class","~24k rpm (D008); testa completa entro il carico ToolDock di 4 kg",110,1.5,"M","design","TO QUALIFY"),
("MC-SP-002","Spindle","VFD","1",1,"0.8 kW class","RS485/analog; nel quadro esterno",100,1.0,"C","source","TO SOURCE"),
("MC-SP-003","Spindle","Spindle mount","1",1,"Custom machined clamp","Receiver-compatible con ToolDock",35,0.4,"M","design","TO DESIGN"),
("MC-SP-005","Tooling","ER collet starter set","1",1,"Precision collets class","Starter tooling only",25,0.2,"M","source","TO SOURCE"),
]),
("D · ToolDock (identico sulle tre basi)",[
("MC-TD-001","ToolDock","Master kinematic plate","1",1,"Custom 3-point kinematic interface","Montata sul carrello Z",150,0.6,"M","critical","CRITICAL DESIGN"),
("MC-TD-002","ToolDock","Base spindle receiver","1",1,"Custom receiver plate","Receiver dedicata al modulo spindle base",80,0.3,"M","design","TO DESIGN"),
("MC-TD-003","ToolDock","Automatic clamp","1",1,"Clamp a molla ≥ 1500 N, pull-stud (ICD v1)","Normalmente chiuso; sgancio passivo dal dock",100,0.4,"M","critical","CRITICAL DESIGN"),
("MC-TD-004","ToolDock","Hybrid connector set","1",1,"Power + signal + ID","Quick-connect; pneumatica/fluidi predisposti",120,0.3,"M","critical","CRITICAL DESIGN"),
("MC-TD-005","ToolDock","Module ID","1",1,"EEPROM / coded ID","Identificazione automatica del modulo",30,0.02,"M","design","TO DESIGN"),
]),
("E · Controllo (quadro esterno)",[
("MC-CTRL-001","Control","Motion controller","1",1,"Mesa 7i96S","Ethernet LinuxCNC motion/I-O baseline, comune alle tre basi",160,0.2,"C","validate","I/O REVIEW"),
("MC-CTRL-003","Control","Espansione I/O","1",1,"Scheda Mesa su porta di espansione 7i96S (modello da confermare)","≥ +16 ingressi / +8 uscite 24 V: home, probe, setter, conferme ToolDock, sensori testa, interlock (ICD v1)",90,0.2,"C","validate","I/O REVIEW"),
("MC-CTRL-002","Compute","Fanless mini PC","1",1,"x86 LinuxCNC compatible","Ethernet dedicata alla Mesa",120,0.8,"C","source","TO SOURCE"),
("MC-PWR-001","Power","48 V PSU","1",1,"Mean Well LRS-350-48","Motion supply",60,0.9,"C","source","TO SOURCE"),
("MC-PWR-002","Power","24 V PSU","1",1,"Mean Well HDR-60-24","I/O, sensori, relè, logica ToolDock",35,0.3,"C","source","TO SOURCE"),
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
("MC-RS-001","Clearance","Rialzi spalle spinati","1 set",1,"Custom Al blocks +75 mm","Clearance manuale riferita da spine (D007); accessorio, non montato di serie (D008)",60,1.4,"A","design","TO DESIGN"),
("MC-TD-006","ToolDock","Dock rail","1",1,"2-position rail","Parcheggio moduli; arriva con il primo kit ToolDock (D008); include la camma di sgancio del clamp (ICD v1)",80,0.8,"A","design","TO DESIGN"),
]),
]
