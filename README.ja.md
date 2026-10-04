# ai-infra-poc

[English](README.md) | [日本語](README.ja.md)

シフトレフトセキュリティゲートと厳格なコストガードレールを備えた、**AWS EKS** 上の堅牢（Hardened）かつエフェメラルな AI 推論マイクロサービス。ライフサイクル全体を検証済み：67個のリソースを計画（Plan）→ プロビジョニング（Apply）→ 破棄（Destroy）、リソースの残存（Dangling resources）はゼロ。

## アーキテクチャ (AWS EKS)

![Architecture (AWS EKS)](docs/architecture/architecture-aws-eks.png)

| レイヤー | 詳細 |
|---|---|
| IaC | モジュール化された Terraform: `vpc`, `ecr`, `eks`（KMS CMK によるエンベロープ暗号化） |
| コンピュート | マネージドノードグループ, `SPOT`, `t3.large`, Bottlerocket (`containerd://1.7.33+bottlerocket`), 1 ノード (最大 2) |
| ネットワーク | 2 つのアベイラビリティゾーン (`ap-northeast-1a/c`), **シングル NAT Gateway** |
| レジストリ | プライベート ECR, イミュータブルタグ, プッシュ時スキャン（scan-on-push） |
| ワークロード | Sentence-Transformers FastAPI → 384次元ベクトル埋め込み（Embeddings）; 非 root, 制限付き `securityContext` |

## 主な設計判断 (Key Engineering Decisions)

- **Bottlerocket:** 最小限でイミュータブルなコンテナ特化型 OS。シェルやパッケージマネージャを排除し、攻撃対象領域（Attack Surface）を最小化。ノードへのアクセスは SSM 経由のみ（SSH や Bastion ホストなし）。TOML 設定により `max-pods=35` を構成。
- **シングル NAT:** NAT Gateway はスタック内で最大の固定費要因。AZ ごとに 1 台ではなく 1 台のみ配置することで、AZ レベルのエグレス高可用性をコスト削減とトレードオフ。エフェメラルな検証環境（PoC）として許容。
- **IMDSv2 の強制** (`http_tokens=required`, hop limit 2): メタデータエンドポイント経由の SSRF による認証情報窃取を防止。Hop limit 2 により Pod からの IMDS アクセスを維持。
- **KMS CMK:** Kubernetes Secrets のエンベロープ暗号化および ECR の KMS 暗号化。
- **CVE トリアージ (v1.0.0 → v1.0.1):** Trivy ゲートにより **16 件の CVE（Critical 2件、High 14件）** をブロック。修正内容:
  1. 依存関係のアップデート (`fastapi`, `torch>=2.6`, `sentence-transformers>=3`, `pydantic`)。
  2. ランタイムイメージから `pip` / `setuptools` / `wheel` を削除。
  3. OS レベルの CVE 対処のため、ランタイムステージで `apt-get upgrade` を実行。
  4. 悪用不可能な残存検出事項を `.trivyignore` に文書化。
  
  結果: **対応要（Actionable）な CVE 0件**。
- **コストガードレール:** スポットインスタンスの利用、シングル NAT、1ノード構成、ログ保持期間の短縮、および実行ごとの `terraform destroy` の徹底。

## ローカルサンドボックス: eBPF 脅威検知 & ランタイム隔離 (Quarantine)

![Local Sandbox Architecture: KVM + eBPF + Calico Quarantine](docs/architecture/ai-infra-image.png)

AWS へのプロビジョニング前にローカル KVM サンドボックスで実施した事前検証フェーズ。同一の推論ワークロードに対して、ランタイムのシステムコール監視（eBPF/Falco）および自動化されたワークロード隔離（Calico quarantine）を検証。

- **検知 (Detection):** [`security/falco/`](security/falco/rules-ai-inference.yaml) の Falco ルールにより推論 Pod のシステムコールを監視。
- **封じ込め (Containment):** [`k8s/quarantine-policy.yaml`](k8s/quarantine-policy.yaml) により検知された Pod を隔離し、[`k8s/network-policy.yaml`](k8s/network-policy.yaml) によりエグレス通信を遮断。
- **エビデンス:** [エグレス隔離](docs/evidence/local/03_k8s_egress_isolation.txt), [隔離動作検証](docs/evidence/local/04_containment_quarantine_verification.txt), [クラスタ内推論](docs/evidence/local/02_k8s_incluster_inference.json)。

## 検証実績 (Proof of Work)

| PoW | 主張 / 検証項目 | エビデンス |
|---|---|---|
| 01 Shift-Left SAST | Trivy が 16 件の CVE をブロック (v1.0.0) | [01a (詳細)](docs/evidence/aws-eks/01_shift_left_security/01a_trivy_gate_blocked_before.png), [01b (サマリ)](docs/evidence/aws-eks/01_shift_left_security/01b_trivy_summary_before.png) |
| | v1.0.1 で CVE 0 件を達成 | [01c](docs/evidence/aws-eks/01_shift_left_security/01c_trivy_gate_passed_after.png) |
| | Checkov 36/36 通過 | [01d](docs/evidence/aws-eks/01_shift_left_security/01d_checkov_iac_passed.png) |
| 02 Cost & Guardrails | KMS CMK + 67 リソース検証 | [02a](docs/evidence/aws-eks/02_cost_and_iac_guardrails/02a_kms_envelope_encryption.png) |
| | シングル NAT の適用 | [02b](docs/evidence/aws-eks/02_cost_and_iac_guardrails/02b_single_nat_cost_guardrail.png) |
| 03 Hardened Node | Bottlerocket OS の検証 | [03](docs/evidence/aws-eks/03_bottlerocket_node_hardening/03_bottlerocket_node_verified.png) |
| 04 Registry Gate | ECR 上で Critical 0 件 | [04](docs/evidence/aws-eks/04_supply_chain_registry/04_ecr_image_scan_verified.png) |
| 05 Live Workload | HTTP 200, 384次元ベクトル返却 | [05](docs/evidence/aws-eks/05_live_workload_verification/05_live_inference_success.png) |

## 再現手順 (Reproduce)

```bash
cd terraform/environments/prod && terraform init && terraform plan -var='cluster_endpoint_public_access_cidrs=["<your-ip>/32"]'
checkov -d ../.. --config-file ../../.checkov.yaml --compact          # IaC gate
trivy image --severity HIGH,CRITICAL --ignorefile .trivyignore --exit-code 1 <ecr-url>:v1.0.1   # container gate
terraform apply -var='cluster_endpoint_public_access_cidrs=["<your-ip>/32"]'  # ⚠ 課金が発生します
terraform destroy -var='cluster_endpoint_public_access_cidrs=["<your-ip>/32"]' # 検証後は必ず削除
```
