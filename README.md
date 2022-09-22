
# Web Log Analytics with Amazon Kinesis Data Streams Proxy using Amazon API Gateway

This repository provides you cdk scripts and sample code on how to implement a simple [web analytics](https://en.wikipedia.org/wiki/Web_analytics) system.<br/>
Below diagram shows what we are implementing.

![web-analytics-arch](web-analytics-arch.svg)


The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
(.venv) $ pip install -r requirements.txt
```

### Upload Lambda Layer code

Before deployment, you should uplad zipped code files to s3 like this:
<pre>
(.venv) $ aws s3api create-bucket --bucket <i>your-s3-bucket-name-for-lambda-layer-code</i> --region <i>region-name</i>
(.venv) $ ./build-aws-lambda-layer-package.sh <i>your-s3-bucket-name-for-lambda-layer-code</i>
</pre>
(:warning: Make sure you have **Docker** installed.)

For example,
<pre>
(.venv) $ aws s3api create-bucket --bucket lambda-layer-resources --region us-east-1
(.venv) $ ./build-aws-lambda-layer-package.sh lambda-layer-resources
</pre>

For more information about how to create a package for Amazon Lambda Layer, see [here](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-layer-simulated-docker/).

### Deploy

At this point you can now synthesize the CloudFormation template for this code.

<pre>
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
(.venv) $ cdk synth --all \
              --parameters KinesisStreamName='your-kinesis-data-stream-name' \
              --parameters FirehoseStreamName='your-delivery-stream-name' \
              --parameters LambdaLayerCodeS3BucketName=<i>'your-s3-bucket-name-for-lambda-layer-code'</i> \
              --parameters LambdaLayerCodeS3ObjectKey=<i>'your-s3-object-key-for-lambda-layer-code'</i>
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy --require-approval never --all \
              --parameters KinesisStreamName='your-kinesis-data-stream-name' \
              --parameters FirehoseStreamName='your-delivery-stream-name' \
              --parameters LambdaLayerCodeS3BucketName=<i>'your-s3-bucket-name-for-lambda-layer-code'</i> \
              --parameters LambdaLayerCodeS3ObjectKey=<i>'your-s3-object-key-for-lambda-layer-code'</i>
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Run Test

1. Run `GET /streams` method to invoke `ListStreams` in Kinesis
   <pre>
   $ curl -X GET https://<i>your-api-gateway-id</i>.execute-api.us-east-1.amazonaws.com/v1/streams
   </pre>

   The response is:
   <pre>
   {
     "HasMoreStreams": false,
     "StreamNames": [
       "PUT-Firehose-aEhWz"
     ],
     "StreamSummaries": [
       {
         "StreamARN": "arn:aws:kinesis:us-east-1:123456789012:stream/PUT-Firehose-aEhWz",
         "StreamCreationTimestamp": 1661612556,
         "StreamModeDetails": {
           "StreamMode": "ON_DEMAND"
         },
         "StreamName": "PUT-Firehose-aEhWz",
         "StreamStatus": "ACTIVE"
       }
     ]
   }
   </pre>
2. Generate test data.
   <pre>
   (.venv) $ pip install -r requirements-dev.txt
   (.venv) $ python src/utils/gen_fake_data.py --max-count 5 --stream-name <i>PUT-Firehose-aEhWz</i> --api-url 'https://<i>your-api-gateway-id</i>.execute-api.us-east-1.amazonaws.com/v1' --api-method records
   [200 OK] {"EncryptionType":"KMS","FailedRecordCount":0,"Records":[{"SequenceNumber":"49633315260289903462649185194773668901646666226496176178","ShardId":"shardId-000000000003"}]}
   [200 OK] {"EncryptionType":"KMS","FailedRecordCount":0,"Records":[{"SequenceNumber":"49633315260289903462649185194774877827466280924390359090","ShardId":"shardId-000000000003"}]}
   [200 OK] {"EncryptionType":"KMS","FailedRecordCount":0,"Records":[{"SequenceNumber":"49633315260223001227053593325351479598467950537766600706","ShardId":"shardId-000000000000"}]}
   [200 OK] {"EncryptionType":"KMS","FailedRecordCount":0,"Records":[{"SequenceNumber":"49633315260245301972252123948494224242560213528447287314","ShardId":"shardId-000000000001"}]}
   [200 OK] {"EncryptionType":"KMS","FailedRecordCount":0,"Records":[{"SequenceNumber":"49633315260223001227053593325353897450107179933554966530","ShardId":"shardId-000000000000"}]}
   </pre>
3. Creating and loading a table with partitioned data in Amazon Athena

   Go to [Athena](https://console.aws.amazon.com/athena/home) on the AWS Management console.<br/>
   * (step 1) Create a database

     In order to create a new database called `mydatabase`, enter the following statement in the Athena query editor
     and click the **Run** button to execute the query.

     <pre>
     CREATE DATABASE mydatabase
     </pre>

    * (step 2) Create a table

      Copy the following query into the Athena query editor, replace the `xxxxxxx` in the last line under `LOCATION` with the string of your S3 bucket, and execute the query to create a new table.
      <pre>
      CREATE EXTERNAL TABLE `mydatabase.web_log_json`(
        `userId` string,
        `sessionId` string,
        `referrer` string,
        `userAgent` string,
        `ip` string,
        `hostname` string,
        `os` string,
        `timestamp` timestamp,
        `uri` string)
      PARTITIONED BY (
        `year` int,
        `month` int,
        `day` int,
        `hour` int)
      ROW FORMAT SERDE
        'org.openx.data.jsonserde.JsonSerDe'
      STORED AS INPUTFORMAT
        'org.apache.hadoop.mapred.TextInputFormat'
      OUTPUTFORMAT 
        'org.apache.hadoop.hive.ql.io.IgnoreKeyTextOutputFormat'
      LOCATION
        's3://web-analytics-<i>xxxxx</i>/json-data'
      </pre>
      If the query is successful, a table named `web_log_json` is created and displayed on the left panel under the **Tables** section.

      If you get an error, check if (a) you have updated the `LOCATION` to the correct S3 bucket name, (b) you have mydatabase selected under the Database dropdown, and (c) you have `AwsDataCatalog` selected as the **Data source**.

    * (step 3) Load the partition data

      Run the following query to load the partition data.
      <pre>
      MSCK REPAIR TABLE mydatabase.web_log_json;
      </pre>
      After you run this command, the data is ready for querying.

4. Run test query

   Enter the following SQL statement and execute the query.
   <pre>
   SELECT COUNT(*)
   FROM mydatabase.web_log_json;
   </pre>
5. Merge small files into large one

   When real-time incoming data is stored in S3 using Kinesis Data Firehose, files with small data size are created.<br/>
   To improve the query performance of Amazon Athena, it is recommended to combine small files into one large file.<br/>
   Also, it is better to use columnar dataformat (e.g., `Parquet`, `ORC`, `AVRO`, etc) instead of `JSON` in Amazon Athena.<br/>
   Now we create an Athena table to query for large files that are created by periodical merge files task.
   <pre>
   CREATE EXTERNAL TABLE `mydatabase.web_log_parquet`(
     `userId` string,
     `sessionId` string,
     `referrer` string,
     `userAgent` string,
     `ip` string,
     `hostname` string,
     `os` string,
     `timestamp` timestamp,
     `uri` string)
   PARTITIONED BY (
     `year` int,
     `month` int,
     `day` int,
     `hour` int)
   ROW FORMAT SERDE
     'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
   STORED AS INPUTFORMAT
     'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat'
   OUTPUTFORMAT
     'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
   LOCATION
     's3://web-analytics-<i>xxxxx</i>/parquet-data'
   </pre>
   After creating the table and once merge files task is completed, the data is ready for querying.

## Clean Up

Delete the CloudFormation stack by running the below command.
<pre>
(.venv) $ cdk destroy --force --all
</pre>


## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

 * [Web Analytics](https://en.wikipedia.org/wiki/Web_analytics)
 * [Tutorial: Create a REST API as an Amazon Kinesis proxy in API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/integrating-api-with-aws-services-kinesis.html)
 * [Streaming Data Solution for Amazon Kinesis](https://aws.amazon.com/ko/solutions/implementations/aws-streaming-data-solution-for-amazon-kinesis/)
   <div>
     <img src="https://d1.awsstatic.com/Solutions/Solutions%20Category%20Template%20Draft/Solution%20Architecture%20Diagrams/aws-streaming-data-using-api-gateway-architecture.1b9d28f061fe84385cb871ec58ccad18c7265d22.png", alt with="385" height="204">
   </div>
 * [Serverless Patterns Collection](https://serverlessland.com/patterns)
 * [aws-samples/serverless-patterns](https://github.com/aws-samples/serverless-patterns)
 * [Building fine-grained authorization using Amazon Cognito, API Gateway, and IAM](https://aws.amazon.com/ko/blogs/security/building-fine-grained-authorization-using-amazon-cognito-api-gateway-and-iam/)
 * [Amazon Athena Workshop](https://athena-in-action.workshop.aws/)
 * [Curl Cookbook](https://catonmat.net/cookbooks/curl)
 * [fastavro](https://fastavro.readthedocs.io/) - Fast read/write of `AVRO` files
 * [Apache Avro Specification](https://avro.apache.org/docs/current/spec.html)
 * [How to create a Lambda layer using a simulated Lambda environment with Docker](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-layer-simulated-docker/)
   ```
   $ cat <<EOF > requirements-Lambda-Layer.txt
   > fastavro==1.6.1
   > EOF
   $ docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.9" /bin/sh -c "pip install -r requirements-Lambda-Layer.txt -t python/lib/python3.9/site-packages/; exit"
   $ zip -r fastavro-lib.zip python > /dev/null
   $ aws s3 mb s3://my-bucket-for-lambda-layer-packages
   $ aws s3 cp fastavro-lib.zip s3://my-bucket-for-lambda-layer-packages/
   ```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

