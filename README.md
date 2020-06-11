# eb-route53

The purpose of this project is to illustrate how a Route53 hosted zone can automatically be created when a specific tag is applied to an organization, all using AWS Serverless technologies.

**Note** The example below assumes that an [AWS Organization](https://aws.amazon.com/organizations/) already exists in the account to which this application is being deployed.  Please refer to the product documentation for [creating and managing an organization](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_org.html).

When an organization is tagged, an event is written to [AWS CloudTrail](https://aws.amazon.com/cloudtrail/).  This event captures the pertinent information regarding the tagging event.  Please refer to [TagResource.json](./TagResource.json) for a representative event.

In this example application, the CloudTrail event is captured by [Amazon EventBridge](https://aws.amazon.com/eventbridge/) when a *TagResource* event occurs from *organizations.amazonaws.com*.  Amazon EventBridge is a serverless event bus that makes it easy to connect applications together using data from your own applications, integrated Software-as-a-Service (SaaS) applications, and AWS services.  EventBridge delivers a stream of real-time data from event sources to targets.  One such target is [Amazon Simple Queue Service (SQS)](https://aws.amazon.com/sqs/).  In our example application, EventBridge delivers an event to our SQS queue.  An [AWS Lambda](https://aws.amazon.com/lambda/) function is set to be invoked when a message is present on our Amazon SQS queue.  This function, in turn, will create a hosted zone in [Amazon Route 53](https://aws.amazon.com/route53/), a highly available and scalable cloud [Domain Name System (DNS)](https://aws.amazon.com/route53/what-is-dns/) web service.

In the event our Lambda function cannot process the event on the SQS queue, the event is sent to a [Dead Letter Queue (DLQ)](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html).  Our application has an alarm configured to send an email notification via [Amazon Simple Notification Service (SNS)](https://aws.amazon.com/sns/) should a message be sent to the DLQ.

# Pre-requisites

* [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)

* [AWS CLI](https://aws.amazon.com/cli/)

* [Docker](https://docs.docker.com/install/)


# Building and deploying the application

## Build

```bash
sam build --use-container
```

## Package

```bash
export DEPLOYMENT_BUCKET='s3_bucket_you_own'
sam package --s3-bucket DEPLOYMENT_BUCKET
```

## Deploy

### Default

```bash
export REGION='us-east-1' # Adjust to your desired region
export PROJECT='eb-route-53' # Adjust to your desired project name
export ALARM_RECIPIENT='your_address@domain.tld' # Adjust to your desired email address

sam deploy \
    --template-file packaged-template.yml \
    --stack-name ${PROJECT} \
    --region ${REGION} \
    --tags Project=${PROJECT} \
    --parameter-overrides AlarmRecipientEmailAddress=${ALARM_RECIPIENT} \
    --capabilities CAPABILITY_IAM
```

### Using custom tag name

```bash
export REGION='us-east-1' # Adjust to your desired region
export PROJECT='eb-route-53' # Adjust to your desired project name
export ALARM_RECIPIENT='your_address@domain.tld' # Adjust to your desired email address
export TAG_NAME='your_tag_name' # Adjust to your desired email address (default: r53zone)

sam deploy \
    --template-file packaged-template.yml \
    --stack-name ${PROJECT} \
    --region ${REGION} \
    --tags Project=${PROJECT} \
    --parameter-overrides AlarmRecipientEmailAddress=${ALARM_RECIPIENT} TagName=${TAG_NAME} \
    --capabilities CAPABILITY_IAM
```
