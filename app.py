#!/usr/bin/env python3
import os

import aws_cdk as cdk

from web_analytics import (
  KdsProxyApiGwStack,
  KdsStack,
  FirehoseDataTransformLambdaStack,
  FirehoseStack,
  MergeSmallFilesLambdaStack,
  AthenaWorkGroupStack,
  AthenaNamedQueryStack,
  VpcStack
)

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()
vpc_stack = VpcStack(app, 'WebAnalyticsVpc',
  env=AWS_ENV)

kds_proxy_apigw = KdsProxyApiGwStack(app, 'WebAnalyticsKdsProxyApiGw')
kds_stack = KdsStack(app, 'WebAnalyticsKinesisStream')

firehose_data_transform_lambda = FirehoseDataTransformLambdaStack(app,
  'WebAnalyticsFirehoseDataTransformLambda')

firehose_stack = FirehoseStack(app, 'WebAnalyticsFirehose',
  kds_stack.target_kinesis_stream.stream_arn,
  firehose_data_transform_lambda.schema_validator_lambda_fn)

athena_work_group_stack = AthenaWorkGroupStack(app,
  'WebAnalyticsAthenaWorkGroup'
)

merge_small_files_stack = MergeSmallFilesLambdaStack(app,
  'WebAnalyticsMergeSmallFiles',
  firehose_stack.s3_dest_bucket_name,
  firehose_stack.s3_dest_folder_name,
  athena_work_group_stack.athena_work_group_name
)

AthenaNamedQueryStack(app,
  'WebAnalyticsAthenaNamedQueries',
  athena_work_group_stack.athena_work_group_name,
  merge_small_files_stack.s3_json_location,
  merge_small_files_stack.s3_parquet_location
)

app.synth()
