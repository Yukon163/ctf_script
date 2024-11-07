import os
import json
import socket
import threading
from cryptography.hazmat.primitives.asymmetric import dh, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

# Generate RSA keys

def generate_rsa_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

def encrypt_message(message, key):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(message.encode()) + encryptor.finalize()
    return iv + ciphertext

def decrypt_message(ciphertext, key):
    iv = ciphertext[:16]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext[16:]) + decryptor.finalize()
    return plaintext.decode()

# Perform Diffie-Hellman key exchange

def perform_dh_key_exchange(peer_public_key_bytes, private_key):
    peer_public_key = serialization.load_pem_public_key(
        peer_public_key_bytes,
        backend=default_backend()
    )
    shared_key = private_key.exchange(peer_public_key)
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'handshake data',
        backend=default_backend()
    ).derive(shared_key)
    return derived_key

class Client:
    def __init__(self, host, port, server_public_key):
        self.host = host
        self.port = port
        self.server_public_key = server_public_key
        self.session_key = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        # Connect to server
        self.socket.connect((self.host, self.port))
        print("Connected to server")

        # 获取服务器的DH参数
        dh_parameters_pem = self.socket.recv(1024)
        dh_parameters = serialization.load_pem_parameters(dh_parameters_pem, backend=default_backend())

        # 根据收到的参数生成私钥和公钥
        dh_private_key = dh_parameters.generate_private_key()
        dh_public_key = dh_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.socket.sendall(dh_public_key)

        # 接收服务器的公钥并进行密钥交换
        server_dh_public_key = self.socket.recv(1024)
        self.session_key = perform_dh_key_exchange(server_dh_public_key, dh_private_key)

        print(f"Session key established: {self.session_key}")

        # Start listening for incoming messages
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    def remote_attestation(self):
        # Simulate remote attestation by sending a dummy attestation token
        attestation_token = json.dumps({"status": "trusted"}).encode()
        self.socket.sendall(attestation_token)
        response = self.socket.recv(1024).decode()
        if response != 'attestation_success':
            raise Exception("Remote attestation failed")
        print("Remote attestation successful")

    def key_exchange(self):
        # Perform DH key exchange
        dh_parameters = dh.generate_parameters(generator=2, key_size=2048, backend=default_backend())
        dh_private_key = dh_parameters.generate_private_key()
        dh_public_key = dh_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.socket.sendall(dh_public_key)
        server_dh_public_key = self.socket.recv(1024)
        self.session_key = perform_dh_key_exchange(server_dh_public_key, dh_private_key)

        # 调试：打印会话密钥
        print(f"客户端会话密钥已建立: {self.session_key}")
        print("Session key established")

    def send_message(self, message):
        encrypted_message = encrypt_message(message, self.session_key)
        self.socket.sendall(encrypted_message)

    def listen_for_messages(self):
        while True:
            encrypted_message = self.socket.recv(1024)
            message = decrypt_message(encrypted_message, self.session_key)
            print(f"Received: {message}")

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.dh_parameters = dh.generate_parameters(generator=2, key_size=2048, backend=default_backend())

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print("Server listening...")

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        # 发送DH参数给客户端
        dh_parameters_pem = self.dh_parameters.parameter_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.ParameterFormat.PKCS3
        )
        client_socket.sendall(dh_parameters_pem)

        # 接收客户端的公钥
        client_dh_public_key = client_socket.recv(1024)

        # 生成私钥并交换
        dh_private_key = self.dh_parameters.generate_private_key()
        dh_public_key = dh_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        client_socket.sendall(dh_public_key)

        session_key = perform_dh_key_exchange(client_dh_public_key, dh_private_key)
        print(f"Session key established with client: {session_key}")

        self.clients.append((client_socket, session_key))

        while True:
            encrypted_message = client_socket.recv(1024)
            message = decrypt_message(encrypted_message, session_key)
            print(f"Client says: {message}")
            # Broadcast to all clients
            for sock, key in self.clients:
                if sock != client_socket:
                    sock.sendall(encrypt_message(message, key))

if __name__ == "__main__":
    mode = input("Enter mode (server/client): ")
    if mode == "server":
        server = Server('0.0.0.0', 12345)
        server.start()
    elif mode == "client":
        server_public_key = None  # Replace with actual server public key if required
        client = Client('localhost', 12345, server_public_key)
        client.start()
        while True:
            msg = input("Enter message: ")
            client.send_message(msg)
