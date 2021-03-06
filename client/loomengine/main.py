#!/usr/bin/env python

import argparse
import os
import sys

from loomengine.common import get_server_url, has_connection_settings, is_server_running
import loomengine_utils.version
from loomengine_utils.connection import Connection

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)

from loomengine import browser
from loomengine import example
from loomengine import file_client
from loomengine import run
from loomengine import server
from loomengine import template
from loomengine import test_runner
from loomengine import auth
from loomengine import user

class Version(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if not has_connection_settings():
            server_version = 'not connected'
        else:
            url = get_server_url()
            if not is_server_running(url=url):
                server_version = 'no response'
            else:
                connection = Connection(url)
                server_version = connection.get_version()

        print "client version: %s" % loomengine_utils.version.version()
        print "server version: %s" % server_version
        exit(0)

class Main(object):

    def __init__(self, args=None):
        if args is None:
            parser = self.get_parser()
            args = parser.parse_args()
        self.args = args

    def get_parser(cls):
        parser = argparse.ArgumentParser('loom')
        parser.add_argument('-v', '--version', nargs=0, action=Version)

        subparsers = parser.add_subparsers(
            metavar='{run,file,template,browser,auth,user,example,server,test}')

        run_subparser = subparsers.add_parser('run', help='manage runs')
        run.RunClient.get_parser(run_subparser)
        run_subparser.set_defaults(SubcommandClass=run.RunClient)
        
        file_subparser = subparsers.add_parser('file', help='manage files')
        file_client.FileClient.get_parser(file_subparser)
        file_subparser.set_defaults(SubcommandClass=file_client.FileClient)

        template_subparser = subparsers.add_parser('template',
                                                    help='mangage templates')
        template.Template.get_parser(template_subparser)
        template_subparser.set_defaults(SubcommandClass=template.Template)

        browser_subparser = subparsers.add_parser(
            'browser', help='launch the Loom web browser')
        browser.Browser.get_parser(browser_subparser)
        browser_subparser.set_defaults(SubcommandClass=browser.Browser)

        auth_subparser = subparsers.add_parser('auth', help='manage authentication')
        auth.get_parser(auth_subparser)
        auth_subparser.set_defaults(SubcommandClass=auth.AuthClient)

        user_subparser = subparsers.add_parser('user', help='manage users (admin only)')
        user.UserClient.get_parser(user_subparser)
        user_subparser.set_defaults(SubcommandClass=user.UserClient)

        example_subparser = subparsers.add_parser(
            'example', help='use demo examples')
        example.Example.get_parser(example_subparser)
        example_subparser.set_defaults(SubcommandClass=example.Example)
        
        server_subparser = subparsers.add_parser(
            'server', help='manage the Loom server')
        server.get_parser(server_subparser)
        server_subparser.set_defaults(SubcommandClass=server.ServerControls)

        test_subparser = subparsers.add_parser('test', help='run tests')
        test_runner.get_parser(test_subparser)
        test_subparser.set_defaults(SubcommandClass=test_runner.TestRunner)

        return parser

    def run(self):
        return self.args.SubcommandClass(self.args).run()

# pip entrypoint requires a function with no arguments 
def main():
    return Main().run()

if __name__=='__main__':
    main()
