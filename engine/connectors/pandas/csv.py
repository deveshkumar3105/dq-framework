import pandas as pd

class CSVConnector:
    def __init__(self, path: str):
        self.path = path

    def load(self):
        return pd.read_csv(self.path)