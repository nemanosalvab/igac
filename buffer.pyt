# -*- coding: utf-8 -*-

import arcpy
import os
import shutil


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object): 
  
  def __init__(self):
    """Define the tool (tools name is the name of the clases)."""   
    self.label = "Tool" 
    self.descripcion = "Tool" 
    self.canRunInBackground = False
  
  def getParameterInfo(self):
    """Define parameter definitions"""
    params = [
      arcpy.Parameter(displayName="Input shapefile",
                      name="input_feature_class",
                      datatype="DEShapeFile",
                      parameterType="Required",
                      direction="Input"),
      arcpy.Parameter(displayName="point FID for buffer selection",
                      name="input_fid_shapefileinput",
                      datatype="GPDouble",
                      parameterType="Required",
                      direction="Input"),
      arcpy.Parameter(displayName="Input coincidence percent",
                      name="input_coincidence_percent",
                      datatype="GPDouble",
                      parameterType="Required",
                      direction="Input"),
      
      arcpy.Parameter(displayName="Input buffer radius",
                      name="input_buffer_radius",
                      datatype="GPDouble",
                      parameterType="Required",
                      direction="Input"),
      
      arcpy.Parameter(displayName="Output folder",
                      name="output_folder",
                      datatype="DEFolder",
                      parameterType="Required",
                      direction="Input")
    ]
    return params
  
  def isLicensed(self):
    """Set whether tools is licensed to execute."""   
    return True
  
  def execute(self, parameters, messages):
      # Call the function to compare fields within the buffer and create the output shapefile

      # Input shp file
      shapefile_path = parameters[0].valueAsText
      fit_input= parameters[1].value
     
      # Spatial reference set to GCS_WGS_1984
      spatial_reference = arcpy.SpatialReference(9377)

      field_to_compare1 = "NOMBRE_GEO"
      field_to_compare2 = "ngnoficial"

      coincidence_percent = float(parameters[2].value)
      buffer_radius = float(parameters[3].value)  # Assuming the parameter is a numeric input
      output_shapefile = parameters[4].valueAsText
      self.compare_fields_within_buffer(shapefile_path, fit_input, field_to_compare1, field_to_compare2, coincidence_percent,buffer_radius, output_shapefile)
      arcpy.AddMessage("Success execute")  
  
  def make_folder(self,folders, output_shapefile):
    for folder in folders:
        try:
            path = os.path.join(output_shapefile, folder) 
            if os.path.isdir(path):
                shutil.rmtree(path)
                os.mkdir(path) 
            else: os.mkdir(path) 
            #self.delete_files_in_directory(path)
        except OSError:
            print("Error occurred while make folder.")


  def compare_fields_within_buffer(self, shapefile, fid, field1, field2, coincidence_percent,buffer_radius, output_shapefile):
      self.make_folder(['tmp', 'result'], output_shapefile)
      # Create a feature layer from the feature class
      arcpy.management.MakeFeatureLayer(shapefile, "point_layer")    
      sql_query = f"FID = {fid}"
      arcpy.management.SelectLayerByAttribute("point_layer", "NEW_SELECTION", sql_query)
      arcpy.management.CopyFeatures("point_layer", output_shapefile+"\\tmp\\salida.shp")
      arcpy.analysis.Buffer(output_shapefile+"\\tmp\\salida.shp", output_shapefile+"\\tmp\\buffer.shp", buffer_radius)
      arcpy.management.MakeFeatureLayer(shapefile, "intersect_point_layer")  
      arcpy.management.SelectLayerByLocation("intersect_point_layer", 'INTERSECT', output_shapefile+"\\tmp\\buffer.shp")
      arcpy.management.CopyFeatures("intersect_point_layer", output_shapefile+"\\tmp\\final.shp")

      # Create a list to store selected feature geometries
      selected_features = []
      #fields = ['SHAPE@XY', field1, field2 ]
      fields = ['SHAPE@',field1, field2 ]

      with arcpy.da.SearchCursor(output_shapefile+"\\tmp\\final.shp", fields) as cursor:
          for row in cursor:
              feature_geometry, field1_value, field2_value  = row[0], row[1], row[2]

              # Calculate the similarity score (coincidence percentage) between the two text values
              similarity_score = self.similarity(field1_value, field2_value)

              # Compare the similarity score with the user-defined coincidence percentage
              if similarity_score > coincidence_percent:selected_features.append(feature_geometry)

      # Create a new shapefile with the selected features
      if len(selected_features)>0:arcpy.management.CopyFeatures(selected_features, output_shapefile+"\\result\\coincidencia.shp")
      else: arcpy.AddMessage("Empty result shapefile") 

  def similarity(self, str1, str2):
      # Function to calculate similarity percentage between two strings
      common_chars = set(str1) & set(str2)
      return (2.0 * len(common_chars)) / (len(str1) + len(str2)) * 100 if (len(str1) + len(str2)) > 0 else 0




