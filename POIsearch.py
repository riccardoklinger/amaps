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

class POIs(QgsProcessingAlgorithm):
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
        return 'findPOIS'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Find POIs')

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
        return self.tr("This processing algorithm collects POIs around features of a point layer using a metric radius in meters.<br>For a complete list of POI categories and examples visit the <a href='https://docs.microsoft.com/en-us/azure/azure-maps/supported-search-categories'>reference</a>.<br> Make sure your Azure Maps API credentials are managed in the plugin dialog. Please read the referenced <a href='https://www.microsoftvolumelicensing.com/DocumentSearch.aspx?Mode=3&DocumentTypeId=31'>Terms of Usage</a> prior usage.<br>" + warning )

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
        self.addParameter(
            QgsProcessingParameterNumber(
                self.RADIUS,
                self.tr('Radius around Points [m]'),
                defaultValue=100,
                minValue=1,
                maxValue=50000,
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
            feedback.pushInfo("https://atlas.microsoft.com/search/nearby/json?subscription-key=" + key + "&api-version=1.0&limit=" + str(limit) + "&lat=" +str(y) + "&lon=" +str(x) + "&radius=" + str(radius))
            #r = requests.get("https://atlas.microsoft.com/search/poi/category/json?subscription-key={}&api-version=1.0&query={}&limit={}&lat={}&lon={}&radius={}".format(key,categories,limit,y,x,radius))
            r = requests.get("https://atlas.microsoft.com/search/nearby/json?subscription-key=" + key + "&api-version=1.0&limit=" + str(limit) + "&lat=" +str(y) + "&lon=" +str(x) + "&radius=" + str(radius))
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
