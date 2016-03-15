from __future__ import absolute_import

import celery

from raven.contrib.celery import SentryCeleryHandler
from raven.utils.testutils import InMemoryClient, TestCase


class CeleryTestCase(TestCase):
    def setUp(self):
        super(CeleryTestCase, self).setUp()
        self.celery = celery.Celery(__name__)
        self.celery.conf.CELERY_ALWAYS_EAGER = True

        @self.celery.task(name='dummy_task')
        def dummy_task(x, y):
            return x / y

        self.client = InMemoryClient()
        self.handler = SentryCeleryHandler(self.client)
        self.handler.install()
        self.addCleanup(self.handler.uninstall)

    def test_simple(self):
        self.celery.tasks['dummy_task'].delay(1, 2)
        self.celery.tasks['dummy_task'].delay(1, 0)
        assert len(self.client.events) == 1
        event = self.client.events[0]
        exception = event['exception']['values'][0]
        assert event['culprit'] == 'dummy_task'
        assert exception['type'] == 'ZeroDivisionError'
