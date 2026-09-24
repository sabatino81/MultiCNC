"""Dati BOM Base Light → bom/base-light.html.

Ogni riga: (id, gruppo, componente, q.tà etichetta, q.tà numerica, candidate, specifica,
€/cad, kg/cad, dove, classe stato, stato).
dove: "M" = sulla macchina, "C" = quadro/unità esterne, "A" = accessorio (escluso dai totali).
Dopo una modifica: python3 tools/bom/build.py
"""
PAGE = "bom/base-light.html"
EXTERNAL_LABEL = "quadro"

G=[
("A · Struttura e riferimenti",[
("ML-BAS-001","Structure","Telaio basamento","1",1,"Profilati Al 40×40 + piastre lavorate","Piastre con sedi guide Y lavorate su telaio a profilati; lunghezza ~corsa Y + tavola; piastre assottigliate (D010)",120,2.0,"M","design","TO DESIGN"),
("ML-GAN-001","Structure","Trave gantry","1",1,"Profilo Al 40×80 lavorato","Ponte fisso (D006), faccia guide X lavorata, pareti ridotte (D010)",70,1.1,"M","design","TO DESIGN"),
("ML-GAN-002","Structure","Spalle gantry","2",2,"Al 5083 8 mm alleggerito","Spinate al telaio; sede rialzi (D007)",30,0.5,"M","design","TO DESIGN"),
("ML-Z-001","Structure","Piastra asse Z","1",1,"Al 5083 8 mm","Guide Z + ToolDock master",40,0.3,"M","design","TO DESIGN"),
("ML-TBL-001","Workholding","Tavola Y / tooling plate","1",1,"Al 5 mm con tasche","Tavola mobile Y (D006), 450×350 utile (D010); reference pattern comune alle tre basi",80,1.4,"M","design","TO DESIGN"),
("ML-HW-001","Structure","Fasteners + dowel pins","1 set",1,"ISO","Viteria, spine, inserti",30,0.4,"M","source","TO SOURCE"),
]),
("B · Cinematica XYZ",[
("ML-LIN-151","XY","Guide lineari MGN12","4 rails",4,"HIWIN MGN12 class","2 rail Y + 2 rail X, ~600 mm (D010)",22,0.39,"M","source","TO SOURCE"),
("ML-LIN-152","XY","Pattini MGN12H","8",8,"HIWIN MGN12H class","2 pattini per rail, versione lunga",9,0.08,"M","source","TO SOURCE"),
("ML-LIN-153","Z","Guide lineari MGN12","2 rails",2,"HIWIN MGN12 class","~250 mm",14,0.16,"M","source","TO SOURCE"),
("ML-LIN-154","Z","Pattini MGN12H","4",4,"HIWIN MGN12H class","4 pattini complessivi",9,0.08,"M","source","TO SOURCE"),
("ML-BS-1204X","X","Ball screw X","1",1,"SFU1204 C7","~600 mm",40,0.75,"M","validate","TO VALIDATE"),
("ML-BS-1204Y","Y","Ball screw Y","1",1,"SFU1204 C7","Vite singola centrale sotto la tavola (D006), ~550 mm",40,0.7,"M","validate","TO VALIDATE"),
("ML-BS-1204Z","Z","Ball screw Z","1",1,"SFU1204 C7","Stessa vite Z della Standard",35,0.45,"M","validate","TO VALIDATE"),
("ML-BKBF-001","XYZ","Supporti BK10/BF10","3 set",3,"BK/BF class","Supporti per le tre viti",18,0.35,"M","source","TO SOURCE"),
("ML-CPL-001","XYZ","Giunti motore-vite","3",3,"Low backlash bellows class","Taglia NEMA17",12,0.07,"M","source","TO SOURCE"),
("ML-MOT-001","XYZ","Motori NEMA17 closed-loop","3",3,"NEMA17 ~0.6 Nm + encoder","Motore + encoder sulla macchina",35,0.55,"M","design","CANDIDATE"),
("ML-DRV-001","XYZ","Driver closed-loop","3",3,"CL42T class","Nel quadro esterno",18,0.2,"C","design","CANDIDATE"),
]),
("C · Spindle base",[
("ML-SP-001","Spindle","Spindle BLDC 300–500 W","1",1,"ER11, air-cooled","Testa completa entro il carico ToolDock di 2 kg",80,1.0,"M","design","TO QUALIFY"),
("ML-SP-002","Spindle","Driver BLDC","1",1,"0.5 kW class","Al posto del VFD; nel quadro esterno",50,0.5,"C","source","TO SOURCE"),
("ML-SP-003","Spindle","Spindle mount","1",1,"Custom machined clamp","Receiver-compatible con ToolDock",25,0.25,"M","design","TO DESIGN"),
("ML-SP-005","Tooling","ER11 collet starter set","1",1,"Precision collets class","Starter tooling only",20,0.15,"M","source","TO SOURCE"),
]),
("D · ToolDock (identico sulle tre basi)",[
("MC-TD-001","ToolDock","Master kinematic plate","1",1,"Stessa parte della Standard","Montata sul carrello Z",150,0.6,"M","critical","CRITICAL DESIGN"),
("MC-TD-002","ToolDock","Base spindle receiver","1",1,"Stessa parte della Standard","Receiver del modulo spindle base",80,0.3,"M","design","TO DESIGN"),
("MC-TD-003","ToolDock","Automatic clamp","1",1,"Stessa parte della Standard","Clamp a molla ≥ 1500 N, sgancio passivo dal dock (ICD v1)",100,0.4,"M","critical","CRITICAL DESIGN"),
("MC-TD-004","ToolDock","Hybrid connector set","1",1,"Stessa parte della Standard","Power + signal + ID",120,0.3,"M","critical","CRITICAL DESIGN"),
("MC-TD-005","ToolDock","Module ID","1",1,"Stessa parte della Standard","Identificazione automatica",30,0.02,"M","design","TO DESIGN"),
]),
("E · Controllo (quadro esterno)",[
("MC-CTRL-001","Control","Motion controller","1",1,"Mesa 7i96S","Comune alle tre basi",160,0.2,"C","validate","I/O REVIEW"),
("MC-CTRL-003","Control","Espansione I/O","1",1,"Scheda Mesa su porta di espansione 7i96S (modello da confermare)","≥ +16 ingressi / +8 uscite 24 V: home, probe, setter, conferme ToolDock, sensori testa, interlock (ICD v1)",90,0.2,"C","validate","I/O REVIEW"),
("MC-CTRL-002","Compute","Fanless mini PC","1",1,"x86 LinuxCNC compatible","Ethernet dedicata alla Mesa",120,0.8,"C","source","TO SOURCE"),
("ML-PWR-001","Power","48 V PSU","1",1,"Mean Well LRS-200-48","Motion supply NEMA17",45,0.6,"C","source","TO SOURCE"),
("MC-PWR-002","Power","24 V PSU","1",1,"Mean Well HDR-60-24","I/O, sensori, logica ToolDock",35,0.3,"C","source","TO SOURCE"),
("MC-SAFE-001","Safety","E-stop + contactor chain","1 set",1,"Industrial safety hardware","Arresto energia motion/process",70,0.5,"C","design","TO DESIGN"),
("ML-IO-001","I/O","Relays / terminals / protection","1 set",1,"DIN rail","Fusibili, relè, morsetti",60,0.5,"C","source","TO SOURCE"),
("ML-EL-BOX","Electrical","Quadro elettrico esterno compatto","1",1,"DIN cabinet","Controller, PSU, driver",60,1.8,"C","design","TO DESIGN"),
]),
("F · Cablaggio, sensori e metrologia",[
("ML-CAB-001","Electrical","Cavi schermati macchina–quadro","1 set",1,"Motion + spindle + I/O","EMC-aware routing",70,0.7,"M","source","TO SOURCE"),
("ML-CHAIN-001","Mechanical","Drag chains","1 set",1,"Low-profile cable chain","X/Z sul ponte",35,0.3,"M","source","TO SOURCE"),
("MC-SNS-001","Sensing","Home/limit sensors","4",4,"Inductive class","XYZ home + limite",8,0.05,"M","source","TO SOURCE"),
("MC-PROBE-001","Metrology","XYZ touch probe","1",1,"Wired probe class","Work offset / edge finding",45,0.2,"M","design","TO QUALIFY"),
("MC-TOOL-001","Metrology","Tool length setter","1",1,"Wired setter class","Tool length reference",55,0.3,"M","design","TO QUALIFY"),
]),
("G · Accessori (non inclusi nei totali)",[
("ML-RS-001","Clearance","Rialzi spalle spinati","1 set",1,"Custom Al blocks +50 mm","Clearance manuale riferita da spine",45,0.8,"A","design","TO DESIGN"),
("MC-TD-006","ToolDock","Dock rail","1",1,"Stessa parte della Standard","Arriva con il primo kit ToolDock; include la camma di sgancio del clamp (ICD v1)",80,0.8,"A","design","TO DESIGN"),
]),
]
