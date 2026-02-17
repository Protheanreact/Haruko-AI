import datetime
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Generate key
key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Generate a self-signed cert
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "DE"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Berlin"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Berlin"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MoltBot-PC"),
    x509.NameAttribute(NameOID.COMMON_NAME, "192.168.178.67"),
])

cert = x509.CertificateBuilder().subject_name(
    subject
).issuer_name(
    issuer
).public_key(
    key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.datetime.utcnow()
).not_valid_after(
    # Our certificate will be valid for 1 year
    datetime.datetime.utcnow() + datetime.timedelta(days=365)
).add_extension(
    x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_network("192.168.178.67").network_address)]),
    critical=False,
).sign(key, hashes.SHA256())

# Write key.pem
with open("key.pem", "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))

# Write cert.pem
with open("cert.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print("Zertifikate (cert.pem, key.pem) erfolgreich erstellt, Master.")
