"""This module contains functions to interact with the CTA alerts API."""

import datetime as dt
import requests

from glom import glom, Coalesce, Literal


CTA_ALERTS_URI = "http://lapi.transitchicago.com/api/1.0/alerts.aspx?outputType=JSON"  # noqa


def _query_api(uri=CTA_ALERTS_URI):
    """Query the alerts API and retrieve a list of alerts."""
    return requests.get(uri).json()


def _parse_api_response(resp_json):
    """Parse the json returned by the alerts API and extract relevant bits."""

    service_subspec = {
        'ServiceType': 'ServiceType',
        'ServiceTypeDescription': 'ServiceTypeDescription',
        'ServiceName': 'ServiceName',
        'ServiceId': 'ServiceId'}

    spec = ('CTAAlerts.Alert', [

               # for each entry in CTAAlerts.Alert pull out the following info
               {'AlertId': 'AlertId',
                'ShortDescription': 'ShortDescription',
                'FullDescription': 'FullDescription',
                'Impact': 'Impact',
                'SeverityScore': 'SeverityScore',
                'LastSeen': Literal(dt.datetime.utcnow().isoformat()),
                'EventStart': Coalesce('EventStart', default=None),
                'EventEnd': Coalesce('EventEnd', default=None),

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
        """Returns true if the alert impact isn't from the minor categories."""

        minors = ['Planned Reroute', 'Special Note', 'Bus Stop Relocation',
                  'Added Service', 'Planned Work', 'Service Change',
                  'Elevator Status', 'Bus Stop Note']

        return alert.get('Impact') not in minors

    return list(filter(is_not_low_impact, alerts))


def get_alerts():
    """Get the any current train delay alerts from the CTA API."""

    resp_json = _query_api()

    alerts = _parse_api_response(resp_json)

    return _filter_delays(_filter_train_alerts(alerts))
