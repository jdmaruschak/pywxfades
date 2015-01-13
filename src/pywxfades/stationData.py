'''
Created on Jan 10, 2015

@author: Joel
'''
#
from config import Config #@UnusedImport Used in __init__()
from modelData import ModelData
#
import plumes
#
import numpy
import pygrib #@UnresolvedImport @UnusedImport pygrib not available in windows.
#
class StationData:
    """
    This class will manage data and static information about each station.
    Data storage will be created once it is needed. Storage will be in the form
     of multi-tiered numpy arrays.
    Instance Variables:
     latitude <float>
      Latitude of the station in degrees, range: [-90,90]
     longitude <float>
      Longitude of the station in degrees, range: [-180,180]
     station_name <string>
      Name of the station, i.e. Scranton,PA
     grib_i <int>
      x-coordinate reference from grib lat/lon grid used for accessing data 
       from grib messages.
     grib_j <int>
      y-coordinate reference from grib lat/lon grid used for accessing data 
       from grib messages.
     grib_lat <float>
      Latitude of the nearest grid point from the model.
     grib_lon <float>
      Longitude of the nearest grid point from the model.
     config <Config>
      Config instance holding runtime configuration.
     data <numpy.ndarray>
      Variable containing all data for this station. Indexed in order by plume
       type, data type, model name, forecast time.
    """
    # Instances of this class will be added to a list for later iteration.
    instances = []
    #
    def __init__(self,lat,lon,name,config):
        """
        Instantiate the StationData object with the given latitude and
         longitude. Grib coordinates and access indexes will be set when the
         first grib file is opened.
        """
        self.latitude = lat
        self.longitude = lon
        self.station_name = name
        self.grib_i = None
        self.grib_j = None
        self.grib_lat = None
        self.grib_lon = None
        self.config = config
        # Initialize storage.
        self.data = []
        # Extremely convoluted definitions involving appending empty lists at
        #  each step. This will all be converted to a numpy array and accessed
        #  via indexes in config.
        for plume in plumes.describe.PLUMES:
            plume_name = plume[0]
            self.data.append([])
            for data_type in plume[1]:
                self.data[self.config.indexes[plume_name]].append([])
                for model in ModelData.member_names:
                    self.data[self.config.indexes[plume_name]][self.config.indexes[data_type]].append([])
                    for time in range(0,config.num_forecasts): #@UnusedVariable
                        # time required for loop syntax.
                        if data_type == 'tp':
                            self.data[self.config.indexes[plume_name]][self.config.indexes[data_type]][self.config.indexes[model]].append(0.0)
                        else:
                            self.data[self.config.indexes[plume_name]][self.config.indexes[data_type]][self.config.indexes[model]].append(0)
        # Convert to a powerful numpy array.
        self.data = numpy.array(self.data)
        # Add this object to the list of StationData objects.
        StationData.instances.append(self)
    #
    def add_data(self,plume,model,message):
        """
        Add data to memory for this station.
        """
        value = message.values[self.grib_i, self.grib_j]
        fcst_time = message.forecastTime
        fcst_index = fcst_time / self.config.model_fcst_interval
        parameter = message.shortName
        # Extra processing needed if data is precipitation amount.
        if parameter == 'tp':
            # Do not enter total precipitation to forecast hour.
            if message.endStep - message.startStep == self.config.model_fcst_interval:
                # Convert mm to inches.
                value = value * 0.0393701
                # Correct negative values to 0.
                if value < 0:
                    value = 0
                    print 'Warning: Negative value in precipitation data: %s %s time %s val %s\n' % (model,parameter,str(fcst_index + 1), str(value))
                # Remove very small values < 0.001 inches. These pop in from
                #  time to time due to the conversion from mm to inches.
                if value < 0.001 and value > 0.0:
                    value = 0
                    print 'Warning: Tiny value in precipitation data: %s %s time %s val %s\n' % (model,parameter,str(fcst_index + 1), str(value))
        # Set the data value in station memory.
        self.data[self.config.indexes[plume]][self.config.indexes[parameter]][self.config.indexes[model]][fcst_index] = value
    #
    @staticmethod
    def populate_grid_information(message,config):
        """
        Converges on i,j coordinates using numpy array differences of lats/lons.
        Uses existing StationData objects, finds closest grid point based on
         latitude and longitude differences.
        Inputs:
            message <pygrib.gribmessage>
             Arbitrary grib message from which to pull lats and lons.
        Outputs:
            No physical outputs.
            Sets instance variables of all StationData objects.
        """
        # Extract lats and lons from the grib message.
        lats,lons = message.latlons()
        # Display information if under test mode.
        if config.test:
            print 'LATS:'
            print lats
            print 'LONS:'
            print lons
        # Loop over StationData objects. Find i and j points and set instance
        #  variables.
        for station in StationData.instances:
            lat = station.latitude
            lon = station.longitude
            # Correct to a 360 degree grid if using GEFS system.
            if config.forecast_system == 'gefs':
                lon = lon + 360
            # Perform the difference on all cells in the array. Powerful numpy.
            lat_diff,lon_diff = abs(lats-lat),abs(lons-lon)
            # Get the minimum total difference. The closest point in latitude
            #  may not be the closest point also in longitude. Add the
            #  difference arrays to find a total displacement.
            diffs = numpy.add(lat_diff,lon_diff)
            #==================================================================
            # The quirky argmin function:
            # The argmin function returns the linear index of the cell with the
            #  minimum value. Because this is difficult to visualize, convert
            #  to an x- and y-coordinate system. This is done by using the
            #  integer division and modulus operators.
            #  Example:
            #  Imagine a 10x10 grid (100 total values). Assume you want to
            #   access the 15th cell (actually cell 14 due to the zero-base).
            #   Cell 14 is on the second row from the top (row 1, top being
            #   row 0), and the 5th cell from the left (cell 4, left-most being
            #   cell 0). Integer division by the number of columns will yield
            #   a value of 1. The modulus with the same parameters will yield
            #   a value of 4. Access that cell with array_name[1][4]. This
            #   argument does not work for a 1-based system.
            #==================================================================
            # Set instance variables.
            station.grib_i = diffs.argmin()/diffs.shape[1]
            station.grib_j = diffs.argmin()%diffs.shape[1]
            station.grib_lat = lats[station.grib_i][station.grib_j]
            station.grib_lon = lons[station.grib_i][station.grib_j]
        return
    #
# End Class StationData
#
if __name__ == '__main__':
    print 'stationData.py is not designed to be run independently.'
    print 'PYTHON STOP'
#
#
#
#
# EOF