import collections
import arcpy
import locale
locale.setlocale(locale.LC_ALL, '')
def field_checker(from_field_type, to_field_type, delimiter):
    """A function to check for correct field types between the from and to fields."""
    if from_field_type == "String":
        if not to_field_type == "String":
            arcpy.AddError("Copy To Field must be of type text when Read From Field is of type text.")
    else:
        if not to_field_type == "String":
            if delimiter != "":
                arcpy.AddError("Copy To Field must be of type text when Read From Field is of type numeric or date and you are using a delimiter.")
            if delimiter == "":
                if from_field_type == "SmallInteger":
                    if not to_field_type in ["Integer",  "SmallInteger", "Float", "Double"]:
                        if to_field_type == "Date":
                            arcpy.AddError("Copy To Field must be of type text.")
                if from_field_type == "Integer":
                    if to_field_type in ["SmallInteger", "Integer", "Float", "Double", "Date"]:
                        arcpy.AddError("Copy To Field must be of type text.")
                else:
                    if from_field_type in ["Float", "Double" , "Date"]:
                        if to_field_type in ["Integer", "SmallInteger", "Float", "Double" , "Date"]:
                            arcpy.AddError("Copy To Field must be of type text.")
# End field_checker function
def concatenate(input_table, case_field, from_field, to_field, delimiter='', *args):
    """Function to concatenate row values."""
    # Get field types for from and to fields
    from_field_type = arcpy.ListFields(input_table, from_field)[0].type
    to_field_length = 500
    # Alter the length of the destination field to 500
    arcpy.management.AlterField(input_table, to_field, field_length=to_field_length)
    # Group a sequence of case field ID's and value pairs into a dictionary of lists.
    dictionary = collections.defaultdict(list)
    try:
        srows = None
        srows = arcpy.SearchCursor(input_table, '', '', '', '{0} A;{1} A'.format(case_field, from_field))
        for row in srows:
            case_id = row.getValue(case_field)
            value = row.getValue(from_field)
            if from_field in ['Double', 'Float']:
                value = locale.format('%s', (row.getValue(from_field)))
            if value is not None:  # Changed from 'if value <> None:' to 'if value is not None:'
                dictionary[case_id].append(value)
    except RuntimeError as re:
        arcpy.AddError('Error in accessing {0}. {1}'.format(input_table, re.args[0]))
    finally:
        if srows:
            del srows
    try:
        urows = None
        urows = arcpy.UpdateCursor(input_table)
        for row in urows:
            case_id = row.getValue(case_field)
            values = dictionary[case_id]
            f = ''.join(str(val) for val in values)  # Removed the use of 'unicode' function
            print("content length:", len(f))
            # Check if the length of the concatenated content exceeds the field length
            if len(f) > to_field_length:
                arcpy.AddError('Length of the Copy to Field is less than the length of the content you are trying to copy.')
            else:
                # Concatenate values and update the destination field
 
                if from_field_type == 'String':
                   
                    row.setValue(to_field, delimiter.join(sorted(set([val for val in values if val is not None]))))
                else:
                    row.setValue(to_field, delimiter.join(sorted(set([str(val) for val in values if val is not None]))))
            urows.updateRow(row)
    except RuntimeError as re:
        arcpy.AddError('Error updating {0}. {1}'.format(input_table, re.args[0]))
    finally:
        if urows:
            del urows
    # If you are using the tool in ModelBuilder, set the derived output parameter to the value
    # of input table so that it is not empty and can be used with other tools.
    arcpy.SetParameterAsText(4, str(input_table))
# End concatenate function
if __name__ == '__main__':
    argv = tuple(arcpy.GetParameterAsText(i)
             for i in range(arcpy.GetArgumentCount()))
    concatenate(*argv)
