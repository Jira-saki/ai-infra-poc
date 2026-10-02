resource "aws_ecr_repository" "this" {
  name                 = "ai-inference"
  image_tag_mutability = "MUTABLE"

  # ป้องกันปัญหา terraform destroy บล็อกเมื่อมี Image ค้างใน Repo
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Environment = "prod"
    Workload    = "ai-inference"
  }
}

output "repository_url" {
  value = aws_ecr_repository.this.repository_url
}

output "repository_arn" {
  value = aws_ecr_repository.this.arn
}
