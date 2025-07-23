"""
Script Description:
---------------------
This script processes multiple datasets (RRM, SIPs, WorkOrders2024, WorkOrders2025)
from the asset management system, including:
1. Creating temporary copies of input datasets.
2. Adding or updating necessary fields.
3. Concatenating field values.
4. Exporting the processed datasets and merging them.
5. Dissolving the merged datasets by a specified field ("segIDN") with concatenated values.
6. Applying symbology and labeling to the dissolved layer.
7. Renaming the layer.
 
~ In order to ensure proper execution, make sure to enter the correct file in the designated user parameter (RRM, SIPs, WorkOrders2024, WorkOrders2025).
 
~ Ensure field names within each file is consistent.
 
~ Common error messages, such as 'Cannot acquire a lock,' may occur. In such cases, verify that the input or output geodatabase (GDB) has the correct lock permissions. If one GDB fails to operate, try using a different one.
 
~ The KML export will need to be made manually as the LayerToKML tool doesn't always preserve all symbology settings (like line color or thickness), especially when they're set programmatically.
 
"""
import arcpy
import os
import re
import datetime
import time
 
# Set up the workspace
arcpy.env.workspace = r"S:\8. Asset Management\simplified_inspector_map\simplified_no_go\simplified_inspector_map\simplified_inspector_map.gdb"
wksp = arcpy.env.workspace
 
# Overwrite existing output
arcpy.env.overwriteOutput = True
 
# Get the current date and input files from the user
current_date = datetime.datetime.now().strftime("%Y%m%d")
 
# Input parameters
RRM = arcpy.GetParameterAsText(0)
SIPs = arcpy.GetParameterAsText(1)
workorders2024 = arcpy.GetParameterAsText(2)
workorders2025 = arcpy.GetParameterAsText(3)
 
# Define field mappings for each dataset
FIELD_MAPPINGS = {
    "RRM": {
        "Project_statuses": ["sa_current", "NOCend"],
        "Project_locations": ["sa_current", "locdes"],
        "Project_numbers": ["sa_current"],
    },
    "SIPs": {
        "Project_statuses": ["pid", "status"],
        "Project_locations": ["pid", "pjct_name"],
        "Project_numbers": ["pid"],
    },
    "WorkOrders2025": {
        "Project_statuses": ["Work_Order", "Date_Installed_Text"],
        "Project_locations": ["Work_Order", "OFT"],
        "Project_numbers": ["Work_Order"],
    },
    "WorkOrders2024": {
        "Project_statuses": ["Work_Order", "Date_Billed_Text"],
        "Project_locations": ["Work_Order", "OFT"],
        "Project_numbers": ["Work_Order"],
    }
}
 
# Static string mappings
static_strings = {
    "RRM": {"Project_statuses": " NOC rec'd: "},
    "SIPs": {"Project_statuses": "SIP no. "},
    "WorkOrders2025": {"Project_statuses": " installing: "},
    "WorkOrders2024": {"Project_statuses": " billing: "},
}
 
# Function to create required fields if they don't exist
def create_fields(feature_class):
    fields = [f.name for f in arcpy.ListFields(feature_class)]
    if "Project_statuses" not in fields:
        arcpy.management.AddField(feature_class, "Project_statuses", "TEXT")
    if "Project_locations" not in fields:
        arcpy.management.AddField(feature_class, "Project_locations", "TEXT")
    if "Project_numbers" not in fields:
        arcpy.management.AddField(feature_class, "Project_numbers", "TEXT")
 
# Create copies of the input datasets and temporary datasets
input_datasets = {
    "RRM": RRM,
    "SIPs": SIPs,
    "WorkOrders2025": workorders2025,
    "WorkOrders2024": workorders2024
}
 
temp_datasets = {}
for name, dataset in input_datasets.items():
    temp_name = f"{name}_temp"
    temp_path = os.path.join(wksp, temp_name)
    print(f"Creating copy of {name} as {temp_name}...")
    arcpy.management.CopyFeatures(dataset, temp_path)
    temp_datasets[name] = temp_path
    time.sleep(2)  # Small delay to ensure copy completes
 
# Process each copied dataset sequentially
for dataset_name, dataset in temp_datasets.items():
    print(f"Processing dataset: {dataset}")
   
    fields_in_dataset = [f.name for f in arcpy.ListFields(dataset)]
    create_fields(dataset)
   
    # Determine the correct mappings and static strings for this dataset
    mapping = FIELD_MAPPINGS[dataset_name]
    static = static_strings[dataset_name]
 
    # Define the fields you want to use in your cursor
    cursor_fields = ['Project_statuses', 'Project_locations', 'Project_numbers'] + \
                    mapping['Project_statuses'] + mapping['Project_locations'] + mapping['Project_numbers']
   
    # Run UpdateCursor for each dataset to modify fields
    with arcpy.da.UpdateCursor(dataset, cursor_fields) as cursor:
        row_count = 0
        for row in cursor:
            row_count += 1
           
            for field, fields in mapping.items():
                field_index = cursor_fields.index(field)
           
                concatenated_value = ""
               
                if field == "Project_locations":
                    if dataset_name == "RRM":
                        concatenated_value = f"{row[cursor_fields.index('sa_current')] or ''} {row[cursor_fields.index('locdes')] or ''}".strip()
                    elif dataset_name == "SIPs":
                        concatenated_value = f"{row[cursor_fields.index('pid')] or ''} {row[cursor_fields.index('pjct_name')] or ''}".strip()
                    elif dataset_name == "WorkOrders2025":
                        concatenated_value = f"{row[cursor_fields.index('Work_Order')] or ''} {row[cursor_fields.index('OFT')] or ''}".strip()
                    elif dataset_name == "WorkOrders2024":
                        concatenated_value = f"{row[cursor_fields.index('Work_Order')] or ''} {row[cursor_fields.index('OFT')] or ''}".strip()
                else:
                    for field_entry in fields:
                        field_value = row[cursor_fields.index(field_entry)]
                        if field_value is not None:
                            concatenated_value += f"{field_value} "
               
                if dataset_name == "SIPs" and field in static:
                    concatenated_value = static[field] + concatenated_value.strip()
                elif field in static:
                    parts = concatenated_value.strip().split(" ")
                    concatenated_value = f"{parts[0]} {static[field]} {' '.join(parts[1:])}" if parts else ""
 
                concatenated_value = re.sub(r'<.*?>', '', concatenated_value)
                row[field_index] = concatenated_value.strip()
               
            cursor.updateRow(row)
 
    print(f"Finished processing {dataset} with UpdateCursor.")
    time.sleep(2)  # Add a small delay after processing each dataset to avoid index out of bound errors (can be omitted)
 
# Export all copied datasets using CopyFeatures
output_gdb = r"S:\8. Asset Management\simplified_inspector_map\simplified_no_go\simplified_inspector_map\simplified_inspector_map.gdb"
exported_datasets = {}
for dataset_name, dataset_path in temp_datasets.items():
    print(f"Exporting dataset: {dataset_name}")
    output_path = f"{output_gdb}/{dataset_name}_exported_{current_date}"
    arcpy.management.CopyFeatures(dataset_path, output_path)
    exported_datasets[dataset_name] = output_path
    print(f"{dataset_name} exported successfully.")
    time.sleep(2)
 
# Merge the exported datasets
merged_output = f"{output_gdb}/merged_file_{current_date}"
merged_files = [exported_datasets[name] for name in temp_datasets.keys()]
 
print("Merging exported files...")
arcpy.management.Merge(merged_files, merged_output)
print("Merge completed.")
time.sleep(2)
 
# Dissolve the merged file on "segIDN"
dissolved_output = f"{output_gdb}/dissolved_file_{current_date}"
arcpy.management.Dissolve(
    in_features=merged_output,
    out_feature_class=dissolved_output,
    dissolve_field="segIDN",
    statistics_fields=[
        ["Project_statuses", "CONCATENATE"],
        ["Project_locations", "CONCATENATE"],
        ["Project_numbers", "CONCATENATE"],
        ["BORO", "FIRST"]
    ],
    multi_part="SINGLE_PART",
    unsplit_lines="DISSOLVE_LINES",
    concatenation_separator="; "
)
 
print("Dissolve completed.")  
 
# Apply symbology and add layer to map
dissolved_layer_name = "Dissolved_Layer"
arcpy.management.MakeFeatureLayer(dissolved_output, dissolved_layer_name)
 
# Access the current ArcGIS Pro project and map
project = arcpy.mp.ArcGISProject("CURRENT")
mymap = project.listMaps()[0]  # Get the first map in the project
 
# Create a feature layer from the dissolved output
dissolved_layer = arcpy.management.MakeFeatureLayer(dissolved_output, dissolved_layer_name).getOutput(0)
mymap.addLayer(dissolved_layer, "TOP")
 
merged_layer = mymap.listLayers(dissolved_layer_name)[0]
print(f"Layer added to map: {merged_layer.name}")  # Debug to confirm
 
# Symbolize lines as Black (R0 G0 B0) and size 6 points
if hasattr(merged_layer.symbology, 'renderer'):
    sym = merged_layer.symbology
    sym.renderer.symbol.color = {'RGB': [0, 0, 0]}
    sym.renderer.symbol.size = 6  
    merged_layer.symbology = sym
 
merged_layer.showLabels = True
label_class = merged_layer.listLabelClasses()[0]
label_class.visible = True  
label_class.expression = '[Project_numbers]'
 
# Rename the layer
new_name = f"BLACK = refurb_M_{current_date}_do_not_write_WO"
merged_layer.name = new_name
print(f"Layer renamed to: {merged_layer.name}")  # Debug to confirm
 
