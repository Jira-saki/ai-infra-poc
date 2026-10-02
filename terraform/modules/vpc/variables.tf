variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of AZs in Tokyo"
  type        = list(string)
  default     = ["ap-northeast-1a", "ap-northeast-1c"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.11.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (EKS Nodes & Pods)"
  type        = list(string)
  default     = ["10.0.2.0/24", "10.0.12.0/24"]
}

variable "cluster_name" {
  description = "EKS Cluster Name for Subnet Auto-discovery tags"
  type        = string
}
