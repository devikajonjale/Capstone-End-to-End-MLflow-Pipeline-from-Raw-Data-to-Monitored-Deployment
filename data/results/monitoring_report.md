# Monitoring report: incoming batches

| Batch | Rows | Drifted features | Watch | Batch RMSE | Ref RMSE | Alert |
|-------|------|------------------|-------|-----------|----------|-------|
| batch_1 | 500 | none | none | 7.26 | 7.487 | no |
| batch_2 | 500 | none | none | 9.092 | 7.487 | no |
| batch_3 | 500 | Area_sqft, Bedrooms, City_Zone | Bathrooms | 16.049 | 7.487 | yes |
