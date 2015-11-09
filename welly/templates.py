#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reader for template strings.

Replaces Mac OS newlines with \n characters.
"""
import re


def get_template(name):
    """
    Still unsure about best way to do this, hence cruft.
    """
    text = re.sub(r'\r\n', r'\n', name)
    text = re.sub(r'\{([FISDE°].*?)\}', r'{{\1}}', text)
    return text

__las = """~Version
VERS .              3.0       :CWLS LOG ASCII STANDARD - VERSION 3.0
WRAP .               NO       :ONE LINE PER DEPTH STEP
DLM  .            COMMA       :DELIMITING CHARACTER
PROG .      {prog:>12s}      :LAS Program name and version
CREA . {date:16s}       :LAS Creation date {{YYYY/MM/DD hh:mm}}

~Well
#MNEM .UNIT  DATA             DESCRIPTION
#---- ------ --------------   -----------------------------
STRT .M      {start:8.3f}         :START DEPTH
STOP .M      {stop:8.3f}         :STOP DEPTH
STEP .M      {step:9.4f}        :STEP
NULL .       {null:9.4f}        :NULL VALUE

WELL .       {well:20s}  :WELL
FLD  .       UNDEFINED             :FIELD
CTRY .       CA                    :COUNTRY

PROV .       NOVA SCOTIA           :PROVINCE
UWI  .       {uwi:21s} :UNIQUE WELL ID
LIC  .       {lic:21s} :LICENSE NUMBER

~Parameter
#MNEM .UNIT  VALUE            DESCRIPTION
#---- ------ --------------   -----------------------------

#Required parameters
RUN  .        ONE             :RUN NUMBER
PDAT .        GL              :PERMANENT DATUM
APD  .M       {apd:8.3f}        :ABOVE PERM DATUM
DREF .        KB              :DEPTH REFERENCE
EREF .M       {eref:8.3f}        :ELEVATION OF DEPTH

#Remarks
R1   .                        :REMARK LINE 1
R2   .                        :REMARK LINE 2
R3   .                        :REMARK LINE 3

{section}

{curve}"""

__section = """~{name}_Parameter
{short} .   {source:16s} : {name} source          {S}
{short}D.   MD               : {name} depth reference {S}

~{name}_Definition
{short}T.M                   : {name} top depth       {F}
{short}B.M                   : {name} base depth      {F}
{short}D.                    : {name} description     {S}

~{name}_Data | {name}_Definition
{data}"""

__curve = """~Curve
#MNEM .UNIT  LOG CODES        DESCRIPTION
#---- ------ --------------   -----------------------------
DEPT .m        00 001 00 00               :Depth Index - Measured Depth
LITH .         00 000 00 00               :See remarks

~Ascii
{logs}"""

las = get_template(__las)
section = get_template(__section)
curve = get_template(__curve)
