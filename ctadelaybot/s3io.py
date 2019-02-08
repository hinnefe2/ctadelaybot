"""This module contains functions to read from and write to S3."""

import json
import os
import tempfile

import boto3

from collections import defaultdict


S3_BUCKET = 'ctabot-alerts'


def write_to_s3(alert):
    """Save an alert to S3 as a json file."""

    alert_id = alert.get('AlertId')
    edit_num = set_edit_num(alert)

    with tempfile.TemporaryDirectory(dir='/tmp') as tmpdir:

        filename = os.path.join(tmpdir, f'{alert_id}.{edit_num}')

        with open(filename, 'w') as outfile:
            json.dump(alert, outfile, indent=2)

        boto3.resource('s3').meta.client.upload_file(
                filename, S3_BUCKET, f'{alert_id}.{edit_num}')


def read_from_s3(alert_id_edit):
    """Read an alert from S3 as a json file."""

    bucket = boto3.resource('s3').Bucket(S3_BUCKET)

    with tempfile.TemporaryDirectory(dir='/tmp') as tmpdir:

        filename = os.path.join(tmpdir, alert_id_edit)

        bucket.download_file(alert_id_edit, filename)

        with open(filename, 'r') as infile:
            alert = json.load(infile)

    return alert


def set_edit_num(alert):
    """Get the version number to append to an alert id."""

    alert_id = alert.get('AlertId')
    edit_lookup = read_alert_edits()

    # start at 0 if we haven't seen this alert id yet
    if alert_id not in edit_lookup:
        return 0

    edit_num = max(edit_lookup[alert_id])
    latest = read_from_s3(f'{alert_id}.{edit_num}')

    # use the same edit number if nothing has changed
    if _unchanged(alert, latest):
        return edit_num

    # increment the edit number if something has changed
    else:
        return edit_num + 1


def read_alert_edits():
    """Read the edit versions of each alert_id."""

    bucket = boto3.resource('s3').Bucket(S3_BUCKET)

    # alerts are stored in files named <alert_id>.<edit_number>
    alert_id_edits = [map(int, obj.key.split('.'))
                      for obj in bucket.objects.all()]

    edit_lookup = defaultdict(lambda: [])

    for (id_, edit) in alert_id_edits:
        edit_lookup[id_].append(edit)

    return edit_lookup


def _unchanged(v1, v2):
    """Check if anything except 'LastSeen' is different between two alerts."""
    return ({k: v for k, v in v1.items() if k != 'LastSeen'} ==
            {k: v for k, v in v2.items() if k != 'LastSeen'})
