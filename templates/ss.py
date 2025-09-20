from cryptography.hazmat.primitives.asymmetric import ec
from base64 import urlsafe_b64encode
from cryptography.hazmat.primitives import serialization
priv = ec.generate_private_key(ec.SECP256R1())
raw_priv = priv.private_numbers().private_value.to_bytes(32, "big")
pub = priv.public_key().public_numbers()
raw_pub = b"\x04" + pub.x.to_bytes(32,"big") + pub.y.to_bytes(32,"big")
print("VAPID_PRIVATE_KEY=", urlsafe_b64encode(raw_priv).decode().rstrip("="))
print("VAPID_PUBLIC_KEY=",  urlsafe_b64encode(raw_pub).decode().rstrip("="))
