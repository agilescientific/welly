# -*- coding: utf 8 -*-
"""
Codes for Canstrat ASCII files; only used by canstrat.py.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""


# Codes for rtc
rtc_txt = """X ROC-C_X ROCKTP_IGNEB ROCK TYPE 1 Igneous Basic
N ROC-C_N ROCKTP_IGNEA ROCK TYPE 2 Igneous Acidic
Z ROC-C_Z ROCKTP_META ROCK TYPE 3 Metamorphic
V ROC-C_V ROCKTP_VOLC ROCK TYPE 4 Volcanic
R ROC-C_R ROCKTP_SID ROCK TYPE 8 Siderite
U ROC-C_U ROCKTP_TILL ROCK TYPE 9 Glacial Till
E ROC-C_E ROCKTP_CONGL ROCK TYPE 12 Conglomerate
F ROC-C_F ROCKTP_BRECC ROCK TYPE 13 Breccia
H ROC-C_H ROCKTP_CHERT ROCK TYPE 16 Chert
J ROC-C_J ROCKTP_SAND ROCK TYPE 17 Sandstone
I ROC-C_I ROCKTP_SILT ROCK TYPE 18 Siltstone
C ROC-C_C ROCKTP_CLAY ROCK TYPE 19 Clay
S ROC-C_S ROCKTP_SHALE ROCK TYPE 20 Shale
B ROC-C_B ROCKTP_BENT ROCK TYPE 22 Bentonite
Q ROC-C_Q ROCKTP_COAL ROCK TYPE 24 Coal
M ROC-C_M ROCKTP_MARL ROCK TYPE 26 Marlstone
L ROC-C_L ROCKTP_LST ROCK TYPE 27 Limestone
D ROC-C_D ROCKTP_DOL ROCK TYPE 30 Dolomite
A ROC-C_A ROCKTP_ANHY ROCK TYPE 35 Anhydrite
T ROC-C_T ROCKTP_SALT ROCK TYPE 37 Salt
G ROC-C_G ROCKTP_GYP ROCK TYPE 39 Gypsum
P ROC-C_P ROCKTP_PHOS ROCK TYPE 40 Phosphate"""

rtc = {w[0]: ' '.join(w[6:]) for w in [r.split() for r in rtc_txt.split('\n')]}


# Code for grain size
grains_txt = """X GRA-C_X GRAINS_CRYPTOX GRAIN, CRYSTAL OR 0.001 Cryptocrystalline (carbonate, chert, coal)
L GRA-C_L GRAINS_LITHO GRAIN, CRYSTAL OR 0.001 Lithographic (carbonate, chert, coal)
M GRA-C_M GRAINS_SHALE GRAIN, CRYSTAL OR 0.001 Shale, Clay, Marlstone, Bentonite
V GRA-C_V GRAINS_VOLC GRAIN, CRYSTAL OR 0.001 Volcanics (equivalent to size M)
1 GRA-C_1 GRAINS_SILT2 GRAIN, CRYSTAL OR 0.0176 1/2 Silt Size
2 GRA-C_2 GRAINS_SILT GRAIN, CRYSTAL OR 0.0473 Silt Size
3 GRA-C_3 GRAINS_VFGR2 GRAIN, CRYSTAL OR 0.0781 1/2 Very fine grained
4 GRA-C_4 GRAINS_VFGR GRAIN, CRYSTAL OR 0.1094 Very fine grained
5 GRA-C_5 GRAINS_FGR2 GRAIN, CRYSTAL OR 0.156 1/2 Fine grained
6 GRA-C_6 GRAINS_FGR GRAIN, CRYSTAL OR 0.2185 Fine grained
7 GRA-C_7 GRAINS_MGR2 GRAIN, CRYSTAL OR 0.313 1/2 Medium grained
8 GRA-C_8 GRAINS_MGR GRAIN, CRYSTAL OR 0.438 Medium grained
9 GRA-C_9 GRAINS_CGR2 GRAIN, CRYSTAL OR 0.625 1/2 Coarse grained
0 GRA-C_0 GRAINS_CGR GRAIN, CRYSTAL OR 0.875 Coarse grained
C GRA-C_C GRAINS_VCGR GRAIN, CRYSTAL OR 1.500 Greater than 1.000 mm"""

grains = {w[0]: float(w[6]) for w in [r.split() for r in grains_txt.split('\n')]}
grains['L'] += 0.0001
grains['M'] += 0.0002
grains['V'] += 0.0003
grains['X'] += 0.0004


# Code for fwork
fwork_txt = """** FRA-N_XX FRAMEW_-1 FRAMEWORK -1 uninterpretable
00 FRA-N_00 FRAMEW_0 FRAMEWORK 0 0%
01 FRA-N_01 FRAMEW_10 FRAMEWORK 10 10%
02 FRA-N_02 FRAMEW_20 FRAMEWORK 20 20%
03 FRA-N_03 FRAMEW_30 FRAMEWORK 30 30%
04 FRA-N_04 FRAMEW_40 FRAMEWORK 40 40%
05 FRA-N_05 FRAMEW_50 FRAMEWORK 50 50%
06 FRA-N_06 FRAMEW_60 FRAMEWORK 60 60%
07 FRA-N_07 FRAMEW_70 FRAMEWORK 70 70%
08 FRA-N_08 FRAMEW_80 FRAMEWORK 80 80%
09 FRA-N_09 FRAMEW_90 FRAMEWORK 90 90%
10 FRA-N_10 FRAMEW_100 FRAMEWORK 100 100%"""

fwork = {w[0]: int(w[4]) for w in [r.split() for r in fwork_txt.split('\n')]}


# Code for colour
colour_txt = """W COL-C_W COLOUR_WHITE COLOUR 1 White
C COL-C_C COLOUR_CREAM COLOUR 2 Cream
F COL-C_F COLOUR_BUFF COLOUR 3 Buff-Tan
Y COL-C_Y COLOUR_YELLOW COLOUR 4 Yellow
S COL-C_S COLOUR_S&P COLOUR 5 Salt and Pepper
V COL-C_V COLOUR_VARIC COLOUR 6 Varicoloured
O COL-C_O COLOUR_ORANGE COLOUR 7 Orange
R COL-C_R COLOUR_RED COLOUR 8 Red
P COL-C_P COLOUR_PURPLE COLOUR 9 Purple
U COL-C_U COLOUR_BLUE COLOUR 10 Blue
N COL-C_N COLOUR_GREEN COLOUR 11 Green
B COL-C_B COLOUR_BROWN COLOUR 12 Brown
G COL-C_G COLOUR_GRAY COLOUR 13 Gray
K COL-C_K COLOUR_BLACK COLOUR 14 Black"""

colour = {w[0]: ' '.join(w[5:]) for w in [r.split() for r in colour_txt.split('\n')]}
colour[' '] = ''


# Code for colour modifier
cmod_txt = """V COI-C_V COLOURINT_VLIGHT COLOUR INTENSITY 1 Very Light
L COI-C_L COLOURINT_LIGHT COLOUR INTENSITY 3 Light
M COI-C_M COLOURINT_MEDIUM COLOUR INTENSITY 5 Medium
D COI-C_D COLOURINT_DARK COLOUR INTENSITY 7 Dark
K COI-C_K COLOURINT_VDARK COLOUR INTENSITY 9 Very Dark"""

cmod = {w[0]: ' '.join(w[6:]) for w in [r.split() for r in cmod_txt.split('\n')]}
cmod[' '] = ''


# Code for porgrade
porg_txt = """1 POR-N_1 PORGRADE_3 POROSITY GRADE 3 3%
2 POR-N_2 PORGRADE_6 POROSITY GRADE 6 6%
3 POR-N_3 PORGRADE_9 POROSITY GRADE 9 9%
4 POR-N_4 PORGRADE_12 POROSITY GRADE 12 12%
5 POR-N_5 PORGRADE_15 POROSITY GRADE 15 15%
6 POR-N_6 PORGRADE_20 POROSITY GRADE 20 20%
7 POR-N_7 PORGRADE_26 POROSITY GRADE 26 26%
8 POR-N_8 PORGRADE_33 POROSITY GRADE 33 33%
9 POR-N_9 PORGRADE_39 POROSITY GRADE 39 >33%"""

porgrade = {w[0]: float(w[5])/100 for w in [r.split() for r in porg_txt.split('\n')]}

# Codes for oil stains.
stain_txt = """Q OIL-C_Q OILSTN_QUEST OIL STAIN 1 Questionable stain
D OIL-C_D OILSTN_DEAD OIL STAIN 2 Dead Stain
M OIL-C_M OILSTN_MEDSPOT OIL STAIN 3 Medium-Spotted Stain
G OIL-C_G OILSTN_GOOD OIL STAIN 4 Good Stain"""

stain = {w[0]: w[2][7:].title() for w in [r.split() for r in stain_txt.split('\n')]}
stain[' '] = 'None'

oil = {' ': 0, 'Q': 1, 'D': 2, 'M': 3, 'G': 4}
