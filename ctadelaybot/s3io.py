"""This module contains functions to read from and write to S3."""

import json
import os
import tempfile

import boto3


S3_BUCKET = 'ctabot-alerts'


def write_to_s3(alert):
    """Save an alert to S3 as a json file."""

    alert_id = alert.get('AlertId')

    with tempfile.TemporaryDirectory(dir='/tmp') as tmpdir:

        filename = os.path.join(tmpdir, alert_id)

        with open(filename, 'w') as outfile:
            json.dump(alert, outfile, indent=2)

        boto3.resources('s3').meta.client.upload_file(
                filename, S3_BUCKET, alert_id)


def is_in_s3(alert):
    """Check if an alert is already saved in S3."""

    alert_id = alert.get('AlertId')
    bucket = boto3.resource('s3').Bucket('alethiomoji-processed-ids')

    return alert_id in [obj.key for obj in bucket.objects.all()]
