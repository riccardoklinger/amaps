class credloader():
    def getCredentials(self):
        import json, os
        print("get credentials")
        keyStrings = []
        scriptDirectory = os.path.dirname(os.path.realpath(__file__))
        #self.dlg.credentialInteraction.setText("")
        #try:
            #scriptDirectory = os.path.dirname(os.path.realpath(__file__))
        with open(scriptDirectory + os.sep + 'creds' + os.sep + 'credentials.json') as f:
            try:
                data = json.load(f)
                for entry in data["subscriptions"]:
                    #print(entry["key"])
                    #self.dlg.keylist.addItem(QListWidgetItem(entry["key"] + " | " + entry["tier"]))
                    keyStrings.append(str(entry["note"] + " | " + entry["key"] + " | " + entry["tier"]))
                    print("added")
            except:
                print("something went wrong in loading")
        return keyStrings
