'''
Created on Jan 7, 2015

@author: Joel
'''
#
from glob import glob
from config import Config
from manageData import inventory
#
import os
#
def display_menu(options,title='Menu',desc=None,multi=False):
    """
    Display a menu with from the given options. Individual options will be
     listed on separate lines indexed starting at 1 and incrementing by 1.
     Option number 10 will be indexed with 0. This function is not designed to
     create menues greater than length 10.
    Inputs:
        options <list>
         List of text options.
        title <string>
         Optional menu title.
        desc <string>
         Optional menu description.
        multi <boolean>
         Display panel navigation if set to True. Default False.
    """
    # Display blank line, then menu title.
    print '\n%s' % (title)
    # Print an underline under the title.
    print ''.join(['-' for i in title]) #@UnusedVariable
    # Show a description if one was sent.
    if desc:
        print desc,'\n'
    # Display options with indexes. Should give indexes 1-9 and 0 for index 10.
    print '\n'.join([(str((options.index(i) + 1) % 10) + ': ' + i) for i in\
                     options])
    # Display navigation when applicable.
    if multi:
        print "Enter 'p' for previous page, or 'n' for next page."
    print "Enter the number of your selection, or enter 'e' to quit."
    return
#
def get_date_input(config):
    """
    Finds available dates and presents a menu for the user to make a selection.
    Returns the selected option.
    Inputs:
        config <Config> Config object containing runtime variables.
    Outputs:
        selection <string> The selected date.
    """
    available_dates = inventory.get_available_dates()
    # Create a menu from the available dates options defined above and get user
    #  input. User input will be returned as an index to one of the options.
    option_index = menu(available_dates,title='Please select a date.')
    # Return the selection using the index input by the user.
    return available_dates[option_index]
#
def get_efs_input(config):
    """
    Finds available forecast systems for the date in stored in config. Presents
     a menu for the user to make a selection. Returns the selected option.
    Inputs:
        config <Config> Config object containing runtime variables.
    Outputs:
        selection <string> The selected forecast system.
    """
    available_efs_systems =\
        inventory.get_available_efs_systems(config.model_init_date)
    # Get user input and return selected option.
    option_index = menu(available_efs_systems,
                        title = 'Please select a forecast system.')
    return available_efs_systems[option_index]
#
def get_hour_input(config):
    """
    Finds available initialization times given the date and forecast system
     stored in config. Presents a menu for the user to make a selection.
     Returns the selected forecast initialization time.
    Inputs:
        config <Config> Config object containing runtime variables.
    Outputs:
        selection <string> The selected initialization time.
    """
    available_hours = inventory.get_available_hours(config.model_init_date,
                                                    config.forecast_system)
    # Get user input and return selected option.
    option_index = menu(available_hours,title='Please select a forecast hour.')
    return available_hours[option_index]
#
def get_stations_data_file_input(config):
    """
    Finds available stations data files. Presents a menu for the user to make a
     selection. Returns the selected stations data file name (not the path).
    Inputs:
        config <Config> Config object containing runtime variables.
    Outputs:
        selection <string> The selected stations data file name.
    """
    #
    raw_glob = glob(Config.STATIONS_DATA_STORAGE_PATH + '/*.dat')
    # Loop over items and add to a new list if the item is a file.
    #  Grabs file name without its path.
    available_stations_data_files = [i.split('/')[-1] for i in raw_glob if\
                                     os.path.isfile(i)]
    # Get user input and return selected option.
    option_index = menu(available_stations_data_files,
                        title = 'Please select a stations data file.')
    return available_stations_data_files[option_index]
#
def menu(options,title='Menu',desc=None):
    """
    Generate a menu from a list of options and wait for a selection. After 10
     available options, generate another page of options.
    Inputs:
        options <list> 
         List of options from which to create a menu.
        title <String> 
         Menu title, defaults to 'Menu'
        desc <String> 
         Optional description for the menu
    Outputs:
        selection <int> Index of options item which the user selected.
    """
    # Split options into groups of 10.
    split_options = [options[i:i+10] for i in range(0, len(options), 10)]
    # Start panel index at 0.
    panel_index = 0
    # Keep going until a selection is made or the program terminates.
    while True:
        # Menu title should have page numbers when applicable.
        if len(split_options) > 1:
            menu_title = '%s Page %s of %s' % (title, panel_index + 1,
                                               len(split_options))
        else:
            menu_title = title
        # Display menu with current page of options.
        display_menu(split_options[panel_index], title = menu_title,
                      desc = desc, multi = (len(split_options) > 1))
        raw_selection = raw_input('Input: ')
        # Attempt to cast user input to an integer. Dodge ValueErrors.
        try:
            selection = int(raw_selection)
        except ValueError:
            selection = raw_selection
        # User wants to quit.
        if selection in ['e', 'E']:
            print "Program terminating at user's request."
            print 'PYTHON STOP'
            exit()
        # User wants the next page. This can wrap around.
        elif len(split_options) > 1 and selection in ['n', 'N']:
            if panel_index == len(split_options) - 1:
                panel_index = 0
            else:
                panel_index += 1
        # User wants the previous page. This can wrap around.
        elif len(split_options) > 1 and selection in ['p', 'P']:
            if panel_index == 0:
                panel_index = len(split_options) - 1
            else:
                panel_index -= 1
        # User entered a possible selection.
        elif selection - 1 in range(0,len(split_options[panel_index])):
            if len(split_options[panel_index]) == 10 and selection == 0:
                selection = 10
            return (selection - 1) + (10 * panel_index)
        else:
            print 'Input not recognized, please try again. . .\n'
    #
#
def show(config):
    """
    Entry point of UI process.
    Process:
        -Menu to select a date from available dates.
        -Menu to select a forecast system from avail. systems at selected date.
        -Menu to select an initialization time from available times, given
          previous selections.
        -Eventually: Menu to select a plume type from available plume types.
        -Menu to select a stations data file from available data files.
    Inputs:
        config <Config> Config object which will be configured with UI inputs.
    Outputs:
        No physical outputs. Initializes the Config object.
    """
    # Get the date input and set config.
    input_date = get_date_input(config)
    print 'Selected date:',input_date
    config.set_init_date(input_date)
    # Get the EFS system input and set config.
    input_forecast_system = get_efs_input(config)
    print 'Selected forecast system:',input_forecast_system
    config.set_forecast_system(input_forecast_system)
    # Get the initialization time input and set config.
    input_init_time = get_hour_input(config)
    print 'Selected time:',input_init_time
    config.set_init_hour(input_init_time)
    # Placeholder for plume type selection
    #
    #
    # Get the stations data file input.
    input_stations_data_file_name = get_stations_data_file_input(config)
    print 'Selected stations data file:',input_stations_data_file_name
    config.set_stations_data_file_name(input_stations_data_file_name)
    config.expand()
    return
#
if __name__ == '__main__':
    print 'ui.py is not designed to be run independently.'
    print 'PYTHON STOP'
#
#
#
#
# EOF