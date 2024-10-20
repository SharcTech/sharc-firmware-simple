import network
import espnow


class NOW:
    def __init__(self, message_handler=None, channel=8, peer=b'\xff\xff\xff\xff\xff\xff', **kwargs):
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        sta.disconnect()
        sta.config(channel=channel)
        self._sequence = 0
        self._broadcast_address = b'\xff\xff\xff\xff\xff\xff'
        self._external_message_handler = message_handler
        self._now = espnow.ESPNow()
        self._now.active(True)
        self._now.add_peer(peer)

    def _message_handler(self, host, msg):
        if self._external_message_handler:
            self._external_message_handler(host, msg)

    def send(self, peer, msg, sync=True):
        try:
            self._now.add_peer(peer)
        except:
            pass
        self._sequence = self._sequence + 1
        message = b'|%s%s' % (self._sequence, msg)
        print(f"sending to: {peer}, msg: {message}")
        return self._now.send(peer, message, sync)

    def broadcast(self, msg, sync=True):
        self._sequence = self._sequence + 1
        message = b'|%s%s' % (self._sequence, msg)
        print(f"sending to: {self._broadcast_address}, msg: {message}")
        return self._now.send(self._broadcast_address, message, sync)

    def update(self):
        host, msg = self._now.recv(0)
        if msg:
            print("msg received from {}: {}".format(host, msg))
            self._message_handler(host, msg)

    def stats(self):
        return self._now.stats()