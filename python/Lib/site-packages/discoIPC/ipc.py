"""The DiscordIPC class."""

import os
import platform
import re
import json
import struct
import socket
import uuid


class DiscordIPC(object):
    """Docstring for DiscordIPC."""

    def __init__(self, client_id):
        """Docstring for __init__."""
        super(DiscordIPC, self).__init__()

        # Your computer's platform.
        self.platform = self._get_platform()
        # The connection path to Discord IPC Socket.
        self.ipc_path = self._get_ipc_path()
        # Your Application's ID (a.k.a. Client ID).
        self.client_id = client_id
        # The process ID of the running process.
        self.pid = os.getpid()
        # It's not connected to Discord Client at this point.
        self.connected = False
        # The User Activity that's to be sent to Discord Client.
        self.activity = None
        # The Discord IPC Socket.
        self.socket = None

    def _get_platform(self):
        """Get the system's platformself."""
        system = platform.system().lower()
        # Supported Discord platforms are Linux, macOS (darwin) and Windows.
        if system in ['darwin', 'linux', 'windows']:
            return system
        else:
            raise Exception('Discord IPC doesn\'t support {0}.'.format(system))

    def _get_ipc_path(self, id=0):
        """Get the path to IPC Socket connection."""
        if self.platform == 'windows':
            # IPC path for Windows.
            return '\\\\?\\pipe\\discord-ipc-{0}'.format(id)
        else:
            # IPC path for unix based systems (Linux, macOS).
            path = os.environ.get('XDG_RUNTIME_DIR') or os.environ.get('TMPDIR') or os.environ.get('TMP') or os.environ.get('TEMP') or '/tmp'
            return re.sub(r'\/$', '', path) + '/discord-ipc-{0}'.format(id)

    def _encode(self, opcode, payload):
        """Encode the payload to send to the IPC Socket."""
        payload = json.dumps(payload)
        payload = payload.encode('utf-8')
        return struct.pack('<ii', opcode, len(payload)) + payload

    def _decode(self):
        """Decode the data received from Discord."""
        if self.platform == 'windows':
            encoded_header = b""
            header_size = 8

            while header_size:
                encoded_header += self.socket.read(header_size)
                header_size -= len(encoded_header)

            decoded_header = struct.unpack('<ii', encoded_header)
            encoded_data = b''
            remaining_packet_size = int(decoded_header[1])

            while remaining_packet_size:
                encoded_data += self.socket.read(remaining_packet_size)
                remaining_packet_size -= len(encoded_data)
        else:
            recived_data = self.socket.recv(1024)
            encoded_header = recived_data[:8]
            decoded_header = struct.unpack('<ii', encoded_header)
            encoded_data = recived_data[8:]

        return json.loads(encoded_data.decode('utf-8'))

    def _send(self, opcode, payload):
        """Send the payload to Discord via Discord IPC Socket."""
        encoded_payload = self._encode(opcode, payload)

        try:
            if self.platform == 'windows':
                self.socket.write(encoded_payload)
                self.socket.flush()
            else:
                self.socket.send(encoded_payload)
        except Exception:
            raise Exception('Can\'t send data to Discord via IPC.')

    def connect(self):
        """Connect to Discord Client via IPC."""
        if self.connected:
            # Already Connected to the Discord Client.
            pass
        else:
            # Let's connect to Discord Client via Discord IPC Socket.
            try:
                if self.platform == 'windows':
                    self.socket = open(self.ipc_path, 'w+b')
                else:
                    self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    self.socket.connect(self.ipc_path)
            except Exception:
                raise Exception('Can\'t connect to Discord Client.')

            # Let's handshake with Discord...
            self._send(0, {
                'v': 1,
                'client_id': self.client_id
            })
            # ...and see it's respond.
            self._decode()

            # Since it respond and we're connected
            self.connected = True
            # TODO: And if activity is defined, set it.
            # if self.activity:
            #     ipc.set_activity(self.activity)

    def disconnect(self):
        """Terminate connection to Discord IPC Socket."""
        # Let's let Discord know that we're going to disconnect.
        self._send(2, {})

        # Bye Discord!
        if self.platform != 'windows':
            self.socket.shutdown(socket.SHUT_RDWR)

        # See you soon!
        self.socket.close()
        self.socket = None
        # We are not connected to Discord anymore, so...
        self.connected = False
        self.activity = None

    def update_activity(self, activity):
        """Update User's Discord activity."""
        # Let's add some payload to the acitivity object.
        payload = {
            'cmd': 'SET_ACTIVITY',
            'args': {
                'activity': activity,
                'pid': self.pid
            },
            'nonce': str(uuid.uuid4())
        }

        # Send activity data to Discord Client.
        self._send(1, payload)
        self._decode()
