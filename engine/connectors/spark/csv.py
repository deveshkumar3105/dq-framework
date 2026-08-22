from engine.executors.spark.session import get_spark_session


class SparkCSVConnector:
    def __init__(self, path: str):
        self.path = path

    def load(self):
        spark = get_spark_session()
        return spark.read.csv(self.path, header=True, inferSchema=True)