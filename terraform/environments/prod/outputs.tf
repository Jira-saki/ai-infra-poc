output "configure_kubectl" {
  description = "Command to connect kubectl to EKS"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}

output "ecr_repository_url" {
  description = "ECR Repository URL for pushing AI Inference container image"
  value       = module.ecr.repository_url
}
