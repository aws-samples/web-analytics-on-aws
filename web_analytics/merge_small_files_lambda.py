#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam,
  aws_lambda,
  aws_logs,
  aws_events,
  aws_events_targets
)
from constructs import Construct

class MergeSmallFilesLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, s3_bucket_name, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    merge_small_files_lambda_fn = aws_lambda.Function(self, "MergeSmallFiles",
      runtime=aws_lambda.Runtime.PYTHON_3_9,
      function_name="MergeSmallFiles",
      handler="athena_ctas.lambda_handler",
      description="Merge small files in S3",
      code=aws_lambda.Code.from_asset('./src/main/python/MergeSmallFiles'),
      environment={
        #TODO: MUST set appropriate environment variables for your workloads.
        'OLD_DATABASE': 'mydatabase',
        'OLD_TABLE_NAME': 'web_log_json',
        'NEW_DATABASE': 'mydatabase',
        'NEW_TABLE_NAME': 'web_log_parquet',
        'WORK_GROUP': 'primary',
        'OLD_TABLE_LOCATION_PREFIX': 's3://{}'.format(os.path.join(s3_bucket_name, 'json-data')),
        'OUTPUT_PREFIX': 's3://{}'.format(os.path.join(s3_bucket_name, 'parquet-data')),
        'STAGING_OUTPUT_PREFIX': 's3://{}'.format(os.path.join(s3_bucket_name, 'tmp')),
        'COLUMN_NAMES': 'userId,sessionId,referrer,userAgent,ip,hostname,os,timestamp,uri',
      },
      timeout=cdk.Duration.minutes(5)
    )

    merge_small_files_lambda_fn.add_to_role_policy(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=["athena:*"]))
    merge_small_files_lambda_fn.add_to_role_policy(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=["s3:Get*",
        "s3:List*",
        "s3:AbortMultipartUpload",
        "s3:PutObject",
      ]))
    merge_small_files_lambda_fn.add_to_role_policy(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=["glue:CreateDatabase",
        "glue:DeleteDatabase",
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:UpdateDatabase",
        "glue:CreateTable",
        "glue:DeleteTable",
        "glue:BatchDeleteTable",
        "glue:UpdateTable",
        "glue:GetTable",
        "glue:GetTables",
        "glue:BatchCreatePartition",
        "glue:CreatePartition",
        "glue:DeletePartition",
        "glue:BatchDeletePartition",
        "glue:UpdatePartition",
        "glue:GetPartition",
        "glue:GetPartitions",
        "glue:BatchGetPartition"
      ]))
    merge_small_files_lambda_fn.add_to_role_policy(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=["lakeformation:GetDataAccess"]))

    lambda_fn_target = aws_events_targets.LambdaFunction(merge_small_files_lambda_fn)
    aws_events.Rule(self, "ScheduleRule",
      schedule=aws_events.Schedule.cron(minute="5"),
      targets=[lambda_fn_target]
    )

    log_group = aws_logs.LogGroup(self, "MergeSmallFilesLogGroup",
      log_group_name=f"/aws/lambda/{self.stack_name}/MergeSmallFiles",
      retention=aws_logs.RetentionDays.THREE_DAYS)
    log_group.grant_write(merge_small_files_lambda_fn)

