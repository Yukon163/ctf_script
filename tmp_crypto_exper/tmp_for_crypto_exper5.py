from Cryptodome.Cipher import DES
from Cryptodome.Random import get_random_bytes
import os
import json

def initialize_users(file_path='user_keys.json', user_count=10):
    """
    初始化用户主密钥并保存到文件。

    Args:
        file_path (str): 存储用户主密钥的文件路径。
        user_count (int): 初始化的用户数量
    """
    users = {f"User{i}": get_random_bytes(8).hex() for i in range(1, user_count + 1)}
    with open(file_path, 'w') as f:
        json.dump(users, f)
    print(f"Initialized users and saved keys to {file_path}")

def encrypt(key, data):
    """
    使用 DES 算法对数据进行加密。

    Args:
        key (str): 十六进制格式的加密密钥（8 字节）。
        data (str): 需要加密的字符串数据。

    Returns:
        bytes: 加密后的字节数据。
    """
    cipher = DES.new(bytes.fromhex(key), DES.MODE_ECB)
    padded_data = data + (8 - len(data) % 8) * ' '
    return cipher.encrypt(padded_data.encode())

def decrypt(key, encrypted_data):
    """
    使用 DES 算法对数据进行解密。

    Args:
        key (str): 十六进制格式的加密密钥（8 字节）。
        encrypted_data (bytes): 加密的字节数据。

    Returns:
        str: 解密后的字符串数据。
    """
    cipher = DES.new(bytes.fromhex(key), DES.MODE_ECB)
    decrypted_data = cipher.decrypt(encrypted_data).decode().rstrip(' ')
    return decrypted_data

def load_user_keys(file_path='user_keys.json'):
    """
    加载用户主密钥文件。

    Args:
        file_path (str): 存储用户主密钥的文件路径。

    Returns:
        dict: 包含用户名和主密钥的字典。
    """
    with open(file_path, 'r') as f:
        return json.load(f)

def kdc_generate_session_key(user_keys, user_a, user_b):
    """
    KDC 生成会话密钥并返回加密消息。

    Args:
        user_keys (dict): 用户主密钥字典。
        user_a (str): 发起会话请求的用户。
        user_b (str): 接收会话请求的用户。

    Returns:
        tuple: 包含会话密钥、发给 A 的加密消息、发给 B 的加密消息。
    """
    session_key = get_random_bytes(8).hex()
    ka = user_keys[user_a]
    kb = user_keys[user_b]
    message_a = encrypt(ka, f"{session_key}|{user_a}|{user_b}")
    message_b = encrypt(kb, f"{session_key}|{user_a}")
    return session_key, message_a, message_b

def simulate_session(user_keys, user_a, user_b, secret_msg='test'):
    """
    模拟用户之间通过文件传输加密会话内容的过程。

    Args:
        user_keys (dict): 用户主密钥字典。
        user_a (str): 发起会话的用户。
        user_b (str): 接收会话的用户。
        secret_msg (str): 发送的秘密消息。

    Returns:
        None
    """
    original_message = secret_msg
    session_content_file = f'{user_a}_to_{user_b}.txt'

    print(f"{user_a} requests session key for communication with {user_b}")
    session_key, message_a, message_b = kdc_generate_session_key(user_keys, user_a, user_b)

    decrypted_a = decrypt(user_keys[user_a], message_a)
    received_session_key, _, _ = decrypted_a.split('|')
    print(f"{user_a} received session key: {received_session_key}")

    decrypted_b = decrypt(user_keys[user_b], message_b)
    received_session_key_b, sender_id = decrypted_b.split('|')
    print(f"{user_b} received session key: {received_session_key_b} from {sender_id}")

    print(f"\n{user_a} encrypting and sending message to {user_b}: {original_message}")
    encrypted_message = encrypt(received_session_key, original_message)

    encrypted_file = f'encrypted_{session_content_file}'
    with open(encrypted_file, 'wb') as f:
        f.write(encrypted_message)
    print(f"Encrypted message saved to {encrypted_file}")

    print(f"\n{user_b} receiving and decrypting message from {user_a}...")
    with open(encrypted_file, 'rb') as f:
        encrypted_content = f.read()

    decrypted_message = decrypt(received_session_key_b, encrypted_content)
    print(f"Decrypted message: {decrypted_message}")

    assert original_message == decrypted_message, "Decrypted message does not match original!"
    print(f"\n{user_b} successfully received and validated the message.")


if __name__ == "__main__":
    initialize_users()

    user_keys = load_user_keys()

    simulate_session(user_keys, "User4", "User9", "This is a secret message!")

