import arcpy
import os
from datetime import datetime
 
arcpy.env.overwriteOutput = True
 
input = r'S:\8. Asset Management\marking_condition\condition_by_factor\marking_condition\marking_condition.gdb\Crosswalks_data'
output = r'S:\8. Asset Management\marking_condition\condition_by_factor\marking_condition\marking_condition.gdb\refurb_counts_by_node'
 
 
if arcpy.Exists(output):
    arcpy.management.Delete(output)
 
out_path = os.path.dirname(output)
out_name = os.path.basename(output)
 
arcpy.management.CreateTable(out_path=out_path, out_name=out_name)
 
 
 
arcpy.management.AddField(output, "NodeID_Direction", "TEXT", field_length=50)
arcpy.management.AddField(output, "Start_GL_Date", "DATE")
arcpy.management.AddField(output, "End_GL_Date", "DATE")
arcpy.management.AddField(output, "Refurb_Count", "LONG")
arcpy.management.AddField(output, "fragmented", "TEXT", field_length=20)
arcpy.management.AddField(output, "SegmentID", "TEXT", field_length=50)
 
# helpr function to classify work order types
def classify_workorder(prefix):
    if prefix == "GL":
        return "GL"
    elif prefix in ("RM", "LL"):
        return "Refurb"
    else:
        return "Other"
 
# read all rows into a list (to group by nodedir)
rows = []
with arcpy.da.SearchCursor(input, ["NodeDir", "Installation_Date", "Prefix", "SegmentID", "fragmented"]) as cursor:
    for r in cursor:
        join_field = r[0]
        # convrt to datetime
        if r[1] is None:
            continue  # Skip rows with no date
        elif isinstance(r[1], datetime):
            inst_date = r[1]
        else:
            inst_date = datetime.strptime(r[1], '%d-%b-%y')
 
        prefix = r[2]
        segment = r[3]
        aadt = r[4]
 
 
        rows.append({
            "NodeDir": join_field,
            "Installation_Date": inst_date,
            "SegmentID": segment,
            "fragmented": aadt,
            "Work_Type": classify_workorder(prefix)
        })
 
# sort rows by nodedir and Installation_Date
rows.sort(key=lambda x: (x["NodeDir"], x["Installation_Date"]))
 
print(f"Total rows read: {len(rows)}")
 
gl_total = sum(1 for r in rows if r["Work_Type"] == "GL")
print(f"Total GL rows: {gl_total}")
 
group_keys = set(r["NodeDir"] for r in rows)
print(f"Total unique NodeDir groups: {len(group_keys)}")
 
# Check how many groups have at least 2 GL rows:
from collections import Counter
 
group_gl_counts = Counter()
for key, group_rows in groupby(rows, key=lambda x: x["NodeDir"]):
    group_list = list(group_rows)
    gl_dates = sorted(set(
    row["Installation_Date"]
    for row in group_list
    if row["Work_Type"] == "GL"
))
    group_gl_counts[key] = len(gl_indices)
 
groups_with_2plus_gl = [k for k,v in group_gl_counts.items() if v >= 2]
print(f"Groups with at least 2 GL orders: {len(groups_with_2plus_gl)}")
print(f"Sample groups with 2+ GL: {groups_with_2plus_gl[:5]}")
 
# group rows by Join_Field_WO
from itertools import groupby
 
with arcpy.da.InsertCursor(output, ["NodeID_Direction", "Start_GL_Date", "End_GL_Date", "Refurb_Count", "fragmented", "SegmentID"]) as insert_cursor:
    for key, group_rows in groupby(rows, key=lambda x: x["NodeDir"]):
        group_list = list(group_rows)
        # get the indices of GL orders
        gl_indices = [i for i, row in enumerate(group_list) if row["Work_Type"] == "GL"]
       
        if len(gl_indices) < 2:
            # not enough GL orders to form an interval
            continue
       
        # loop over GL intervals
        for i in range(len(gl_indices) - 1):
            start_idx = gl_indices[i]
            end_idx = gl_indices[i + 1]
            start_row = group_list[start_idx]
            end_row = group_list[end_idx]
           
            # count refurbishments between GLs
            refurb_count = sum(1 for r in group_list[start_idx + 1:end_idx] if r["Work_Type"] == "Refurb")
           
            insert_cursor.insertRow([
                key,                           # NodeID_Direction
                start_row["Installation_Date"], # Start_GL_Date
                end_row["Installation_Date"],   # End_GL_Date
                refurb_count,
                start_row["fragmented"],
                start_row["SegmentID"]
            ])
 
print("Refurbishment counts between GL intervals created successfully.")
