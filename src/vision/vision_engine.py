"""Turns a shared screenshot into a factual observation for LUCID."""

from src.utils import Logger

from .vision_client import VisionClient


class VisionEngine:
    def __init__(self):
        self.client = VisionClient()

    def observe(self, page_context, question, previous_observation=""):
        if page_context is None or not page_context.has_image:
            return ""

        observation = self.client.observe(
            page_context.image_base64,
            question,
            previous_observation=previous_observation,
        )

        if observation:
            Logger.info("[Vision] Screen observation completed")

        return observation
