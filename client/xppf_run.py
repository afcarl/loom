#!/usr/bin/env python

import json
import requests

from xppf.client import settings_manager

_OK_RESPONSE_CODE = 200

class XppfRunException(Exception):
    pass

class XppfRun:
    """
    This method provides commands for submitting and managing xppf pipeline runs.
    An xppf server must already be running to use this client.
    Users should call this through ../bin/xppfrun to ensure the environment is configured.
    """

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()
        self.settings_manager = settings_manager.SettingsManager(settings_file = args.settings)
        self.pipeline_file = args.pipeline_file

    def _get_args(self):
        parser = self._get_parser()
        args = parser.parse_args()
        return args

    @classmethod
    def _get_parser(cls):
        import argparse
        parser = argparse.ArgumentParser('xppfrun')
        parser.add_argument('pipeline_file')
        parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE', 
                            help="Settings indicate what server to talk to and how to launch it. Use 'xppfserver savesettings -s SETTINGS_FILE' to save.")
        parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
        return parser

    def run(self):
        pipeline = self.read_pipeline_file()

        try:
            response = requests.post(self.settings_manager.get_server_url()+'/api/submitrequest', data=json.dumps(pipeline))
        except requests.exceptions.ConnectionError as e:
            raise Exception("No response from server. (%s)" % e)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise XppfRunException("%s\n%s" % (e.message, response.text))

        return response

    def read_pipeline_file(self):
        try: 
            with open(self.pipeline_file, 'r') as f:
                pipeline_data = json.load(f)
                return pipeline_data
        except IOError as e:
            raise Exception('Failed to open pipeline file %s. (%s)' % (self.pipeline_file, e))
        except ValueError:
            raise Exception("Failed to parse pipeline file file because it is not in valid JSON format: %s" % self.pipeline_file)

if __name__=='__main__':
    response =  XppfRun().run()
    print response.text
