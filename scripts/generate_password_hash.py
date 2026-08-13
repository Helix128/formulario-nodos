#!/usr/bin/env python3
from getpass import getpass
from argon2 import PasswordHasher

password = getpass("Contraseña para administración: ")
if not password:
    raise SystemExit("La contraseña no puede estar vacía.")
print(PasswordHasher().hash(password))
