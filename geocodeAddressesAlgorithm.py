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
import amaps

import os, requests, json, time, urllib

class geocodeAddresses(QgsProcessingAlgorithm):
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
        return 'geocodeFieldAddresses'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Geocode Addresses from Layer')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('geocodeAddresses')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'geocode'

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
        return self.tr("This processing algorithm supports geocoding of a layer with an address field (example: a delimited text file).<br> Make sure your Azure Maps API credentials are managed in the plugin dialog. Please read the referenced <a href='https://www.microsoftvolumelicensing.com/DocumentSearch.aspx?Mode=3&DocumentTypeId=31'>Terms of Usage</a> prior usage.<br>" + warning )

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
                [QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD,
                self.tr('Address Field'),
                parentLayerParameterName=self.INPUT,
                type=QgsProcessingParameterField.String

            )
        )


        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Geocoded Addresses Results')
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
        feedback.pushInfo("searching " + addressField + " using Key " + key)

        if addressField is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        fields = QgsFields()
        fields.append(QgsField("id",QVariant.Int))
        fields.append(QgsField("oldAddress",QVariant.String))
        fields.append(QgsField("newAddress",QVariant.String))
        fields.append(QgsField("ResultType",QVariant.String))
        fields.append(QgsField("score",QVariant.Double))
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
        features = source.getFeatures()
        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            r = requests.get('https://atlas.microsoft.com/search/address/json?api-version=1.0&subscription-key='+ key + '&query=' + feature[addressField])
            if r.status_code == 200:
                results = r.json()["results"]
                if len(results) > 0:
                    fid = 0
                    for result in results:
                        fet = QgsFeature()
                        fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(result["position"]["lon"],result["position"]["lat"])))
                        fet.setAttributes([
                          feature.id(),
                          feature[addressField],
                          result["address"]["freeformAddress"],
                          result["type"],
                          result["score"],
                          result["position"]["lat"],
                          result["position"]["lon"]
                        ])
                        fid+=1
                        sink.addFeature(fet, QgsFeatureSink.FastInsert)

            else:
                raise QgsProcessingException("API response: " + str(r.status_code) )
            feedback.setProgress(int(current * total))
        return {self.OUTPUT: dest_id}
