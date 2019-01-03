"""This module contains functions to be invoked by AWS lambda to scrape the CTA
alerts API and record the results in S3."""

import logging

from api import get_alerts
from s3io import is_in_s3, write_to_s3


def scrape_api():

    alerts = get_alerts()
    logging.info('found {} alerts'.format(len(alerts)))

    for alert in alerts:
        if not is_in_s3(alert):
            logging.info('writing alert {} to S3'.format(alert.get('AlertId')))
            write_to_s3(alert)
