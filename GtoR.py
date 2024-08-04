import arcpy
import os
 
# Set workspace
arcpy.env.workspace = r"S:\8. Asset Management\gis_Help"
wksp = arcpy.env.workspace
 
# Enable overwriting of existing outputs to avoid errors during script execution
arcpy.env.overwriteOutput = True
 
# Define input tables and layers, including pwms_file, lion_file, and the table
pwms_file = arcpy.GetParameterAsText(0)  # User-defined PWMS feature class
lion_file = arcpy.GetParameterAsText(1)  # User-defined Lion feature class
rb2_table = arcpy.GetParameterAsText(2)  # User-defined RB2 table
 
try:
    # Create a feature layer from the PWMS feature class
    arcpy.management.MakeFeatureLayer(pwms_file, "pwms_layer")
    print("Feature layer 'pwms_layer' created from 'pwms_file'.")
 
    # Step 1: Perform a join operation between the PWMS feature layer and the Lion feature layer based on the 'SegmentID' field
    arcpy.management.AddJoin("pwms_layer", "SegmentID", lion_file, "SegmentID")
    print("Step 1: Join operation completed between 'pwms_layer' and 'lion_file' on 'SegmentID'.")
 
    # Step 2: Select segments from the 'pwms_layer' where the 'RB_Layer' field equals 'G'
    arcpy.management.SelectLayerByAttribute("pwms_layer", "NEW_SELECTION", "RB_Layer = 'G'")
    print("Step 2: Segments with 'RB_Layer' = 'G' selected from 'pwms_layer'.")
 
    # Step 3: Export the selected segments to a new feature class
    output_feature_class = os.path.join(arcpy.env.workspace, "pwms_layer_CopyFeatures")
    arcpy.management.CopyFeatures("pwms_layer", output_feature_class)
    print(f"Step 3: Selected segments exported to a new feature class at {output_feature_class}.")
 
    # Step 4: Join the RB2 table to the previously exported feature class based on the appropriate fields
    arcpy.management.AddJoin(rb2_table, "SegmentIDG", "pwms_layer_CopyFeatures", "segIDInt", "KEEP_COMMON")
    print("Step 4: A join was performed between rb2_table and pwms_layer_CopyFeatures...")
   
    # Step 5: Export the rows from the RB2 table to a new table in the geodatabase
    joined_features_path = os.path.join(wksp, "joined_RB2_segments")
    arcpy.management.CopyRows(rb2_table, joined_features_path)
    print(f"Step 5: Joined data exported to table at {joined_features_path}.")
 
    # Clean up by deleting unnecessary fields from the joined RB2 segments table
    fields_to_delete = ["SegmentIDG", "RPC", "NCI", "R_FrNd", "G_FrNd", "R_ToNd", "G_ToNd"]
    arcpy.management.DeleteField(joined_features_path, fields_to_delete)
    print(f"Unnecessary fields {fields_to_delete} deleted from 'joined_RB2_segments'.")
 
    # Step 6: Create a table view from the joined RB2 segments table and perform a join with the Lion feature layer
    arcpy.management.MakeTableView(os.path.join(wksp, "joined_RB2_segments"), "joined_view")  # Create a table view
    arcpy.management.AddJoin(lion_file, "SegmentIDN", "joined_view", "SegmentIDR", "KEEP_COMMON")
    print("Step 6: Join operation completed between 'lion_file' and 'joined_RB2_segments' on 'SegmentIDN' and 'SegmentIDR'.")
 
    # Delete unnecessary fields from Lion
    arcpy.management.DeleteField(lion_file, ["RB_Layer", "SegIDInt"])
    print("RB_Layer and SegIDInt deleted from lion_file ...")
 
    # Rename the SegmentIDR field to SegmentIDN
    arcpy.management.AlterField(lion_file, "SegmentIDR", "SegmentIDN")
    print("SegmentIDR renamed to SegmentIDN in lion_file ...")
 
    # Append or merge R segments into the original export (pwms)
    Merge = "Final_Merged"
    arcpy.management.Merge([lion_file, pwms_file], os.path.join(wksp, Merge))
    print("Script execution completed.")
 
except arcpy.ExecuteError:
    print(arcpy.GetMessages())
except Exception as e:
    print(e)
 
