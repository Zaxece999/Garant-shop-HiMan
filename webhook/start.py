import logging
from aiohttp import web
from init import *


logger = logging.getLogger('CS1')


async def start_web_server(host, port):
    logger.debug(f'Server starting.. {host=} {port=}')
    app = web.Application()

    from webhook.heleket import heleket_webhook

    app.add_routes([
        web.post('/heleket', heleket_webhook)
    ])

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, int(port))
    await site.start()
    logger.debug(f'Started!')
