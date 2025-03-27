#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  KdsProxyApiGwStack,
  KdsStack,
  FirehoseToIcebergStack,
  FirehoseRoleStack,
  FirehoseDataProcLambdaStack,
  DataLakePermissionsStack,
  S3BucketStack,
)

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

kds_proxy_apigw = KdsProxyApiGwStack(app, 'WebAnalyticsKdsProxyApiGw')
kds_stack = KdsStack(app, 'WebAnalyticsKinesisStream')

s3_dest_bucket = S3BucketStack(app, 'WebAnalyticsDataFirehoseToIcebergS3Path',
  env=AWS_ENV)
s3_dest_bucket.add_dependency(kds_stack)

firehose_data_transform_lambda = FirehoseDataProcLambdaStack(app,
  'WebAnalyticsFirehoseDataTransformLambdaStack',
  env=AWS_ENV
)
firehose_data_transform_lambda.add_dependency(s3_dest_bucket)

firehose_role = FirehoseRoleStack(app, 'WebAnalyticsFirehoseToIcebergRoleStack',
  firehose_data_transform_lambda.data_proc_lambda_fn,
  kds_stack.kinesis_stream,
  s3_dest_bucket.s3_bucket,
  env=AWS_ENV
)
firehose_role.add_dependency(firehose_data_transform_lambda)

grant_lake_formation_permissions = DataLakePermissionsStack(app, 'WebAnalyticsGrantLFPermissionsOnFirehoseRole',
  firehose_role.firehose_role,
  env=AWS_ENV
)
grant_lake_formation_permissions.add_dependency(firehose_role)

firehose_stack = FirehoseToIcebergStack(app, 'WebAnalyticsFirehoseToIcebergStack',
  firehose_data_transform_lambda.data_proc_lambda_fn,
  kds_stack.kinesis_stream,
  s3_dest_bucket.s3_bucket,
  firehose_role.firehose_role,
  env=AWS_ENV
)
firehose_stack.add_dependency(grant_lake_formation_permissions)

app.synth()
