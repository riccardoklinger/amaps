# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from PyQt5.QtCore import (QCoreApplication, QUrl, QVariant)
from PyQt5.QtNetwork import (QNetworkReply,
                            QNetworkAccessManager,
                            QNetworkRequest)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingParameterString,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterEnum,
                       QgsNetworkAccessManager,
                       QgsField,
                       QgsFields,
                       QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointXY)
from functools import partial
import processing
from .getCreds import *
from .checkResultValidityPOIs import *
import amaps

import os, requests, json, time, urllib

class POIsByCategories(QgsProcessingAlgorithm):
    def __init__(self):
        super().__init__()
        #amaps.getCredentials()

    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    FIELD = 'FIELD'
    KEY = 'KEY'
    CATEGORIES = 'CATEGORIES'
    RADIUS = 'RADIUS'
    LIMIT = 'LIMIT'

    OUTPUT = 'OUTPUT'

    #print(test)
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return type(self)()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'findPOISCategories'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Find POIs by Category around a Layer')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('POI search')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'POIsearch'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        self.keys = credloader().getCredentials()
        if len(self.keys) == 0:
            warning = "<b>Attention! No key in your credentials.json file found!<b>"
        else:
            warning = ""
        return self.tr("This processing algorithm collects POIs based on a selected category around features of a point layer using a metric radius in meters.<br>For a complete list of categories and examples visit the <a href='https://docs.microsoft.com/en-us/azure/azure-maps/supported-search-categories'>reference</a>.<br> Make sure your Azure Maps API credentials are managed in the plugin dialog. Please read the referenced <a href='https://www.microsoftvolumelicensing.com/DocumentSearch.aspx?Mode=3&DocumentTypeId=31'>Terms of Usage</a> prior usage.<br>" + warning )

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        #read keys:
        #keys = amaps.getCredentials()
        self.keys = credloader().getCredentials()
        self.addParameter(
            QgsProcessingParameterEnum(
                self.KEY,
                self.tr('subscription Key'),
                options=self.keys,
                #defaultValue=0,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input table'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        self.categories=['ACCESS_GATEWAY',
        'ADMINISTRATIVE_DIVISION',
        'ADVENTURE_SPORTS_VENUE',
        'AGRICULTURE',
        'AIRPORT',
        'AMUSEMENT_PARK',
        'AUTOMOTIVE_DEALER',
        'BANK',
        'BEACH',
        'BUILDING_POINT',
        'BUSINESS_PARK',
        'CAFE_PUB',
        'CAMPING_GROUND',
        'CAR_WASH',
        'CASH_DISPENSER',
        'CASINO',
        'CINEMA',
        'CITY_CENTER',
        'CLUB_ASSOCIATION',
        'COLLEGE_UNIVERSITY',
        'COMMERCIAL_BUILDING',
        'COMMUNITY_CENTER',
        'COMPANY',
        'COURTHOUSE',
        'CULTURAL_CENTER',
        'DENTIST',
        'DEPARTMENT_STORE',
        'DOCTOR',
        'ELECTRIC_VEHICLE_STATION',
        'EMBASSY',
        'EMERGENCY_MEDICAL_SERVICE',
        'ENTERTAINMENT',
        'EXCHANGE',
        'EXHIBITION_CONVENTION_CENTER',
        'FERRY_TERMINAL',
        'FIRE_STATION_BRIGADE',
        'FRONTIER_CROSSING',
        'FUEL_FACILITIES',
        'GEOGRAPHIC_FEATURE',
        'GOLF_COURSE',
        'GOVERNMENT_OFFICE',
        'HEALTH_CARE_SERVICE',
        'HELIPAD_HELICOPTER_LANDING',
        'HOLIDAY_RENTAL',
        'HOSPITAL_POLYCLINIC',
        'HOTEL_MOTEL',
        'ICE_SKATING_RINK',
        'IMPORTANT_TOURIST_ATTRACTION',
        'INDUSTRIAL_BUILDING',
        'LEISURE_CENTER',
        'LIBRARY',
        'MANUFACTURING_FACILITY',
        'MARINA',
        'MARKET',
        'MEDIA_FACILITY',
        'MILITARY_INSTALLATION',
        'MOTORING_ORGANIZATION_OFFICE',
        'MOUNTAIN_PASS',
        'MUSEUM',
        'NATIVE_RESERVATION',
        'NIGHTLIFE',
        'NON_GOVERNMENTAL_ORGANIZATION',
        'OPEN_PARKING_AREA',
        'OTHER',
        'PARKING_GARAGE',
        'PARK_RECREATION_AREA',
        'PETROL_STATION',
        'PHARMACY',
        'PLACE_OF_WORSHIP',
        'POLICE_STATION',
        'PORT_WAREHOUSE_FACILITY',
        'POST_OFFICE',
        'PRIMARY_RESOURCE_UTILITY',
        'PRISON_CORRECTIONAL_FACILITY',
        'PUBLIC_AMENITY',
        'PUBLIC_TRANSPORT_STOP',
        'RAILWAY_STATION',
        'RENT_A_CAR_FACILITY',
        'RENT_A_CAR_PARKING',
        'REPAIR_FACILITY',
        'RESEARCH_FACILITY',
        'RESIDENTIAL_ACCOMMODATION',
        'RESTAURANT',
        'RESTAURANT_AREA',
        'REST_AREA',
        'SCENIC_PANORAMIC_VIEW',
        'SCHOOL',
        'SHOP',
        'SHOPPING_CENTER',
        'SPORTS_CENTER',
        'STADIUM',
        'SWIMMING_POOL',
        'TENNIS_COURT',
        'THEATER',
        'TOURIST_INFORMATION_OFFICE',
        'TRAFFIC_LIGHT',
        'TRAFFIC_SERVICE_CENTER',
        'TRAFFIC_SIGN',
        'TRAIL_SYSTEM',
        'TRANSPORT_AUTHORITY VEHICLE_REGISTRATION',
        'TRUCK_STOP',
        'VETERINARIAN',
        'WATER_SPORT',
        'WEIGH_STATION',
        'WELFARE_ORGANIZATION',
        'WINERY',
        'ZOOS_ARBORETA_BOTANICAL_GARDEN']
        self.addParameter(
            QgsProcessingParameterEnum(
                self.CATEGORIES,
                self.tr('POI Categories'),
                options=self.categories,
                #defaultValue=0,
                optional=False,
                allowMultiple=False
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.RADIUS,
                self.tr('Radius around Points [m]'),
                defaultValue=100,
                minValue=1,
                maxValue=100000,
                optional=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LIMIT,
                self.tr('Maximum number of results per queried location'),
                defaultValue=100,
                minValue=1,
                maxValue=100,
                optional=False,
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('POIs')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )
        addressField = self.parameterAsString(
            parameters,
            self.FIELD,
            context
        )
        #print(self.KEY)
        keyField = self.parameterAsInt(
            parameters,
            self.KEY,
            context
        )
        key = credloader().loadKey(keyField)
        radius = self.parameterAsInt(
            parameters,
            self.RADIUS,
            context
        )
        limit = self.parameterAsInt(
            parameters,
            self.LIMIT,
            context
        )
        categorySelection = self.parameterAsEnum(
            parameters,
            self.CATEGORIES,
            context
        )
        feedback.pushInfo("searching " + addressField + " using Key " + key)

        if addressField is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        fields = QgsFields()
        fields.append(QgsField("origin_id",QVariant.Int))
        fields.append(QgsField("id",QVariant.String))
        fields.append(QgsField("score",QVariant.Double))
        fields.append(QgsField("distance",QVariant.Double))
        fields.append(QgsField("name",QVariant.String))
        fields.append(QgsField("categories",QVariant.String))
        fields.append(QgsField("streetNumber",QVariant.String))
        fields.append(QgsField("streetName",QVariant.String))
        fields.append(QgsField("municipality",QVariant.String))
        fields.append(QgsField("postalCode",QVariant.String))
        fields.append(QgsField("countryCode",QVariant.String))
        fields.append(QgsField("freeformAddress",QVariant.String))
        fields.append(QgsField("lat",QVariant.Double))
        fields.append(QgsField("lng",QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.Point,
            QgsCoordinateReferenceSystem(4326)
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        category = self.categories[categorySelection]
        feedback.pushInfo("searching for " + category)
        layerCRS = source.sourceCrs()
        if layerCRS != QgsCoordinateReferenceSystem(4326):
            sourceCrs = source.sourceCrs()
            destCrs = QgsCoordinateReferenceSystem(4326)
            tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
        features = source.getFeatures()
        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            if layerCRS != QgsCoordinateReferenceSystem(4326):
                #we reproject:
                geom = feature.geometry()
                newGeom = tr.transform(geom.asPoint())
                x = newGeom.x()
                y = newGeom.y()
            else:
                x = feature.geometry().asPoint().x()
                y = feature.geometry().asPoint().y()
            coordinates = str(y) + "," + str(x)
            feedback.pushInfo("https://atlas.microsoft.com/search/poi/category/json?subscription-key=" + key + "&api-version=1.0&query=" + category + "&limit=" + str(limit) + "&lat=" +str(y) + "&lon=" +str(x) + "&radius=" + str(radius))
            #r = requests.get("https://atlas.microsoft.com/search/poi/category/json?subscription-key={}&api-version=1.0&query={}&limit={}&lat={}&lon={}&radius={}".format(key,categories,limit,y,x,radius))
            r = requests.get("https://atlas.microsoft.com/search/poi/category/json?subscription-key=" + key + "&api-version=1.0&query=" + category + "&limit=" + str(limit) + "&lat=" +str(y) + "&lon=" +str(x) + "&radius=" + str(radius))
            if r.status_code == 200:
                results = r.json()["results"]
                if len(results) > 0:
                    fid = 0
                    for result in results:
                        fet = QgsFeature()
                        fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(result["position"]["lon"],result["position"]["lat"])))
                        fet.setAttributes([
                          feature.id(),
                          result["id"],
                          result["score"],
                          result["dist"],
                          result["poi"]["name"],
                          ",".join(result["poi"]["categories"]),
                          checkValid().checkValidResults(result["address"],"streetNumber"),
                          checkValid().checkValidResults(result["address"],"streetName"),
                          checkValid().checkValidResults(result["address"],"municipality"),
                          checkValid().checkValidResults(result["address"],"postalCode"),
                          result["address"]["countryCodeISO3"],
                          result["address"]["freeformAddress"],
                          result["position"]["lat"],
                          result["position"]["lon"]
                        ])
                        fid+=1
                        sink.addFeature(fet, QgsFeatureSink.FastInsert)
            else:
                raise QgsProcessingException("API response: " + str(r.status_code) )
            feedback.setProgress(int(current * total))
        return {self.OUTPUT: dest_id}
