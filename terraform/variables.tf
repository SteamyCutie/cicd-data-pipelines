variable "project_id" {
  type = string
}
variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Expected dev, staging or prod."
  }
}
