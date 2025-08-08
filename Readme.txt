-----------------
CTD Batch Processor ReadMe
-----------------
V1.0.0-beta.1

submit bug reports to https://github.com/bkclarke/ctd_processing/issues

This software was developed as a front-end GUI for batch processing CTD data using the SBE Data Processing application.  The base language is python, using the Tkinter library for GUI development.  This application does no actual processing of data, rather calls upon SBE data processing modules to do so, bypassing the need for a batch file.  

This application references a folder location containing the users .psa files associated with executables to be run.  The path to the seabird executables must be entered correctly.  The default path is:

C:/Program Files (x86)/Sea-Bird/SBEDataProcessing-Win32 but may differ based on your install.

Once the .psa directory is chosen, all .psa extension files will populate in the GUI window. Once the seabird executable directory is chosen, dropdowns allow the user to select which module to run for each .psa. 

To reduce effort, the user can save the configuration which saves input files and directories, configuration of processing order, and enabled/disabled settings for each executable.

-----------------
Running the software
-----------------
copy the CTD_batch_gui folder to a local directory.  

In the main directory, open ctd_batch_application.

If no configuration was found, either load a configuration, or select the 3 paths to directories (.psa files, executables, output file directory). Select 'save configuration' to save for next time. 

The .psa files will populate once the directory is selected.  Match the .psa to the appropriate executable and choose which order you want to run them, and which modules should be run. 

Choose 1 or more raw .hex file to run.

Select process data.  Files will be processed in series.  

-----------------
dependencies 
-----------------

While Python and associated libraries are cross platform capable, SBE Data Processing is not.  This application will only work on OS's capable of running SBE Data Processing.

Python language and associated libraries do not need to be downloaded to run this application. 

SBE data processing modules must be correctly configured for seamless data processing.

The following .exe modules have been tested:

DatcnvW.exe
-processing script used raw .hex file path as input, output file directory as output file location.  All other modules use the output file directory as both the input and output. 

AlignCTDW.exe

FilterW.exe

CellTMW.exe

DeriveW.exe 
-.psa configuration must uncheck 'match instrument configuration to input file.'

BinAvgW.exe

SeaPlotW.exe

Other modules may work but have not been tested!


