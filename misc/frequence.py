cipher_text = "ryf utxy? \nryf utxy, orqf jhqihu. nx nqww urwz! ax bhgo roogix, trouqyvo - utxix qo yhutqyv oh fryvxihgo chi rylhyx nth tro ohdxutqyv uh tqfx ro ehybxioruqhy! ojxxet, oh r nqox hwf cixyetdry orqf uh dx hyex, qo ry qybxyuqhy hc dry'o uh jixbxyu tqd cihd utqyzqyv. qu qo rwoh ry qycrwwqswx dxryo hc fqoehbxiqyv utru ntqet tx nqotxo uh tqfx. r tgdry sxqyv, trouqyvo, eryyhu ixoqou utx hjjhiugyqul uh ixbxrw tqdoxwc ryf xpjixoo tqo jxiohyrwqul ntqet ehybxioruqhy vqbxo tqd. xbxil uqdx tx nqww vqbx tqdoxwc rnrl. ntru fh lhg xpjxeu egou uh uxww lhg? txiegwx jhqihu odqwxf. \nr wqx, tx orqf. ryf sl qu, q otrww zyhn utx uigut!"
replacement_dict = {
    'a': '-',
    'b': 'v',
    'c': 'f',
    'd': 'm',
    'e': 'c',
    'f': 'd',
    'g': 'u',
    'h': 'o',
    'i': 'r',
    'j': 'p',
    'k': '-',
    'l': 'y',
    'm': '-',
    'n': 'w',
    'o': 's',
    'p': 'x',
    'q': 'i',
    'r': 'a',
    's': 'b',
    't': 'h',
    'u': 't',
    'v': 'g',
    'w': 'l',
    'x': 'e',
    'y': 'n',
    'z': 'k'
}

def decode_text(encrypted_text):
    decoded_chars = []
    for char in encrypted_text:
        if char in replacement_dict:
            decoded_chars.append(replacement_dict[char])
        else:
            decoded_chars.append(char)
    return ''.join(decoded_chars)

print(decode_text(cipher_text))