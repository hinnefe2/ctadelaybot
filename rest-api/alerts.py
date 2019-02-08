import json
import tempfile
import os

import boto3
import botocore

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from flask import jsonify
from flask_api import status


S3 = boto3.resource('s3')
BUCKET_NAME = 'ctabot-alerts'


def _read_one_from_s3(alert_id, edit_num=0):
    """Read an alert from S3"""

    alert_id_edit = f'{alert_id}.{edit_num}'

    with tempfile.TemporaryDirectory(dir='/tmp') as tmpdir:

        try:
            filename = os.path.join(tmpdir, 'alert.json')
            S3.Bucket(BUCKET_NAME).download_file(alert_id_edit, filename)

            with open(filename, 'r') as infile:
                alert = json.load(infile)

        except botocore.exceptions.ClientError as e:

            if e.response['Error']['Code'] == "404":
                return e, status.HTTP_404_NOT_FOUND
            else:
                return e, e.response['Error']['Code']

    return alert


def read_one(alert_id):
    """Read an alert from S3 and return it as JSON.  """

    return jsonify(_read_one_from_s3(alert_id))


def read_many(since=0, offset=0, limit=20):
    """Read many alerts from S3"""

    edit_lookup = _read_alert_edits()

    alert_ids = sorted(edit_lookup.keys())

    if since > 0:
        # find the index of the alert just before 'since'
        # then take all the alerts after it
        idx = max(i for i, id_ in enumerate(alert_ids) if id_ < since)
        alert_ids = alert_ids[idx + 1:]

    with ThreadPoolExecutor() as pool:
        results = pool.map(_read_one_from_s3, alert_ids[offset:offset + limit])

    return jsonify(list(results))


def read_one_edit(alert_id, edit_num):
    """Read a specific edit of an alert."""

    return jsonify(_read_one_from_s3(alert_id, edit_num))


def read_all_edits(alert_id):
    """Read all edits of an alert."""

    edit_lookup = _read_alert_edits()

    with ThreadPoolExecutor() as pool:
        results = pool.map(lambda edit: _read_one_from_s3(alert_id, edit),
                           edit_lookup[alert_id])

    return jsonify(list(results))


def _read_alert_edits():
    """Read the edit versions of each alert_id."""

    bucket = S3.Bucket(BUCKET_NAME)

    # alerts are stored in files named <alert_id>.<edit_number>
    alert_id_edits = [map(int, obj.key.split('.'))
                      for obj in bucket.objects.all()]

    edit_lookup = defaultdict(lambda: [])

    for (id_, edit) in alert_id_edits:
        edit_lookup[id_].append(edit)

    return edit_lookup
