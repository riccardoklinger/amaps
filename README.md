# A-Maps
With the A-Maps plugin for QGIS you will be able to consume Azure Maps services with your Azure Maps subscription.

## Usage
The plugin consists of a GUI to handle your credentials and a set of processing algorithms in the processing toolbox.
Prior usage, please make sure, that your credentials are listed in the GUI by getting a key from Azure (we are using the "Primary Key") and adding to the plugin:<br>
![Saved subscription key](https://i.imgur.com/cueW5pE.png "Saved subscription key")<br>
Currently the following API-endpoints are supported:
* geocoding of single address
* geocode of addresses in a field of a layer
* search for POIs around points of a layer
* search POIs of a defined category around points of a layer
![Layer Geocoding with Azure Maps](https://i.imgur.com/w79WgK9.png "Layer Geocoding with Azure Maps")


## Getting your Subscription Key
Get your Azure Maps Subscription by creating an Azure account and subscribe to [Azure Maps Services](https://azure.microsoft.com/en-us/services/azure-maps/).

## Contributors

The idea for A-Maps was conceived and first implementations were done by Riccardo Klinger. Help us improve A-Maps by [testing, filing bug reports, feature requests or ideas](https://github.com/riccardoklinger/amaps/issues). Thank you!
