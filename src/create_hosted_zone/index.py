import json
import logging
import os
import sys

import aws_lambda_logging
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
import boto3


patch_all()

log = logging.getLogger()

tag_name = os.getenv('TAG_NAME')
processing_queue = os.getenv('PROCESSING_QUEUE')
aws_region = os.getenv('AWS_REGION')

r53_client = boto3.client('route53', region_name=aws_region)
sqs_client = boto3.client('sqs', region_name=aws_region)


def handler(event, context):
    aws_lambda_logging.setup(level='INFO',
                             aws_request_id=context.aws_request_id)

    for record in event['Records']:
        sqs_receipt_handle = record['receiptHandle']

        try:
            body = json.loads(record['body'])
            source = body['source']
            time = body['time']
            account = body['account']
            region = body['region']
            detail = body['detail']
            event_name = detail['eventName']
            request_id = detail['requestID']
            tag = detail['requestParameters']['tags'][0]

            if tag['key'] == tag_name:
                hosted_zone_name = tag['value']
            else:
                continue
        except Exception as e:
            log.error(f'{str(e)}. Hosted zone: {hosted_zone_name}')
            raise Exception(str(e))

        xray_recorder.begin_subsegment('## create_hosted_zone')
        subsegment = xray_recorder.current_subsegment()
        subsegment.put_metadata('hosted_zone', f'{hosted_zone_name}')

        try:
            response = r53_client.create_hosted_zone(
                Name=hosted_zone_name,
                CallerReference=request_id
            )
            subsegment.put_annotation('ZONE_CREATED', 'SUCCESS')
            xray_recorder.end_subsegment()

            hosted_zone_id = response['HostedZone']['Id']
            hosted_zone_name = response['HostedZone']['Name']

        except Exception as e:
            subsegment.put_annotation('ZONE_CREATED', 'FAILURE')
            log.error(f'str(e). Hosted zone: {hosted_zone_name}')
            xray_recorder.end_subsegment()
            raise Exception(str(e))

        log_payload = {
            'zone_name': hosted_zone_name,
            'zone_id': hosted_zone_id, 
            'source': source, 
            'event_name': event_name,
            'request_id': request_id,
            'tag': tag
        }

        log.info(log_payload)
        
        try:
            sqs_client.delete_message(
                QueueUrl=processing_queue,
                ReceiptHandle=sqs_receipt_handle
            )
        except Exception as e:
            log.error(f'str(e). Hosted zone: {hosted_zone_name}')
            raise Exception(str(e))

    return(True)
