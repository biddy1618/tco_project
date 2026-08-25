Default:

5.1. HEADER | Text: "PRESENT SITUATION:"

**5.2. PRESENT SITUATION**

{problem\_statement}



5.3. HEADER | Text: "PROPOSED SOLUTION:"

**5.4. PROPOSED SOLUTION**

* Text: "Proposed Solution presented in this Job Pack." -> {scope\_type}, {line\_class}, {placeholders\_TP}





5.5. HEADER | Text: "SCOPE OF WORK"

**5.6. SCOPE OF WORK**

* ~~Text: "BUSINESS PARTNER (BP) shall strictly follow all relevant TCO Safety Instructions."~~
* ~~Text: "BUSINESS PARTNER (BP) shall follow all Quality Management (QM) requirements designated in the Quality Control package."~~



**5.7. PRELIMINARY SITE WORK**

{scope\_type} -> PSW activities(keep)

* ~~Text: "Prior to start of mechanical activities, perform wall thickness testing at TPxx-yyy/000 and TPxx-yyy/999." -> {placeholders\_TP}, {scope type}(keep), if **no TP(remove)**~~
* ~~Text: "NOTE: Perform the wall thickness test by marking out and recording a matrix as directed by the TCO FER Unit Inspector." prev line(keep), **no prev line(remove)**~~
* ~~Text: "Prior to commencing any fabrication works verify dimensions, pipe routing and field weld locations on site." -> {scope\_type} almost always(keep)~~
* ~~Text: "NOTE: When allocating FW \& FFW locations for machinery \[OR] vessel nozzle \[OR] PSV — strain considerations apply." -> {scope\_type} **always(remove)**~~
* ~~Text: "NOTE: Invite Responsible Engineer to verify dimensions / internal configuration / XXX on site, once vessel is isolated." -> {scope\_type} Use when insufficient data for DTEC to verify Pressure Vessel internal dimensions prior to AFC?~~
* ~~Text: "Prior to excavation works, for installation of pipe support foundation(s) in unpaved areas, perform surveying work for the presence of underground utilities. Arrange this with the TCO Lead Field Surveyor, phone 4931." -> {scope\_type} scope\_type = new piping route(keep), **almost always(remove)**~~
* ~~Text: "Perform excavation and install concrete foundation per isometric drawing 00-YYYY-L-ZZZZ." prev line(keep), **no prev line(remove)**~~
* ~~Text: \[Add when replacing existing equipment with new equipment of different weight]. Consider the weight of the new equipment indicated on drawing XXXX during developing execution steps and lifting plan."~~
* ~~"NOTE: DTEC completed required engineering studies of existing/new piping, foundation \& supports and confirmed new equipment weight is within allowable loads."~~



5.8. SHOP WORK | Text: "SHOP WORK: "

{spool\_prefab}, **{scope\_type} = valve replacement (only), clamp installation (TLR) (remove)**

* ~~Text: "Withdraw materials required for this Job Pack from TCO Warehouse according to Material Request(s)."~~
* ~~Text: "Perform Positive Material Identification (PMI) as per TCO RE QM SWP-20 Procedure on all corrosion resistant alloy (CRA) materials and weld consumables." -> {material}, {material\_family}, **{alloy\_pmi\_required}=100%** ,alloy\_pmi\_required=true <b>(material is SS/alloy/duplex)</b>(keep), Plain <b>CS(remove) (src=TCO NDE)</b>~~
* ~~Text: "Prefabricate pipe spools and pipe supports, as per isometric drawing(s) 00-YYYY-L-ZZZZ. Use TCO-approved Welding Procedure Specification(s) (WPSs) indicated on isometric drawing(s).  BP shall comply with TCO Guideline 16-0015-MI for socket-welded joints.” -> {spool\_prefab}, {placeholders\_dwg} **Never(remove)**~~
* ~~Text: "Perform PWHT as specified by WPS and per TES PIM-SU-2505 / W-ST-2011 / 2016 / 2026 / 2028." -> {pwht\_required}, {material}, {thickness} pwht\_required=true(keep) **(src=TCO WPS)**~~
* Text: "Perform NDE and hardness testing of shop welds, as specified on drawing 00-YYYY-L-ZZZZ." -> {spool\_prefab}, {placeholders\_dwg}, {nde\_class} **No shop welds/spool\_prefab=False (remove)**
* ~~Text: "NOTE: Perform NDE and hardness testing only after PWHT!" -> {pwht\_required} = true(keep)~~
* ~~Text: "NOTE: BP must check with MaxTrax admin on NDE requirements prior to commence welding." flag(give choice to engineer keep/remove)~~
* Text: "Perform shop hydrostatic testing of flanged spools per TES PIM-SU-3541-TCO." -> {spool\_prefab}, {placeholders\_dwg}, {hydrotest\_method} spool\_prefab=true(keep), **otherwise(remove)**
* ~~Text: "NOTE: Test water for SS-300 piping shall be < 50 ppm chloride." -> {material\_family} = SS-300(keep), **Non-SS materials(remove)**~~
* ~~Text: "Abrasive blast and coat new piping spools and supports per TES COM-SU-5191-TCO." ->~~

~~{coating\_system}, {material\_family}, {placeholders\_dwg} coating\_required=true(cs)(keep), **uncoated SS interior service(remove)**~~

* ~~Text: "NOTE: Mask-off field-weld joints and flange faces prior to coating." prev line(keep), **no prev line(remove)**~~



5.9. SITE WORK | Text: "SITE WORK: "

* ~~Text: "Perform relevant job safety assessments (PPHA \& JSA) and obtain required PTWs."~~
* ~~Text: "Demarcate work area as necessary and erect scaffolding for access." ->~~ {work\_elevation} **Ground-level only(remove) excav. works?????**
* ~~Text: "NOTE: TCO Operations shall isolate, depressurize, drain and ready for Hot Work…"~~
* Text: "A spring stopping pin must be installed before dismantling." \[Only when reusing existing spring support] {existing\_spring\_support\_reuse}=true\*\*?????\*\*
* Text: "Remove all cladding and insulation to the extent required." {insulation\_type} != None(keep) **NI?**, **bare piping(remove) (src=5112, table 10)?????**
* Text: "Checklist MCL005A-1 (Spring Support Verification) to be completed." \[Only when reusing existing spring support] {existing\_spring\_support\_reuse=true}
* Text: "Invite Machinery Maintenance team to install dial gauges prior to existing piping cut." \[Only for machinery] {machinery\_connection\_in\_scope}?=true
* Text: "NOTE: Gauges stay on until all work complete. Last step is record of gauges and removal." prev line(keep), **no prev line(remove)**
* Text: "Arrange with TTT \[OR] TASP \[OR] Zone Maintenance \[OR] Plant I\&E to isolate, LOTO and remove electric trace heating and instruments." {heat\_tracing}=electric OR instruments at TP(**keep)** otherwise(remove)
* Text: "NOTE: BP to match mark, call unit operator, show mark and record location prior to cutting/removal." prev line(keep), **no prev line(remove)**
* Text: "Apply and sign special tape per SP-26 at TP-XXX." -> {placeholders\_TP} **Pure bolted-flange replacement(remove)?**
* ~~Text: "Cold Cut, unbolt and remove existing piping and pipe supports per 'Destruct Detail' of isometric drawing 00-YYYY-L-ZZZZ."~~ **Pure bolted-flange replacement(remove)?**
* Text: "Perform hydrogen bake-out in the weld zone of each tie-in points per isometric drawing 00-YYYY-L-ZZZZ." h2s\_status=wet\_h2s OR sour service(keep), \*\***Sweet/non-sour service(remove)?** {\*\*h2s\_status}?, {service}, {placeholders\_dwg} **service?????**
* Text: "Bevel cut ends of existing piping at the tie-in point(s) TPxx-yyy/000 for field welding per drawing 00-YYYY-L-ZZZZ." Always for tie-in field welding(keep), **Bolted-flange only(remove)** {placeholders\_TP}, {placeholders\_dwg}
* Text: "Inspect the prepared weld bevel ends per bevel\_inspection\_methods (e.g., 100% VT + 100% MT/PT, or 100% PT/MT only)." \*\*Bolted-only(remove) {\*\*bevel\_inspection\_methods}, **{material}?????**
* Text: "NOTE: Perform inspection of weld bevels and nipo-flange landings PRIOR to welding." prev line(keep), **no prev line(remove)**
* ~~Text: "Perform PMI at field joints per TCO RE QM SWP-20 on alloy materials listed in SWP-20 Appendix 20-1." {material}, {material\_family}, **{alloy\_pmi\_required}=true(keep)**, <b>Plain CS(remove)?????</b>~~
* ~~Text: "Install piping (and pipe supports, if merged) per isometric drawing 00-YYYY-L-ZZZZ. For field welds use TCO-approved WPSs." -> placeholders\_dwg, wps\_list, new\_support\_complexity? **Always(keep)**~~
* Text: "NOTE: Do NOT drill the header or cut out nipo-flange coupons prior to hydro-testing branch connections." -> **{scope\_type}?** Branch / nipo-flange in scope(keep), **No branch connections(remove)?????**
* Text: NOTE: Verify piping alignment with respect to machinery nozzle." \[{machinery\_connection\_in\_scope}=true], \[For machinery installation projects only]**?????**
* Text: "Install civil structural support per isometric drawing 00-YYYY-L-ZZZZ and attached Standard Support drawing." new\_support\_complexity=Complex (separate step needed)? **new\_support\_complexity=Simple (merge into line 56)?????**
* ~~Text: "Perform PWHT of field joints per WPS and TES PIM-SU-2505 / W-ST-2011 / 2016 / 2026 / 2028, PCR-PU-6239-TCO."~~ {pwht\_required}=true **Prune W-ST-XXXX list to applicable spec?????**
* ~~Text: "Perform NDE and hardness testing of field welds, per isometric drawing 00-YYYY-L-ZZZZ." always for field welds(keep)~~, **Bolted-only(remove) {nde\_class}?????**
* ~~Text: "NOTE: Perform NDE and Hardness Testing only after PWHT!" {pwht\_required=true}(keep)~~
* Text: "NOTE: BP must check with MaxTrax admin on NDE requirements prior to commence welding." **Per project convention**
* Text: "Perform field hydrostatic testing of new piping per isometric drawing 00-YYYY-L-ZZZZ in accordance with TES PIM-SU-3541-TCO." -> hydrotest\_method, placeholders\_dwg, service | hydrotest\_method=full\_hydrostatic (process/hydrocarbon/sour services)(keep), **hydrotest\_method=service\_test\_only (instrument air, utility, low-pressure)(remove)?????**
* ~~Text: "NOTE: Test water for SS-300 piping shall be < 50 ppm chloride." {material\_family}=SS-300 (keep), **Non-SS(remove)**~~
* Text: ~~"Perform surface preparation and touch up field welds and other coating damages per TES COM-SU-4743-TCO and COM-SU-5191-TCO."~~
* **LINE 68 - IGNORE (I don't get it)**
* Text: "Arrange with TTT \[OR] TASP \[OR] Zone Maintenance \[OR] Plant I\&E to reinstate / install related electric trace heating and instruments." : heat\_tracing=electric (mirror of line 47)(keep)? **no heat tracing(remove) {heat\_tracing}, {project\_phase}?????**
* ~~Text: "All QM piping passport documentation (A-category Checklists) verified and signed by TCO-approved QM Inspector prior to PSSR."~~
* Text: "Advise \[name] \[name] / \[name], DTEC KTL Plant Support / DTEC T/A / SGP/SGI / FUPO Engineer at ext./radio \[#] about work completion." Always — substitute names + ext/radio + pick correct DTEC group(keep)  **{placeholders\_contact}, {project\_phase}** **(Job Log → responsible engineer, DTEC routing matrix)?????**
* Text: "NOTE: Arrange with RE Integrated Machinery Inspection (IMI) group for inspection." \[For machinery installation only] **{machinery\_connection\_in\_scope}=true ?????**
* ~~Text: "NOTE: Fixed Equipment nozzle \[OR] Machinery \[OR] PSV \[OR] Swing Elbow \[OR strain-sensitive] connections require additional verification."  vessel\_nozzle OR machinery OR psv in scope\*\*(keep)\*\*~~
* ~~Text: "Job Pack Coordinator shall submit completed PIC check-list to Operations after being signed by QM."~~
* ~~Text: "Conduct PSSR and close out A-category punch points."~~
* Text: "Following PSSR reinstate / install insulation and cladding per TES IRM-SU-1381-TCO / IRM-SU-2634-TCO and isometric drawing 00-YYYY-L-ZZZZ." insulation\_type != None, bare piping(**remove**) **{insulation\_type}?????**
* ~~Text: "Close out all B-category punch points and remove associated scaffolding."~~
* ~~Text: "Clean up the work area and demobilize from site."~~



* 5.10 AFTER COMPLETION OF WORK | Always
* ~~Text: "AFTER COMPLETION OF WORK (section header)"~~
* Text: "Perform service test."  {hydrotest\_method=service\_test\_only} OR service in {Instrument Air, Steam, Utility} **Process lines already hydrotested via Line 65(remove)?????**
* ~~Text: "Final as-built package (including B-category Checklist) submitted to TCO QM group within 2 weeks."~~
* ~~Text: "Return excess material to TCO Warehouse."~~



* 5.11. ATTACHMENTS | Always
* Text: "ATTACHMENTS:



* 5.12. REFERENCED TCO SPECIFICATIONS | Always
* Text: "List of 33 candidate TCO specifications." topic relevant sources

