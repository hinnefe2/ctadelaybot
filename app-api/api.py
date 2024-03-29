"""This module contains functions to interact with the CTA alerts API."""

import datetime as dt
import pytz
import requests

from dateutil.parser import parse

from glom import glom, Coalesce, Literal


CTA_ALERTS_URI = "http://lapi.transitchicago.com/api/1.0/alerts.aspx?outputType=JSON"  # noqa
SEVERITY_THRESHOLD = 37
TIMEOUT=5


def _chicago_to_utc(timestamp):
    """Convert a Chicago timestamp to a UTC timestamp."""

    if timestamp is None:
        return None

    return (pytz.timezone('America/Chicago')
                .localize(parse(timestamp))
                .astimezone(pytz.UTC)
                .isoformat())


def _query_api(uri=CTA_ALERTS_URI):
    """Query the alerts API and retrieve a list of alerts."""
    return requests.get(uri, timeout=TIMEOUT).json()


def _parse_api_response(resp_json):
    """Parse the json returned by the alerts API and extract relevant bits."""

    service_subspec = {
        'ServiceType': 'ServiceType',
        'ServiceTypeDescription': 'ServiceTypeDescription',
        'ServiceName': 'ServiceName',
        'ServiceId': 'ServiceId'}

    spec = ('CTAAlerts.Alert', [

               # for each entry in CTAAlerts.Alert pull out the following info
               {'AlertId': ('AlertId', int),
                'ShortDescription': 'ShortDescription',
                'FullDescription': 'FullDescription.#cdata-section',
                'Impact': 'Impact',
                'SeverityScore': ('SeverityScore', int),
                'LastSeen': Literal(pytz.UTC
                                        .localize(dt.datetime.utcnow())
                                        .isoformat()),
                'EventStart': Coalesce(('EventStart', _chicago_to_utc),
                                       default=None),
                'EventEnd': Coalesce(('EventEnd', _chicago_to_utc),
                                     default=None),

                # pull out each entry in ImpactedService if there are multiple
                'ImpactedService': (
                    'ImpactedService.Service',
                    # some chicanery to make sure this entry is always a
                    # list even though the API just returns a nested dict
                    # when there's only one service
                    lambda s: glom(s, [service_subspec])
                    if isinstance(s, list)
                    else [glom(s, service_subspec)])
                }]
            )

    return glom(resp_json, spec)


def _filter_train_alerts(alerts):
    """Select the subset of alerts which are related to train lines."""

    def is_train_affected(alert):
        """Returns true if the alert affects a train line."""
        return 'R' in glom(alert, ('ImpactedService', ['ServiceType']))

    return list(filter(is_train_affected, alerts))


def _filter_delays(alerts):
    """Select the subset of alerts which refer to delays."""

    def is_not_low_impact(alert):
        """Returns true if the alert severity score is above the threshold."""
        return alert.get('SeverityScore') > SEVERITY_THRESHOLD

    return list(filter(is_not_low_impact, alerts))


def get_alerts():
    """Get the any current train delay alerts from the CTA API."""

    resp_json = _query_api()

    alerts = _parse_api_response(resp_json)

    return _filter_delays(_filter_train_alerts(alerts))
