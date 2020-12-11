~Version
VERS .              3.0       :CWLS LOG ASCII STANDARD - VERSION 3.0
WRAP .               NO       :ONE LINE PER DEPTH STEP
DLM  .            COMMA       :DELIMITING CHARACTER
PROG .       striplog.py      :LAS Program name and version
CREA . 2015/03/22 19:33       :LAS Creation date {YYYY/MM/DD hh:mm}

~Well
#MNEM .UNIT  DATA             DESCRIPTION
#---- ------ --------------   -----------------------------
STRT .M         0.000         :START DEPTH
STOP .M       288.554         :STOP DEPTH
STEP .M      -999.2500        :STEP
NULL .       -999.2500        :NULL VALUE

WELL .       P-135                 :WELL
FLD  .       UNDEFINED             :FIELD
CTRY .       CA                    :COUNTRY

PROV .       NOVA SCOTIA           :PROVINCE
UWI  .                             :UNIQUE WELL ID
LIC  .       P-135                 :LICENSE NUMBER

~Parameter
#MNEM .UNIT  VALUE            DESCRIPTION
#---- ------ --------------   -----------------------------

#Required parameters
RUN  .        ONE             :RUN NUMBER
PDAT .        GL              :PERMANENT DATUM
APD  .M       -999.250        :ABOVE PERM DATUM
DREF .        KB              :DEPTH REFERENCE
EREF .M       -999.250        :ELEVATION OF DEPTH

#Remarks
R1   .                        :REMARK LINE 1
R2   .                        :REMARK LINE 2
R3   .                        :REMARK LINE 3

~Lithology_Parameter
LITH .   Striplog         : Lithology source          {S}
LITHD.   MD               : Lithology depth reference {S}

~Lithology_Definition
LITHT.M                   : Lithology top depth       {F}
LITHB.M                   : Lithology base depth      {F}
LITHD.                    : Lithology description     {S}

~Lithology_Data | Lithology_Definition
    0.000,   68.275,  "Boss Point Formation. Sandstone: red brown, coarse grained quartz pebble rich, locally grading to conglomerate in texture, the quartz grains are potassium feldspar rich, locally clear glassy, occasional red brown mudstone matrix, occasional to rare black mafic detrital.
Quartz pebble conglomerate: red bed mudstone matrix with broken coarse grained fragments of clear glassy quartz to potassium feldspar rich and varied color angular lithic fragments, occasional units of red brown mudstone partings, trace disseminated pyrite. The lithic fragments are micaceous. The formation is very firm & non calcareous."
   68.275,  288.554,  "Claremont Formation. Quartz pebble/polymictic conglomerate: polymictic conglomerate: red brown potassium rich feldspar rich quartz with dark gray mafic grains in mudstone matrix, the pebbles are sub angular to broken shards, the matrix is firm, non calcareous with occasional clear glassy coarse grained sandstone content.
Conglomerate: varicolored clasts of volcanics and intrusive (micaceous granite), minor arkosic sandstone (stringers), red mud matrix, conglomerate is silicified, calcareous, minor kaolin, minor metasediments (detrital). 10% quartzose sandstone (interbeds).
Conglomerate: varicolored (mostly pink and orange) clasts of intrusives (micaceous granite) and felsic volcanics (represented in sample by broken shards of varicolored quartz, kspar and plagioclase), increased red and green metasediments (detrital), red mud matrix, silicified, weakly calcareous. Minor red sandy siliceous siltstone (interbeds)."
