from utils import execute_command, find_value
from exceptions import ObjectAlreadyExistsException, ObjectNotFoundException, ForbiddenException


class Namespace():
    DEFAULT_NAMESPACE_NAME = ''

    def __init__(self, name):
        self.name = name
        self.devices = []

    def is_default(self):
        return self.name == Namespace.DEFAULT_NAMESPACE_NAME

    def exists(self):
        return self in Namespace.discover()

    def create(self):
        if self.is_default() or self.exists():
            raise ObjectAlreadyExistsException(self)
        execute_command('ip netns add %s' % self.name)

    def delete(self):
        if self.is_default():
            raise ForbiddenException('Default namespace deletion is not possible')
        if not self.exists():
            raise ObjectNotFoundException(self)
        execute_command('ip netns del %s' % self.name)

    @staticmethod
    def discover(with_devices=False):
        default = Namespace(Namespace.DEFAULT_NAMESPACE_NAME)
        result = execute_command('ip netns list')
        namespaces = [default] + [Namespace(name) for name in result.split()]
        if with_devices:
            for namespace in namespaces:
                namespace.devices = Device.discover(namespace=namespace)
        return namespaces

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return '[' + self.name + ']'


class Device():
    def __init__(self, id, name, namespace=None):
        self.id = id
        self.name = name
        self.namespace = namespace
        self.inet = []
        self.inet6 = []

    def is_loopback(self):
        return self.name == 'lo'

    def add_address(self, address):
        if address in self.inet + self.inet6:
            raise ObjectAlreadyExistsException(address)
        execute_command('ip addr add %s dev %s' % (address, self.name), namespace=self.namespace)

    def remove_address(self, address):
        if address not in self.inet + self.inet6:
            raise ObjectNotFoundException(address)
        execute_command('ip addr del %s dev %s' % (address, self.name), namespace=self.namespace)

    @staticmethod
    def discover(namespace=None):
        output = execute_command('ip addr list', namespace)
        devices = []
        current_device = None
        for block in output.split('\n'):
            if block and block[0].isdigit():
                if current_device:
                    devices.append(current_device)
                prefixes = block.split(':')
                id = prefixes[0]
                name = prefixes[1].strip()
                current_device = Device(id, name, namespace=namespace)
            else:
                words = block.strip().split(' ')
                inet = find_value(words, 'inet')
                if inet is not None:
                    current_device.inet.append(inet)
                inet6 = find_value(words, 'inet6')
                if inet6 is not None:
                    current_device.inet6.append(inet6)
        if current_device:
            devices.append(current_device)
        return devices

    def __eq__(self, other):
        return \
            self.name == other.name and \
            self.id == other.id and \
            self.inet == other.inet and \
            self.inet6 == other.inet6

    def __repr__(self):
        return '[' + ','.join([self.id, self.name, str(self.inet), str(self.inet6)]) + ']'