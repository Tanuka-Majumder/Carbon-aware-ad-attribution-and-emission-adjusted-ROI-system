from pyspark.sql import SparkSession

def spark(app: str) -> SparkSession:
    return (
        SparkSession.builder
        .appName(app)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.jars", "/app/jars/postgresql-42.7.8.jar")
        .getOrCreate()
    )