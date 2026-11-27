terraform {
  required_version = "~> 1.12.2"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.11.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = "us-central1"
}

locals {
  labels = { managed_by = "terraform", environment = var.environment, product = "retail" }
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id                  = "${var.environment}_analytics"
  location                    = "us-central1"
  delete_contents_on_destroy  = false
  default_table_expiration_ms = var.environment == "dev" ? 86400000 : null
  labels                      = local.labels
}

resource "google_storage_bucket" "landing" {
  name                        = "${var.project_id}-${var.environment}-retail"
  location                    = "US-CENTRAL1"
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  labels                      = local.labels
  versioning {
    enabled = var.environment == "prod"
  }
  lifecycle_rule {
    condition {
      age            = var.environment == "dev" ? 7 : 90
      matches_prefix = ["transient/"]
    }
    action { type = "Delete" }
  }
}
