class checkValid():
    def checkValidResults(self,addressJSON, key):
        import json
        for (k, v) in addressJSON.items():
            if key == k:
                return v
        return ""
