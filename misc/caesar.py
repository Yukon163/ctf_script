import string

def caesar_bruteforce(ciphertext):
    alphabet = string.ascii_lowercase
    for shift in range(26):
        decrypted = "".join(
            alphabet[(alphabet.index(c) - shift) % 26] if c in alphabet else c
            for c in ciphertext.lower()
        )
        print(f"Shift {shift}: {decrypted}")


ciphertext_caesar = "bmjs dtz uqfd ymj lfrj tk ymwtsjx dtz bns tw dtz inj ymjwj nx st rniiqj lwtzsi"  # 一个凯撒加密的例子
print("=== Caesar Brute Force ===")
caesar_bruteforce(ciphertext_caesar)

