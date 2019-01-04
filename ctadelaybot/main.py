"""This module contains functions to be invoked by AWS lambda to scrape the CTA
alerts API and record the results in S3."""

import logging

import awslogging  # noqa

from api import get_alerts
from s3io import write_to_s3


def scrape_api(context, other_thing):

    alerts = get_alerts()
    logging.info('found {} alerts'.format(len(alerts)))

    for alert in alerts:

        logging.info('writing alert {} to S3'.format(alert.get('AlertId')))
        write_to_s3(alert)


if __name__ == '__main__':
    scrape_api(None, None)
