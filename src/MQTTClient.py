# Copyright (C) 2022, MRIIOT LLC
# All rights reserved.

from src.umqtt.robust2 import MQTTClient as RobustMQTTClient
import utime as time
import json


class MQTTClient:
    def __init__(self, **kwargs):
        self._is_network_available: bool = False
        self._known_connection_issue: bool = False
        self._mqtt: RobustMQTTClient = None
        self._next_ping_time_s: int = 0
        self._last_update: int = time.ticks_ms()
        self._interval_ms: int = 500
        self._broker_ping_s: int = 5
        self._command_topic: str = None
        self._event_topic: str = None
        self._message_handler = None

    def connect(self, client_id, server, port, username, password, keepalive,
                command_topic="sharky/command", event_topic="sharky/event", message_handler=None):
        self._command_topic = command_topic
        self._event_topic = event_topic
        self._message_handler = message_handler
        self._mqtt = RobustMQTTClient(client_id=client_id, server=server, port=port, user=username, password=password, keepalive=keepalive, ssl=None, ssl_params=dict(), socket_timeout=5, message_timeout=10)
        self._mqtt.set_callback(f=self._on_msg)
        self._mqtt.set_last_will(
            topic="{}/{}".format(event_topic, "online"),
            msg=json.dumps({"value": False}).encode(),
            retain=True, qos=0)
        connected = self._mqtt.connect(clean_session=True)
        if connected is not None:
            print('mqtt connection OK')
            self.publish_json("{}/{}".format(event_topic, "online"), {"value": True})
            self.subscribe(topic=command_topic)
            self._advance_ping()
        else:
            print('mqtt connection FAILED')
            pass

    def _on_msg(self, topic, msg, retained, duplicate):
        print(f'mqtt on_msg t:{topic.decode()}, m:{msg.decode()}, r:{retained}, dup:{duplicate}')
        if self._message_handler:
            self._message_handler(
                topic=topic.decode(),
                message=msg.decode(),
                retained=retained,
                duplicate=duplicate)

    def publish_json(self, topic, msg, qos: int = 0, retain: bool = False) -> bool:
        self._mqtt.publish(topic=topic.encode(), msg=json.dumps(msg).encode(), retain=retain, qos=qos)
        return True

    def subscribe(self, topic: str, qos: int = 0, resubscribe: bool = True) -> None:
        self._mqtt.subscribe(topic=topic.encode(), qos=qos, resubscribe=resubscribe)


    def update(self) -> None:
        # no processing if time between intervals has not passed
        if abs(time.ticks_diff(time.ticks_ms(), self._last_update)) < self._interval_ms:
            return

        # keep track of last time this function was allowed to execute
        self._last_update = time.ticks_ms()

        # manage any mqtt transport issues
        if self._mqtt.is_conn_issue():
            if self._known_connection_issue is False:
                self._known_connection_issue = True

            # attempt reconnect
            reconnected = self._mqtt.reconnect()

            # reconnected
            if reconnected is not None:
                print('mqtt reconnection OK')
                self._known_connection_issue = False
                self.publish_json("{}/{}".format(self._event_topic, "online"), {"value": True})
                # subscribe, we don't know if initial connection succeeded to be able to resubscribe
                self.subscribe(topic=self._command_topic)
                self._advance_ping()

        # if mqtt transport has no issues
        if not self._mqtt.is_conn_issue():
            # manage ping
            if time.time() >= self._next_ping_time_s:
                self._advance_ping() 	# set next ping time
                self._mqtt.ping() 		# send ping

            # process mqtt client
            self._mqtt.check_msg()

            # process mqtt queue (unsent messages capabilities)
            self._mqtt.send_queue()

    def _advance_ping(self) -> None:
        self._next_ping_time_s = time.time() + self._broker_ping_s

    def disconnect(self) -> None:
        self._mqtt.disconnect()
