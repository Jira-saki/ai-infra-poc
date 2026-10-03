module "vpc" {
  source       = "../../modules/vpc"
  cluster_name = var.cluster_name
}

module "ecr" {
  source = "../../modules/ecr"
}

module "eks" {
  source             = "../../modules/eks"
  cluster_name       = var.cluster_name
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids

  cluster_endpoint_public_access_cidrs = var.cluster_endpoint_public_access_cidrs
}
