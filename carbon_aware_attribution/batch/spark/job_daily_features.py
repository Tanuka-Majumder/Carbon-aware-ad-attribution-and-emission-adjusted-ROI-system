from pyspark.sql.functions import col, sum as Fsum, count as Fcount, expr
from batch.spark.common import spark

def main():
    sp = spark("daily-features")
    # In prod: read from S3 (parquet) or warehouse export
    events = sp.read.format("jdbc").options(
        url="jdbc:postgresql://postgres:5432/attribution",
        driver="org.postgresql.Driver",
        dbtable="ad_events",
        user="app",
        password="app",
    ).load()

    # daily aggregates per campaign
    feats = (
        events
        .withColumn("day", expr("to_date(from_unixtime(ts_ms/1000))"))
        .groupBy("day", "campaign_id", "channel")
        .agg(
            Fsum("cost_usd").alias("cost_usd"),
            Fsum("revenue_usd").alias("revenue_usd"),
            Fcount(expr("case when event_type='click' then 1 end")).alias("clicks"),
            Fcount(expr("case when event_type='conversion' then 1 end")).alias("conversions"),
        )
    )

    feats.write.mode("overwrite").parquet("/app/data/daily_campaign_features.parquet")
    sp.stop()

if __name__ == "__main__":
    main()