from rasa.core.channels.rest import RestInput
from sanic import Blueprint, response
from sanic.request import Request
from typing import Text, Callable, Awaitable
from rasa.core.channels.channel import UserMessage, CollectingOutputChannel


class MetadataChannel(RestInput):

    @classmethod
    def name(cls) -> Text:
        return "custom_channel"

    def blueprint(
        self,
        on_new_message: Callable[[UserMessage], Awaitable[None]]
    ):
        custom_webhook = Blueprint(
            "custom_webhook", __name__
        )

        @custom_webhook.route("/", methods=["GET"])
        async def health(request: Request):
            return response.json({"status": "ok"})

        @custom_webhook.route("/webhook", methods=["POST"])
        async def receive(request: Request):
            sender_id = request.json.get("sender", "user")
            message = request.json.get("message", "")
            metadata = request.json.get("metadata", {})

            collector = CollectingOutputChannel()

            await on_new_message(
                UserMessage(
                    text=message,
                    output_channel=collector,
                    sender_id=sender_id,
                    metadata=metadata,
                )
            )

            return response.json(collector.messages)

        return custom_webhook