from pyspark.sql import SparkSession

_spark_session = None


def get_spark_session() -> SparkSession:
    global _spark_session
    if _spark_session is None:
        _spark_session = (
            SparkSession.builder.appName("DataQualityFramework").getOrCreate()
        )
    return _spark_session