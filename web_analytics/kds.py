#!/usr/bin/env python3

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Duration,
  Stack,
  aws_kinesis,
)
from constructs import Construct

random.seed(31)

class KdsStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    KINESIS_STREAM_NAME = cdk.CfnParameter(self, 'KinesisStreamName',
      type='String',
      description='kinesis data stream name',
      default='PUT-Firehose-{}'.format(''.join(random.sample((string.ascii_letters), k=5)))
    )

    source_kinesis_stream = aws_kinesis.Stream(self, "SourceKinesisStreams",
      retention_period=Duration.hours(24),
      stream_mode=aws_kinesis.StreamMode.ON_DEMAND,
      stream_name=KINESIS_STREAM_NAME.value_as_string)

    self.target_kinesis_stream = source_kinesis_stream

    cdk.CfnOutput(self, '{}_KinesisDataStreamName'.format(self.stack_name),
      value=self.target_kinesis_stream.stream_name, export_name='KinesisDataStreamName')

