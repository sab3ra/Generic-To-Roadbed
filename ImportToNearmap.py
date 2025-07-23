# -------------------------------------- IMPORT MODULES ---------------------------------
import arcpy
 
# ------------------------------- SET THE WORKSPACE ---------------------------------------
arcpy.env.workspace = r"S:\8. Asset Management\convert_files_to_import_into_nearmap\nearmap.gdb"
wksp = arcpy.env.workspace
 
#------------------------------- OVERWRITE EXISTING OUTPUT --------------------------------
arcpy.env.overwriteOutput = True
 
# ------------------------------- DEFINE USER INPUT VARIABLES -----------------------------------
#
# these are entered by the user in the parameter dialog box of the ArcGIS toolbox
#line_file is the file to process and convert to kmz
#
line_file = arcpy.GetParameterAsText(0)
line_field = arcpy.GetParameterAsText(1)
weekly_date = arcpy.GetParameterAsText(2)
data_type = arcpy.GetParameterAsText(3)
#
#
# ---------------------------- WRAP ALL IN A FOR LOOP OF BORO NAMES ----------------------------
#boro_list = ["Manhattan", "The Bronx"]
boro_list = ["Manhattan", "The Bronx", "Staten Island", "Brooklyn", "Queens"]
#boro_list = ["M","X", "S", "B", "Q"]
 
counter = 1
 
for value in boro_list:
    print("Processing borough:", value)  # Print the current borough being processed
   
    # ----------------------------------- SELECT BORO ----------------------------------------------
    # boro is cycling through boro_list in the above for loop
    print("selecting boro ....")
    boro = "BoroName = '{}'".format(value)
    q = str(boro)
    print("Boro selection query:", q)  # Print the selection query for the current borough
    arcpy.MakeFeatureLayer_management(wksp+"/FC_nybb", "boro_lyr")
    arcpy.SelectLayerByAttribute_management("boro_lyr", "NEW_SELECTION", q)
 
    # ------------------------------------ SELECT LINES WITHIN SELECTED BORO -----------------------
    # line_file is user input, here defined as FC_resurfacing
    print("selecting lines ....")
    arcpy.MakeFeatureLayer_management(line_file, "line_file_lyr")
    arcpy.SelectLayerByLocation_management("line_file_lyr", "HAVE_THEIR_CENTER_IN", "boro_lyr")
 
    # ------------------------------------- DISSOLVE ON A FIELD ------------------------------------------
    # input is a feature layer
    # output is a feature class in the workspace
    print("dissolving ...")
    arcpy.Dissolve_management("line_file_lyr", wksp+"/FC_line_dslv", line_field)
 
    # ------------------------------------ BUFFER DISSOLVED LINES ---------------------------------------
    # input is a feature layer
    # output is a feature class in the workspace
    # buffer is 5 feet
    # buffers are dissolved on the same dissolve field (this may not be necessary since multipart was allowed in dissolve step)
    # buffer sizes:  resurfacing 10 ft, WO 15 ft, SIPs 20 ft, refurb list 25 ft
    print("buffering ...")
    arcpy.MakeFeatureLayer_management(wksp+"/FC_line_dslv", "line_dslv_lyr")
    buffer_output = wksp + "/FC_line_dslv_buf15_" + value.replace(" ", "")  # Unique output name per borough
    arcpy.Buffer_analysis("line_dslv_lyr", buffer_output, "10 Feet", "", "", "LIST", line_field, "PLANAR")
 
    # ----------- JOIN LINE_FILE TO BUFFERS FILE ON DISSOLVE FIELD AND COPY IN FIELDS -----------------
    print("joining feature classes - input lines to buffers - and copying in fields ...")
    inFeatures = buffer_output
    joinField = line_field
    joinTable = line_file
    arcpy.management.JoinField(inFeatures, joinField, joinTable, joinField)
 
    # -------------------------- RENAME BUFFER FILE BY ADDING BORO AND DATE ----------------------------------
    print("Borough:", value)
    if value == "Manhattan":
        borough = "MN"
    elif value == "The Bronx":
        borough = "BX"
    elif value == "Staten Island":
        borough = "SI"
    elif value == "Brooklyn":
        borough = "BK"
    elif value == "Queens":
        borough = "QN"
    else:
        raise RuntimeError("Unknown borough {}".format(value))
    print("Borough abbreviation:", borough)
    outFeatures = 'line_buffers_2024_' + data_type + '_' + borough + '_' + weekly_date + '_update_' + str(counter)
    arcpy.MakeFeatureLayer_management(inFeatures, "line_dslv_buf5_lyr")
    arcpy.management.CopyFeatures("line_dslv_buf5_lyr", outFeatures)
 
    # ---------------------------------- END ---------------------------------------------------------------
    print(" Does the buffer file exist?  ")
    print((arcpy.Exists(outFeatures)))
    FC = arcpy.ListFeatureClasses()
    print("feature classes in nearmap.gdb are:  ")
    for contents in FC:
        print (contents)
 
    counter += 1
 
print ('Script ended')
