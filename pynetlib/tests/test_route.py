from __future__ import absolute_import
import mock
import unittest
from . import read_file
from nose_parameterized import parameterized
from pynetlib.route import Route
from pynetlib.exceptions import ObjectNotFoundException


class TestRoute(unittest.TestCase):

    def setUp(self):
        self.ip_route_list_output = read_file('ip_route_list')

    def test_init_route(self):
        destination = 'destination'
        device = 'eth0'
        route = Route(destination, device)
        self.assertIsNone(route.metric)
        self.assertIsNone(route.source)
        self.assertIsNone(route.gateway)
        self.assertIsNone(route.namespace)

    @parameterized.expand([
        ('default', 'wlo1', None, None, '600', '192.168.0.254', True),
        ('169.254.0.0/16', 'docker0', 'link', None, '1000', None, False),
        ('172.17.0.0/16', 'docker0', 'link', '172.17.0.1', None, None, False),
        ('192.168.0.0/24', 'wlo1', 'link', '192.168.0.11', '600', None, False)
    ])
    @mock.patch('pynetlib.route.execute_command')
    def test_route_discovery(self, destination, device, scope, source, metric, gateway, default, execute_command):
        execute_command.return_value = self.ip_route_list_output
        route = Route(destination, device)
        route.scope = scope
        route.source = source
        route.gateway = gateway
        route.metric = metric
        routes = Route.discover()
        self.assertEqual(len(routes), 4)
        found_route = routes[routes.index(route)]
        self.assertTrue(self.deep_equality(route, found_route))
        self.assertEqual(found_route.is_default(), default)

    @mock.patch('pynetlib.route.execute_command')
    def test_refresh_route(self, execute_command):
        execute_command.return_value = self.ip_route_list_output
        route = Route('default', 'wlo1')
        route.refresh()
        execute_command.assert_called_once_with("ip route list", namespace=None)
        self.assertEqual(route.metric, '600')
        self.assertEqual(route.gateway, '192.168.0.254')
        self.assertIsNone(route.source)
        self.assertIsNone(route.scope)
        self.assertIsNone(route.namespace)

    @mock.patch('pynetlib.route.execute_command')
    def test_refresh_non_existing_route(self, execute_command):
        execute_command.return_value = self.ip_route_list_output
        route = Route('destination', 'device')
        with self.assertRaises(ObjectNotFoundException):
            route.refresh()
            execute_command.assert_called_once_with("ip route list", namespace=None)

    def deep_equality(self, expected, actual):
        return expected.destination == actual.destination \
            and expected.device == actual.device \
            and expected.scope == actual.scope \
            and expected.source == actual.source \
            and expected.metric == actual.metric \
            and expected.gateway == actual.gateway
