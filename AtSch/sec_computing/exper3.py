import os
import json
import socket
import hashlib
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature, decode_dss_signature
from cryptography.hazmat.primitives.asymmetric import utils
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Helper function for saving and loading keys

def save_key(key, filename):
    with open(filename, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))


def load_key(filename):
    with open(filename, "rb") as f:
        return serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )


def save_public_key(key, filename):
    with open(filename, "wb") as f:
        f.write(key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))


def load_public_key(filename):
    with open(filename, "rb") as f:
        return serialization.load_pem_public_key(
            f.read(), backend=default_backend()
        )


# CA Initialization
class CA:
    def __init__(self):
        # Generate CA key pair
        self.sk_ca = ec.generate_private_key(ec.SECP256R1())
        self.pk_ca = self.sk_ca.public_key()
        save_key(self.sk_ca, 'ca_private_key.pem')
        save_public_key(self.sk_ca, 'ca_public_key.pem')

    def sign(self, data):
        signature = self.sk_ca.sign(data, ec.ECDSA(hashes.SHA256()))
        return signature

    def verify(self, signature, data, public_key):
        public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))


# Prover Initialization
class Prover:
    def __init__(self):
        # Generate Prover key pair
        self.sk_p = ec.generate_private_key(ec.SECP256R1())
        self.pk_p = self.sk_p.public_key()
        save_key(self.sk_p, 'prover_private_key.pem')
        save_public_key(self.sk_p, 'prover_public_key.pem')

    def generate_aik(self):
        # Generate AIK key pair
        self.sk_aik = ec.generate_private_key(ec.SECP256R1())
        self.pk_aik = self.sk_aik.public_key()
        save_key(self.sk_aik, 'aik_private_key.pem')
        save_public_key(self.sk_aik, 'aik_public_key.pem')

    def sign(self, data):
        signature = self.sk_p.sign(data, ec.ECDSA(hashes.SHA256()))
        return signature

    def sign_aik(self, data):
        signature = self.sk_aik.sign(data, ec.ECDSA(hashes.SHA256()))
        return signature


# Verifier Initialization
class Verifier:
    def __init__(self):
        self.ca_public_key = load_public_key('ca_public_key.pem')

    def verify_certificate(self, pk_p, sigma, pk_ca):
        pk_ca.verify(sigma, pk_p.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo), ec.ECDSA(hashes.SHA256()))

    def verify_aik_certificate(self, pk_aik, sigma_aik, pk_p):
        pk_p.verify(sigma_aik, pk_aik.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo), ec.ECDSA(hashes.SHA256()))


# Example Usage
def main():
    ca = CA()
    prover = Prover()
    prover.generate_aik()
    sigma = ca.sign(prover.pk_p.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo))
    sigma_aik = prover.sign(prover.pk_aik.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo))

    verifier = Verifier()

    try:
        verifier.verify_certificate(prover.pk_p, sigma, verifier.ca_public_key)
        print("Prover certificate verified.")
    except Exception as e:
        print(f"Prover certificate verification failed: {e}")

    try:
        verifier.verify_aik_certificate(prover.pk_aik, sigma_aik, prover.pk_p)
        print("AIK certificate verified.")
    except Exception as e:
        print(f"AIK certificate verification failed: {e}")


if __name__ == "__main__":
    main()
