"""Dati BOM Base Light Core (D023) → bom/base-light.html.

Ogni riga: (id, gruppo, componente, q.tà etichetta, q.tà numerica, candidate, specifica,
€/cad, kg/cad, dove, classe stato, stato).
dove: "M" = sulla macchina, "C" = quadro/unità esterne, "A" = accessorio (escluso dai totali).
Prezzi: TARGET a lotto da 50 macchine (D023), non prezzi di prototipo come Standard e Pro.
Tetto BOM Light Core: ≤ €1.050.
Dopo una modifica: python3 tools/bom/build.py
"""
PAGE = "bom/base-light.html"
EXTERNAL_LABEL = "quadro"

G=[
("A · Struttura e riferimenti",[
("ML-BAS-001","Structure","Telaio basamento","1",1,"Tubi Al 40×40×1,5 saldati a scala, pad e sedi lavorati in lotto","Due longheroni, traversa BF, traversa di coda 40×80 (BK Y + motore Y), 4 sbalzi 40×40 sotto le flange ICD §5 delle spalle; niente traversa anteriore (CAD v2, D036)",80,1.84,"M","design","CAD v1"),
("ML-GAN-001","Structure","Trave gantry","1",1,"Tubo Al 40×80, faccia guide 4 mm, pareti 2 mm, lavorato in lotto","Ponte fisso (D006), senza canale: guide X MGN12 a 52 mm sulla faccia, vite X e BK10/BF10 sul cielo; blocchetti d'angolo per le M6 delle spalle (CAD v2, D036)",35,1.22,"M","design","CAD v1"),
("ML-GAN-002","Structure","Spalle gantry","2",2,"Al 5083 4 mm + flangia 10 mm scaricata, taglio + lavorazione in lotto","Ai lati della trave, flangia ICD §5 spinata al telaio (pattern invariato, rialzi +50, D007); motore X sulla spalla destra all'altezza della vite (CAD v2, D036)",15,0.37,"M","design","CAD v1"),
("ML-Z-001","Structure","Piastra asse Z","1",1,"Al 5083 6 mm con ali 5 mm","Guide Z + master ToolDock (CAD v2, D036)",18,0.31,"M","design","CAD v1"),
("ML-XC-001","Structure","Carrello X","1",1,"Al 6 mm, piastra + torre, senza ali","Porta pattini X, guide Z a 90 mm, vite, BK Z e motore Z; sopra i pattini X si stringe a 110 mm (CAD v2, D036)",22,0.53,"M","design","CAD v1"),
("ML-BRK-001","Structure","Staffe chiocciole, motori e supporti","1 set",1,"Custom Al, 6 pezzi","Staffa chiocciola X sopra la trave, staffa chiocciola Y, piastrina chiocciola Z, staffa motore Z, spessori BK/BF X sul cielo trave, piastra ponte BK Z (CAD v2, D036)",8,0.52,"M","design","CAD v1"),
("ML-TBL-001","Workholding","Tavola Y / tooling plate","1",1,"Al 9 mm, tasche e boss pieni","Tavola mobile Y (D006), 450×350 utile; pelle 4 mm, boss Ø16 × 9 mm attorno ai fori M6 e ai riferimenti (D018): stessi pallet delle altre basi",60,2.18,"M","design","CAD v1"),
("ML-HW-001","Structure","Fasteners + dowel pins","1 set",1,"ISO","Viteria, spine, inserti",15,0.4,"M","source","TO SOURCE"),
("MC-TBL-002","Workholding","Inserti M6 + boccole R1/R2","1 set",1,"63 inserti filettati M6 in acciaio + 2 boccole Ø8 H7","Filetto utile 9 mm nei boss; R1 (50, 50) tonda, R2 (400, 50) asola (ICD v4, D018)",14,0.08,"M","source","TO SOURCE"),
]),
("B · Cinematica XYZ",[
("ML-LIN-151","XY","Guide lineari MGN12","4 rails",4,"MGN12, HIWIN o equivalente qualificato","2 rail X 620 mm + 2 rail Y 580 mm (passo pattini Y 160, Light a piastre D036)",18,0.39,"M","source","TO SOURCE"),
("ML-LIN-152","XY","Pattini MGN12H","8",8,"MGN12H, HIWIN o equivalente qualificato","2 pattini per rail, versione lunga, precarico Z1: equivalente accettato solo con rigidezza ≥ HIWIN (175 N/µm, D022)",5,0.05,"M","source","TO SOURCE"),
("ML-LIN-153","Z","Guide lineari MGN12","2 rails",2,"MGN12, HIWIN o equivalente qualificato","280 mm (D019)",9,0.18,"M","source","TO SOURCE"),
("ML-LIN-154","Z","Pattini MGN12H","4",4,"MGN12H, HIWIN o equivalente qualificato","4 pattini complessivi",5,0.05,"M","source","TO SOURCE"),
("ML-BS-1204X","X","Ball screw X","1",1,"SFU1204 C7 rullata","570 mm totali, estremità BK/BF comprese (D019); sopra la trave (D036). Massa dal CAD: vite piena Ø12 + chiocciola (limite superiore)",22,0.62,"M","validate","TO VALIDATE"),
("ML-BS-1204Y","Y","Ball screw Y","1",1,"SFU1204 C7 rullata","Vite singola centrale sotto la tavola (D006), 480 mm totali (CAD v1: 8 mm fra staffa e BK a fine corsa). Massa dal CAD (limite superiore)",22,0.54,"M","validate","TO VALIDATE"),
("ML-BS-1204Z","Z","Ball screw Z","1",1,"SFU1204 C7 rullata","260 mm totali (D019), fissa-libera: solo BK10 in alto (D036). Massa dal CAD (limite superiore)",22,0.34,"M","validate","TO VALIDATE"),
("ML-BKBF-001","XYZ","Supporti BK10/BF10","2 set + 1 BK10",1,"BK/BF class","Set BK10/BF10 per X (sul cielo della trave) e Y; solo BK10 per la Z fissa-libera (D036)",23,0.9,"M","source","TO SOURCE"),
("ML-CPL-001","XYZ","Giunti motore-vite","3",3,"Low backlash bellows class","Taglia NEMA17",5,0.07,"M","source","TO SOURCE"),
("ML-MOT-002","XYZ","Motori NEMA17 encoder-ready","3",3,"NEMA17 ~0,6 Nm, doppio albero","Open-loop sulla Core; il Platform Pack aggiunge un encoder a innesto sul secondo albero, i motori restano (D026). Crash load D014 invariato",14,0.4,"M","design","CANDIDATE"),
]),
("C · Spindle base",[
("ML-SP-001","Spindle","Spindle BLDC 300–500 W","1",1,"ER11, air-cooled","Testa completa entro il carico ToolDock di 2 kg",60,1.0,"M","design","TO QUALIFY"),
("ML-SP-002","Spindle","Driver BLDC + alimentatore","1",1,"0,5 kW class, alimentatore dedicato","Nel quadro; enable dal controller, tolto dal consenso cambio testa",45,0.8,"C","source","TO SOURCE"),
("ML-SP-003","Spindle","Spindle mount","1",1,"Custom machined clamp","Receiver-compatible con ToolDock",12,0.23,"M","design","CAD v1"),
("ML-SP-005","Tooling","ER11 collet starter set","1",1,"2 pinze (3,175 · 6 mm)","Starter tooling only",3,0.05,"M","source","TO SOURCE"),
]),
("D · ToolDock manuale (interfaccia ICD comune)",[
("ML-TD-001","ToolDock","Master kinematic plate","1",1,"Stesso accoppiamento a 3 sfere e pull-stud delle altre basi","Montata sul carrello Z; sedi già lavorate per clamp automatico, connettore ibrido e connettore dati del Platform Pack",60,0.38,"M","critical","CRITICAL DESIGN"),
("ML-TD-002","ToolDock","Base spindle receiver","1",1,"Receiver ICD comune","Stessa receiver delle altre basi: le teste restano intercambiabili",30,0.26,"M","design","CAD v1"),
("ML-TD-003","ToolDock","Clamp manuale","1",1,"Leva a camma sul pull-stud comune","Preload ≥ 0,5 kN come la classe L (D016); sostituito dal clamp automatico nel Platform Pack, che si monta nelle stesse sedi",35,0.17,"M","critical","CRITICAL DESIGN"),
("ML-TD-004","ToolDock","Connettore modulo manuale","1",1,"Circolare industriale 12 poli","Spindle, 48 V modulo, I/O e ID; si innesta a mano, solo con consenso cambio testa attivo",15,0.1,"M","design","TO SOURCE"),
("MC-TD-005","ToolDock","Module ID","1",1,"1-Wire comune","Stesso ID delle altre basi: il controller rifiuta le teste non Core-ready",3,0.01,"M","design","TO DESIGN"),
]),
("E · Controllo (quadro esterno)",[
("ML-CTRL-001","Control","Controller grblHAL","1",1,"32 bit, Ethernet, 3 driver TMC5160 integrati","Al posto di Mesa + PC + driver separati; web UI, niente PC dedicato",65,0.2,"C","validate","TO VALIDATE"),
("ML-PWR-001","Power","48 V PSU","1",1,"Mean Well LRS-200-48","Motion NEMA17 + linea modulo Core-ready (≤ 60 W)",28,0.6,"C","source","TO SOURCE"),
("ML-EL-BOX","Electrical","Quadro compatto + E-stop","1",1,"Box, E-stop, fusibili, morsetti","E-stop su enable driver e spindle; pulsante consenso cambio testa",27,1.2,"C","design","TO DESIGN"),
]),
("F · Cablaggio, sensori e metrologia",[
("ML-CAB-001","Electrical","Cavi macchina–quadro","1 set",1,"Cablaggi preassemblati","Motori con poli encoder già previsti, spindle, connettore modulo, sensori: restano con il Platform Pack (D026)",28,0.6,"M","source","TO SOURCE"),
("ML-CHAIN-001","Mechanical","Drag chains","1 set",1,"Low-profile cable chain","X/Z sul ponte",12,0.3,"M","source","TO SOURCE"),
("ML-SNS-001","Sensing","Home sensors","3",3,"Micro-switch o induttivi","Home XYZ; i limiti restano sugli hard stop con bumper (D014)",3,0.03,"M","source","TO SOURCE"),
("ML-TOOL-001","Metrology","Tool length setter","1",1,"Wired setter class","Riferimento lunghezza utensile",12,0.2,"M","design","TO QUALIFY"),
("ML-CAB-002","Electrical","Pressacavi e connettori","1 set",1,"Pressacavi, capicorda, fascette","Minuteria di cablaggio",10,0.1,"M","source","TO SOURCE"),
]),
("G · Accessori e upgrade (non inclusi nei totali)",[
("ML-UP-001","Upgrade","Platform Pack","1",1,"Upgrade montabile dal cliente, BOM dedicata","Encoder a innesto, driver closed-loop, Mesa + LinuxCNC, clamp automatico, connettori ibrido e dati: profilo Platform della ICD v4 (D026, vedi BOM Platform Pack)",829,6.4,"A","design","TO DESIGN"),
("ML-PROBE-001","Metrology","XYZ touch probe","1",1,"Wired probe class","Work offset / edge finding",35,0.2,"A","design","TO QUALIFY"),
("MC-ENC-001","Enclosure","Cabina opzionale","1",1,"Telaio indipendente + pannelli PC 4 mm + porta con interlock","Agganciata al basamento, mai al ponte; LED, attacco aspirazione Ø100, vasca trucioli, fonoassorbente; variante laser-ready da qualificare per ogni modulo laser (lunghezza d'onda, protezione ottica, interlock, verifica delle fughe) (D025)",280,13.0,"A","design","TO DESIGN"),
("ML-RS-001","Clearance","Rialzi spalle spinati","1 set",1,"Custom Al blocks +50 mm","Clearance manuale riferita da spine",30,0.8,"A","design","TO DESIGN"),
("MC-TD-006","ToolDock","Magazine indicizzato","1",1,"2–4 posti, indicizzazione motorizzata","Richiede il Platform Pack; sul ponte, presenta la testa in un\'unica posizione di docking (D016, D021)",200,2.0,"A","design","TO DESIGN"),
]),
]
