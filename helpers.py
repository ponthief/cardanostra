from bech32 import bech32_decode, convertbits


def normalize_public_key(pubkey: str) -> str:
    if pubkey.startswith("npub1"):
        _, decoded_data = bech32_decode(pubkey)
        if not decoded_data:
            raise ValueError("Public Key is not valid npub")

        decoded_data_bits = convertbits(decoded_data, 5, 8, False)
        if not decoded_data_bits:
            raise ValueError("Public Key is not valid npub")
        return bytes(decoded_data_bits).hex()

    # check if valid hex
    if len(pubkey) != 64:
        raise ValueError("Public Key is not valid hex")
    int(pubkey, 16)
    return pubkey


def validate_private_key(priv_key: str) -> bool:
    if not priv_key.startswith('nsec1'):
        return False
    if len(priv_key) != 63:
        raise ValueError("Private Key is not valid hex")
    return True