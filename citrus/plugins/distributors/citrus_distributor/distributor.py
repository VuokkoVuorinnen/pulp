# -*- coding: utf-8 -*-
#
# Copyright © 2011 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

from pulp.plugins.distributor import Distributor
from pulp.citrus.transport import HttpPublisher
from pulp.server.managers import factory
from logging import getLogger


_LOG = getLogger(__name__)


PUBLISH_DIR='/var/lib/pulp/published/http/citrus/repos'


class CitrusDistributor(Distributor):
    """
    The (citrus) distributor
    """

    @classmethod
    def metadata(cls):
        return {
            'id':'citrus_distributor',
            'display_name':'Pulp Citrus Distributor',
            'types':['repository',]
        }

    def validate_config(self, repo, config, related_repos):
        return (True, None)

    def publish_repo(self, repo, conduit, config):
        """
        Publishes the given repository.

        While this call may be implemented using multiple threads, its execution
        from the Pulp server's standpoint should be synchronous. This call should
        not return until the publish is complete.

        It is not expected that this call be atomic. Should an error occur, it
        is not the responsibility of the distributor to rollback any changes
        that have been made.

        @param repo: metadata describing the repository
        @type  repo: pulp.plugins.model.Repository

        @param publish_conduit: provides access to relevant Pulp functionality
        @type  publish_conduit: pulp.plugins.conduits.repo_publish.RepoPublishConduit

        @param config: plugin configuration
        @type  config: pulp.plugins.config.PluginConfiguration

        @return: report describing the publish run
        @rtype:  pulp.plugins.model.PublishReport
        """
        publish_dir = config.get('publish_dir', PUBLISH_DIR)
        units = conduit.get_units()
        pub = HttpPublisher(publish_dir, repo.id)
        pub.publish([u.__dict__ for u in units])

    def cancel_publish_repo(self, call_report, call_request):
        pass

    def create_consumer_payload(self, repo, config):
        """
        Called when a consumer binds to a repository using this distributor.
        This call should return a dictionary describing all data the consumer
        will need to access the repository. The contents will vary wildly
        depending on the method the repository is published, but examples
        of returned data includes authentication information, location of the
        repository (e.g. URL), and data required to verify the contents
        of the published repository.

        @param repo: metadata describing the repository
        @type  repo: pulp.plugins.model.Repository

        @param config: plugin configuration
        @type  config: pulp.plugins.config.PluginCallConfiguration

        @return: dictionary of relevant data
        @rtype:  dict
        """
        payload = {}
        self._add_repository(repo.id, payload)
        self._add_importers(payload)
        self._add_distributors(repo.id, payload)
        return payload

    def _add_repository(self, repo_id, payload):
        """
        Add repository information to the payload.
        @param repo_id: The repository ID.
        @type repo_id: str
        @param payload: The repository payload
        @type payload: dict
        """
        manager = factory.repo_query_manager()
        payload['repository'] = manager.get_repository(repo_id)

    def _add_importers(self, payload):
        importer = {
            'id':'citrus_importer',
            'distributor_type_id':'citrus_importer',
            'auto_publish':True,
            'base_url':'http://localhost/pulp/citrus/repos',
        }
        payload['importers'] = [importer]

    def _add_distributors(self, repo_id, payload):
        """
        Add repository distributors information to the payload.
        @param repo_id: The repository ID.
        @type repo_id: str
        @param payload: The distributor(s) payload
        @type payload: dict
        """
        manager = factory.repo_distributor_manager()
        payload['distributors'] = manager.get_distributors(repo_id)