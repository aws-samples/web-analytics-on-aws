#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_athena,
  aws_s3 as s3,
)
from constructs import Construct

random.seed(31)

class AthenaWorkGroupStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    ATHENA_WORK_GROUP_NAME = cdk.CfnParameter(self, 'AthenaWorkGroupName',
      type='String',
      description='Amazon Athena Workgroup Name',
      default='WebAnalyticsGroup'
    )

    S3_BUCKET_SUFFIX = ''.join(random.sample((string.ascii_lowercase + string.digits), k=7))
    s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: core.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name='aws-athena-query-results-{region}-{suffix}'.format(
        region=cdk.Aws.REGION, suffix=S3_BUCKET_SUFFIX))

    athena_cfn_work_group = aws_athena.CfnWorkGroup(self, 'AthenaCfnWorkGroup',
      name=ATHENA_WORK_GROUP_NAME.value_as_string,

      # the properties below are optional
      description='workgroup for developer',
      recursive_delete_option=False,
      state='ENABLED', # [DISABLED, ENABLED]
      tags=[cdk.CfnTag(
        key='Name',
        value=ATHENA_WORK_GROUP_NAME.value_as_string
      )],
      work_group_configuration=aws_athena.CfnWorkGroup.WorkGroupConfigurationProperty(
        #XXX: EnforceWorkGroupConfiguration
        # Link: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-athena-workgroup-workgroupconfiguration.html#cfn-athena-workgroup-workgroupconfiguration-enforceworkgroupconfiguration
        # If set to "true", the settings for the workgroup override client-side settings.
        # If set to "false", client-side settings are used.
        enforce_work_group_configuration=False,
        engine_version=aws_athena.CfnWorkGroup.EngineVersionProperty(
          effective_engine_version='Athena engine version 2',
          selected_engine_version='Athena engine version 2'
        ),
        publish_cloud_watch_metrics_enabled=True,
        requester_pays_enabled=True,
        result_configuration=aws_athena.CfnWorkGroup.ResultConfigurationProperty(
          output_location=s3_bucket.s3_url_for_object()
        )
      )
    )

    self.athena_work_group_name = athena_cfn_work_group.name

    cdk.CfnOutput(self, 'f{self.stack_name}_AthenaWorkGroupName', value=self.athena_work_group_name,
      export_name='AthenaWorkGroupName')

