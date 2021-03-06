from __future__ import absolute_import
from __future__ import print_function

from optparse import make_option
import sys
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from zerver.models import get_realm_by_string_id
from zerver.lib.create_user import random_api_key
from zerver.management.commands.create_realm import Command as CreateRealm

from zilencer.models import Deployment

class Command(BaseCommand):
    help = """Create a deployment and accompanying realm."""

    def add_arguments(self, parser):
        # type: (CommandParser) -> None
        parser.add_argument('--no-realm',
                            dest='no_realm',
                            action='store_true',
                            default=False,
                            help='Do not create a new realm; associate with '
                                 'an existing one. In this case, only the '
                                 'realm and URLs need to be specified.')

        parser.add_argument('-a', '--api-url', dest='api', type=str)
        parser.add_argument('-w', '--web-url', dest='web', type=str)

    def handle(self, *args, **options):
        # type: (*Any, **Any) -> None
        if None in (options["api"], options["web"], options["string_id"]):
            print("\033[1;31mYou must provide a subdomain or string_id, an API URL, and a web URL.\033[0m\n", file=sys.stderr)
            self.print_help("./manage.py", "create_realm")
            exit(1)

        if not options["no_realm"]:
            CreateRealm().handle(*args, **options)
            print() # Newline

        realm = get_realm_by_string_id(options["string_id"])
        if realm is None:
            print("\033[1;31mRealm does not exist!\033[0m\n", file=sys.stderr)
            exit(2)

        dep = Deployment()
        dep.api_key = random_api_key()
        dep.save()
        old_dep = realm.deployment
        if old_dep is not None:
            old_dep.realms.remove(realm)
            old_dep.save()
        dep.realms = [realm]
        dep.base_api_url = options["api"]
        dep.base_site_url = options["web"]
        dep.save()
        print("Deployment %s created." % (dep.id,))
        print("DEPLOYMENT_ROLE_NAME = %s" % (dep.name,))
        print("DEPLOYMENT_ROLE_KEY = %s" % (dep.api_key,))
