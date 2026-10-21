# Monitoring report: incoming batches

| Batch | Rows | Drifted features | Watch | Batch RMSE | Ref RMSE | Alert |
|-------|------|------------------|-------|-----------|----------|-------|
| batch_1 | 500 | none | none | 9.807 | 9.59 | no |
| batch_2 | 500 | none | none | 11.256 | 9.59 | no |
| batch_3 | 500 | Area_sqft, Bedrooms, City_Zone | Bathrooms | 18.075 | 9.59 | yes |
