import asyncio
import json
import logging
import os
from itertools import cycle

import nats
import telebot.types
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from nats.aio.msg import Msg

from emojies import replace_from_emoji

load_dotenv()

bots = [AsyncTeleBot(token) for token in os.getenv("TELEGRAM_BOT_TOKENS").split(" ")]
bot = bots[0]

bots = cycle(bots)  # Bypass rate limit

chat_id = os.getenv("chat_id")

nats_connect = {
    "servers": os.getenv("nats_servers"),
    "user": os.getenv("nats_user"),
    "password": os.getenv("nats_password")
}

logging.basicConfig(
    level=logging.DEBUG,
    filename="bot.log",
    filemode="w",
    format="%(asctime)s %(levelname)s %(message)s"
)

text_bridge = os.getenv("text_bot_to_bridge", "[TG] {name}: {text}")


async def message_handler_telegram(message: Msg):
    await message.in_progress()
    msg = json.loads(message.data.decode())
    logging.debug("teesports.chat_id > %s", msg)
    text = msg["text"]
    if isinstance(text, list):
        text = " ".join(text)
    await next(bots).send_message(chat_id, text, message_thread_id=msg["chat_id"])
    await message.ack()


async def main():
    nc = await nats.connect(**nats_connect)
    logging.info("nats connected")
    print("nats connected")
    js = nc.jetstream()

    await js.add_stream(name='teesports', subjects=['teesports.*'], max_msgs=5000)
    await js.subscribe("teesports.messages", "bot", cb=message_handler_telegram)
    logging.info("nats js subscribe \"teesports.messages\"")

    @bot.message_handler(func=lambda message: True)
    async def echo_to_bridge(message: telebot.types.Message):
        if not js:
            return

        name = message.from_user.first_name + (message.from_user.last_name or '')
        await js.publish(
            f"teesports.{message.message_thread_id}",
            text_bridge.format(name=name, text=replace_from_emoji(message.text)).encode()
        )

    await bot.infinity_polling()

if __name__ == '__main__':
    asyncio.run(main())
