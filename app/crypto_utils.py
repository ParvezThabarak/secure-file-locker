import os, hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

SALT_SIZE = 16
IV_SIZE   = 16
KEY_SIZE  = 32
ITERATIONS = 100_000


def derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS, dklen=KEY_SIZE)


def encrypt_file(input_path: str, output_path: str, password: str) -> dict:
    salt = os.urandom(SALT_SIZE)
    iv   = os.urandom(IV_SIZE)
    key  = derive_key(password, salt)
    padder    = padding.PKCS7(128).padder()
    cipher    = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    with open(input_path, 'rb') as fi, open(output_path, 'wb') as fo:
        fo.write(salt); fo.write(iv)
        while chunk := fi.read(64 * 1024):
            padded = padder.update(chunk)
            if padded: fo.write(encryptor.update(padded))
        fo.write(encryptor.update(padder.finalize()))
        fo.write(encryptor.finalize())
    return {'salt': salt.hex(), 'iv': iv.hex(), 'algorithm': 'AES-256-CBC'}


def decrypt_file(input_path: str, output_path: str, password: str) -> bool:
    with open(input_path, 'rb') as fi:
        salt = fi.read(SALT_SIZE); iv = fi.read(IV_SIZE)
        key  = derive_key(password, salt)
        cipher    = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        unpadder  = padding.PKCS7(128).unpadder()
        with open(output_path, 'wb') as fo:
            while chunk := fi.read(64 * 1024):
                dec = decryptor.update(chunk)
                unp = unpadder.update(dec)
                if unp: fo.write(unp)
            fo.write(unpadder.update(decryptor.finalize()) + unpadder.finalize())
    return True


def get_file_hash(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''): sha256.update(chunk)
    return sha256.hexdigest()
