# this script needs an edit.  some records do not have a "selected LGC" because the LGC codes are all null.
# it will be better to explode out the "LGCs" column into the component LGCs, labeling them LGC1, LGC2 etc.
# instead of copying in the already-separated LGC columns from LION
# also, look at CD205, E TREMONT AVE at GRAND CONCOURSE.  the script is not expanding the E in OnPrincipalName4.
# lets go through 205, 405 and 408
# also look at OnPrincipalName4 = EAST BURNSIDE AVENUE UNDERPASS
 
 
"""
Script: Linear Referencing Street Name script
Author: Sabera Tahseen
Date:  May 2025
 
Description:
This script processes a feature class with street segment records to identify the best matching
OnPrincipalName field for each OnPrimaryName, based on the first six characters of the street name.
The comparison prioritizes matches from the rightmost non-empty OnPrincipalName fields
(OnPrincipalName8 → OnPrincipalName).
 
If a match is found:
- The matching OnPrincipalName is saved in the 'selected_street_name' field.
- The corresponding LGC value (from LGC1–LGC8) is saved in the 'selected_LGC' field.
- A new value, 'selected_B7SC', is created by concatenating the B5SC field with the selected LGC value.
 
If no match is found:
- All three output fields remain null (empty).
 
The script checks for missing output fields and creates them if needed. It uses an ArcPy UpdateCursor
to iterate over the feature class and update each row accordingly.
 
Requirements:
- ArcGIS Pro (with arcpy)
- Access to the input feature class stored in a file geodatabase
"""
 
import pandas as pd
from pandas import DataFrame
import os
import re
import arcpy
 
def normalize_direction(name):
    if not name:
        return ""
    name = re.sub(r'[^\w\s]', '', name.upper()).strip()
    direction_map = {
        "E ": "EAST ",
        "W ": "WEST ",
        "N ": "NORTH ",
        "S ": "SOUTH "
    }
    for abbr, full in direction_map.items():
        if name.startswith(abbr):
            return name.replace(abbr, full, 1)
    return name
 
 
 
# workspace!
arcpy.env.workspace = r'S:\8. Asset Management\LRS\LRS\LRS.gdb'
fc = r'S:\8. Asset Management\LRS\LRS\LRS.gdb\LionRB3_geoSegStreetName_RB_CD408'
arcpy.env.overwriteOutput = True
 
 
# field Definitions
primary_field = "OnPrimaryName"
principal_fields = ["OnPrincipalName"] + [f"OnPrincipalName{i}" for i in range(2, 9)]
lgc_fields = ["LGCs"]
output = ["selected_street_name", "selected_LGC", "selected_B7SC"]
 
existing_fields = [f.name for f in arcpy.ListFields(fc)]
 
# add LGC1 - LGC8 fields if they don't exist
for i in range(1, 9):
    field_name = f"LGC{i}"
    if field_name not in existing_fields:
        arcpy.management.AddField(fc, field_name, "TEXT")
 
# add output fields if they don't exist
for field in output:
    if field not in existing_fields:
        arcpy.management.AddField(fc, field, "TEXT")
 
# fields to use in cursor
cursor_fields = [primary_field] + principal_fields + lgc_fields + ["B5SC"] + [f"LGC{i}" for i in range(1, 9)] + output
 
 
with arcpy.da.UpdateCursor(fc, cursor_fields) as cursor:
    for row in cursor:
        primary_value = row[0]
        principal_values = row[1:9]  
        raw_lgcs = row[9]
 
        # explode 'LGCs' into up to 8 values
        lgc_values = [None] * 8
        if raw_lgcs:
            split_lgcs = [x.strip() for x in raw_lgcs.split()]
            for i in range(min(8, len(split_lgcs))):
                lgc_values[i] = split_lgcs[i]
                row[11 + i] = split_lgcs[i]
 
        b5sc_value = row[10]
 
        selected_street = None
        selected_lgc = None
        selected_b7sc = None
 
        # normalize and compare
        if primary_value:
            primary_cleaned = normalize_direction(primary_value)
            primary_prefix = primary_cleaned[:6]
 
            for i in reversed(range(8)):
                principal = principal_values[i]
                if principal:
                    principal_upper = normalize_direction(principal)
 
                    # skip bridge/underpass variants unless overridden
                    if re.search(r'\b(OV|OVR|OVER|OVERPASS|UNDR|UNDER|UNDERPASS)\b', principal_upper):
                        continue
 
                    principal_prefix = principal_upper[:6]
                    if primary_prefix == principal_prefix:
                        selected_street = principal
                        selected_lgc = lgc_values[i]
                        break
 
        # build B7SC
        if b5sc_value and selected_lgc:
            selected_b7sc = str(b5sc_value) + str(selected_lgc)
 
        # update row fields
        row[-3] = selected_street
        row[-2] = selected_lgc
        row[-1] = selected_b7sc
        cursor.updateRow(row)
 
# script ended
print("Script Ended!")
 
 
