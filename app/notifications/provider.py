import os
from abc import ABC, abstractmethod
from typing import Any


class NotificationProvider(ABC):
    @abstractmethod
    async def send(
        self,
        recipient: str,
        message: str,
        channel: str,
        data_label: str,
        extra: dict[str, Any] | None = None,
    ) -> bool:
        ...


class ConsoleProvider(NotificationProvider):
    async def send(
        self,
        recipient: str,
        message: str,
        channel: str,
        data_label: str,
        extra: dict[str, Any] | None = None,
    ) -> bool:
        print(
            f"[NOTIFICATION] channel={channel} recipient={recipient} "
            f"data_label={data_label} message={message}"
        )
        return True


class TwilioSMSProvider(NotificationProvider):
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER", "")

    async def send(
        self,
        recipient: str,
        message: str,
        channel: str,
        data_label: str,
        extra: dict[str, Any] | None = None,
    ) -> bool:
        if not self.account_sid:
            print(f"[TWILIO STUB] No credentials set. Would SMS {recipient}: {message}")
            return False
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            client.messages.create(body=message, from_=self.from_number, to=recipient)
            return True
        except Exception as e:
            print(f"[TWILIO ERROR] {e}")
            return False


class FCMProvider(NotificationProvider):
    async def send(
        self,
        recipient: str,
        message: str,
        channel: str,
        data_label: str,
        extra: dict[str, Any] | None = None,
    ) -> bool:
        fcm_key = os.getenv("FCM_SERVER_KEY", "")
        if not fcm_key:
            print(f"[FCM STUB] No server key. Would push to {recipient}: {message}")
            return False
        return True


class USSDProvider(NotificationProvider):
    async def send(
        self,
        recipient: str,
        message: str,
        channel: str,
        data_label: str,
        extra: dict[str, Any] | None = None,
    ) -> bool:
        print(f"[USSD MOCK] recipient={recipient} message={message} data_label={data_label}")
        return True


def get_provider() -> NotificationProvider:
    provider_name = os.getenv("NOTIFICATION_PROVIDER", "console").lower()
    providers = {
        "console": ConsoleProvider,
        "twilio": TwilioSMSProvider,
        "fcm": FCMProvider,
        "ussd": USSDProvider,
    }
    cls = providers.get(provider_name, ConsoleProvider)
    return cls()
