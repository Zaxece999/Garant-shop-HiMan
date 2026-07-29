import aiohttp
import logging
import json
import configparser
import uuid
import hashlib
import base64

logger = logging.getLogger('CS1')

NETWORK_MAPPING = {
    "TRC20": "tron",
    "ERC20": "eth",
    "BEP20": "bsc",
    "BSC": "bsc",
    "ETH": "eth",
    "TRON": "tron",
    "BTC": "btc",
    "LIGHTNING": "lightning",
    "LTC": "ltc",
    "POLYGON": "polygon",
    "TON": "ton",
    "BCH": "bch",
    "XMR": "xmr",
    "DASH": "dash",
    "DOGE": "doge",
}

AVAILABLE_CURRENCIES = {
    "TRON": ["USDT", "USDC", "TRX"],
    "ETH": ["ETH", "USDT", "USDC", "BUSD", "DAI", "VERSE"],
    "BSC": ["BNB", "USDT", "USDC", "BUSD", "DAI", "CGPT"],
    "BTC": ["BTC"],
    "LTC": ["LTC"],
    "POLYGON": ["MATIC", "USDT", "USDC", "DAI"],
    "TON": ["TON"],
    "BCH": ["BCH"],
    "XMR": ["XMR"],
    "DASH": ["DASH"],
    "DOGE": ["DOGE"]
}

class HeleketAPI:
    def __init__(self, config):
        self.api_key = config['API_KEYS']['heleket']
        self.merchant_id = config['WEBHOOK'].get('MERCHANT_ID', '')
        self.base_url = "https://api.heleket.com"

        if not self.merchant_id:
            logger.error("MERCHANT_ID is empty in config! Please set it in the config file.")

        logger.info(f"Initializing Heleket API with merchant_id: {self.merchant_id}")

        self.headers = {
            "Content-Type": "application/json",
            "merchant": self.merchant_id,
            "sign": self._generate_sign({})
        }

        masked_api_key = self.api_key[:4] + "****" + self.api_key[-4:] if len(self.api_key) > 8 else "****"
        logger.info(f"Heleket initialized with merchant={self.merchant_id}, API key prefix={masked_api_key}")

    def _generate_sign(self, data):
        if not data:
            json_data = ''
        else:
            json_data = json.dumps(data)

        base64_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')

        sign = hashlib.md5((base64_data + self.api_key).encode('utf-8')).hexdigest()

        return sign

    async def create_invoice(self, amount, currency, network, callback_url=None, is_crypto_amount=False):
        try:
            if amount is None or amount == '':
                logger.error("Amount is None or empty, cannot create invoice")
                return None

            mapped_network = NETWORK_MAPPING.get(network, network.lower())
            logger.info(f"Mapping network: {network} -> {mapped_network}")

            order_id = str(uuid.uuid4())[:10]

            amount_str = f"{float(amount):.8f}" if float(amount) < 1 else str(float(amount))
            payload = {
                "amount": amount_str,
                "order_id": order_id,
            }

            if not is_crypto_amount:
                payload["currency"] = "USD"
                payload["to_currency"] = currency
            else:
                payload["currency"] = currency

            if mapped_network:
                payload["network"] = mapped_network

            if callback_url:
                payload["url_callback"] = callback_url

            headers = self.headers.copy()
            headers["sign"] = self._generate_sign(payload)

            logger.info(f"Sending request to Heleket: {payload}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/payment",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        if data.get('state') == 0 and 'result' in data:
                            result = data['result']
                            logger.info(f"Heleket invoice created: {result}")
                            return {
                                "id": result.get('uuid'),
                                "hash": result.get('uuid'),
                                "invoice_hash": result.get('uuid'),
                                "address": result.get('address'),
                                "payment_address": result.get('address'),
                                "amount": result.get('amount'),
                                "payer_amount": result.get('payer_amount'),
                                "currency": result.get('payer_currency') or result.get('currency'),
                                "network": result.get('network'),
                                "status": result.get('payment_status', 'pending'),
                                "url": result.get('url'),
                            }
                        else:
                            error_message = data.get('message', 'Unknown error')
                            logger.error(f"API returned error: {error_message}")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Error response from Heleket: {response.status} - {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Exception in Heleket API: {e}")
            return None

    async def check_payment(self, invoice_id):
        try:
            if not invoice_id:
                logger.error("Invoice ID is empty, cannot check payment")
                return None

            invoice_id = str(invoice_id)

            payload = {
                "uuid": invoice_id
            }

            headers = self.headers.copy()
            headers["sign"] = self._generate_sign(payload)

            url = f"{self.base_url}/v1/payment/info"
            logger.info(f"Checking payment status for invoice_id={invoice_id}, URL={url}")
            logger.info(f"Request payload: {payload}")

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        url,
                        headers=headers,
                        json=payload
                    ) as response:
                        if response.status == 200:
                            data = await response.json()

                            if data.get('state') == 0 and 'result' in data:
                                result = data['result']
                                logger.info(f"Payment check successful: {result}")

                                payment_status = result.get('payment_status', result.get('status', 'pending'))

                                return {
                                    "id": result.get('uuid'),
                                    "hash": result.get('uuid'),
                                    "status": payment_status,
                                    "amount": result.get('amount'),
                                    "payer_amount": result.get('payer_amount'),
                                    "currency": result.get('currency'),
                                    "network": result.get('network')
                                }
                            else:
                                error_message = data.get('message', 'Unknown error')
                                logger.error(f"API returned error during payment check: {error_message}")
                                return None
                        else:
                            error_text = await response.text()
                            logger.error(f"Error checking payment: {response.status} - {error_text}, URL: {url}")
                            return None
                except Exception as e:
                    logger.error(f"Exception during payment check: {e}")
                    return None

        except Exception as e:
            logger.error(f"Exception in Heleket payment check: {e}")
            return None
