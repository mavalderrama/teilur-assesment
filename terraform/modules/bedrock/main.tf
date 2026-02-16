data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  collection_name = replace(lower("${var.environment}-${var.knowledge_base_name}"), "_", "-")
}

# ------------------------------------------------------------------------------
# S3 Bucket for Supplemental Data Storage
# ------------------------------------------------------------------------------
resource "aws_s3_bucket" "supplemental" {
  bucket = "${var.environment}-kb-supplemental-data"

  tags = {
    Name = "${var.environment}-kb-supplemental-data"
  }
}

resource "aws_s3_bucket_public_access_block" "supplemental" {
  bucket = aws_s3_bucket.supplemental.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ------------------------------------------------------------------------------
# OpenSearch Serverless Collection
# ------------------------------------------------------------------------------
resource "aws_opensearchserverless_security_policy" "encryption" {
  name = "${var.environment}-kb-encryption"
  type = "encryption"

  policy = jsonencode({
    Rules = [
      {
        Resource     = ["collection/${local.collection_name}"]
        ResourceType = "collection"
      }
    ]
    AWSOwnedKey = true
  })
}

resource "aws_opensearchserverless_security_policy" "network" {
  name = "${var.environment}-kb-network"
  type = "network"

  policy = jsonencode([
    {
      Rules = [
        {
          Resource     = ["collection/${local.collection_name}"]
          ResourceType = "collection"
        }
      ]
      AllowFromPublic = true
    }
  ])
}

resource "aws_opensearchserverless_access_policy" "data" {
  name = "${var.environment}-kb-data"
  type = "data"

  policy = jsonencode([
    {
      Rules = [
        {
          Resource     = ["collection/${local.collection_name}"]
          ResourceType = "collection"
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:DeleteCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems",
          ]
        },
        {
          Resource     = ["index/${local.collection_name}/*"]
          ResourceType = "index"
          Permission = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument",
          ]
        }
      ]
      Principal = [
        var.bedrock_execution_role_arn,
        data.aws_caller_identity.current.arn,
      ]
    }
  ])
}

resource "aws_opensearchserverless_collection" "kb" {
  name = local.collection_name
  type = "VECTORSEARCH"

  depends_on = [
    aws_opensearchserverless_security_policy.encryption,
    aws_opensearchserverless_security_policy.network,
    aws_opensearchserverless_access_policy.data,
  ]

  tags = {
    Name = "${var.environment}-kb-collection"
  }
}

resource "time_sleep" "wait_for_collection" {
  depends_on      = [aws_opensearchserverless_collection.kb]
  create_duration = "60s"
}

# ------------------------------------------------------------------------------
# OpenSearch Vector Index (required before creating Knowledge Base)
# ------------------------------------------------------------------------------
resource "null_resource" "create_opensearch_index" {
  depends_on = [time_sleep.wait_for_collection]

  triggers = {
    collection_id = aws_opensearchserverless_collection.kb.id
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-BASH
pip3 install -q opensearch-py requests-aws4auth boto3 && \
python3 << 'PYEOF'
import boto3, json
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

region = "${data.aws_region.current.id}"
host = "${aws_opensearchserverless_collection.kb.collection_endpoint}".replace("https://", "")
index_name = "bedrock-knowledge-base-default-index"

session = boto3.Session()
credentials = session.get_credentials()
auth = AWSV4SignerAuth(credentials, region, "aoss")

client = OpenSearch(
    hosts=[{"host": host, "port": 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=30,
)

index_body = {
    "settings": {
        "index.knn": True,
        "index.knn.algo_param.ef_search": 512
    },
    "mappings": {
        "properties": {
            "bedrock-knowledge-base-default-vector": {
                "type": "knn_vector",
                "dimension": 1024,
                "method": {
                    "name": "hnsw",
                    "engine": "faiss",
                    "parameters": {"ef_construction": 512, "m": 16}
                }
            },
            "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
            "AMAZON_BEDROCK_METADATA": {"type": "text"}
        }
    }
}

try:
    if client.indices.exists(index=index_name):
        print("Index already exists, skipping.")
    else:
        response = client.indices.create(index=index_name, body=index_body)
        print(f"Index created: {json.dumps(response)}")
except Exception as e:
    if "resource_already_exists_exception" in str(e):
        print("Index already exists, skipping.")
    else:
        raise
PYEOF
BASH
  }
}

# ------------------------------------------------------------------------------
# Bedrock Knowledge Base
# ------------------------------------------------------------------------------
resource "aws_bedrockagent_knowledge_base" "main" {
  name     = "${var.knowledge_base_name}-${var.environment}"
  role_arn = var.bedrock_execution_role_arn

  depends_on = [null_resource.create_opensearch_index]

  knowledge_base_configuration {
    type = "VECTOR"

    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${data.aws_region.current.id}::foundation-model/amazon.titan-embed-text-v2:0"

      embedding_model_configuration {
        bedrock_embedding_model_configuration {
          dimensions          = 1024
          embedding_data_type = "FLOAT32"
        }
      }

      supplemental_data_storage_configuration {
        storage_location {
          type = "S3"

          s3_location {
            uri = "s3://${aws_s3_bucket.supplemental.id}"
          }
        }
      }

    }
  }

  storage_configuration {
    type = "OPENSEARCH_SERVERLESS"

    opensearch_serverless_configuration {
      collection_arn    = aws_opensearchserverless_collection.kb.arn
      vector_index_name = "bedrock-knowledge-base-default-index"

      field_mapping {
        vector_field   = "bedrock-knowledge-base-default-vector"
        text_field     = "AMAZON_BEDROCK_TEXT_CHUNK"
        metadata_field = "AMAZON_BEDROCK_METADATA"
      }
    }
  }

}

# ------------------------------------------------------------------------------
# S3 Data Source for Knowledge Base
# ------------------------------------------------------------------------------
resource "aws_bedrockagent_data_source" "s3" {
  name                 = "${var.environment}-s3-data-source"
  knowledge_base_id    = aws_bedrockagent_knowledge_base.main.id
  data_deletion_policy = "RETAIN"

  data_source_configuration {
    type = "S3"

    s3_configuration {
      bucket_arn = var.s3_bucket_arn
    }
  }
}
