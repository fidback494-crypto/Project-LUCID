"""Turns a shared screenshot into a factual observation for LUCID."""

from src.utils import Logger

from .vision_client import VisionClient


class VisionEngine:
    def __init__(self):
        self.client = VisionClient()

    def observe(self, page_context, question):
        if page_context is None or not page_context.has_image:
            return ""

        observation = self.client.observe(
            page_context.image_base64,
            question,
        )

        if observation:
            Logger.info("[Vision] Screen observation completed")

        return observation
