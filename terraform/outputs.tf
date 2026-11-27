output "dataset" { value = google_bigquery_dataset.analytics.dataset_id }
output "bucket" { value = google_storage_bucket.landing.name }
