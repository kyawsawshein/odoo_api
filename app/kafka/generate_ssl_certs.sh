#!/bin/bash

# Cleanup previous run
rm -rf secrets
mkdir secrets

echo "1. Generate CA (Certificate Authority)"
# Generate CA private key and self-signed certificate
openssl req -new -x509 -keyout secrets/ca-key -out secrets/ca-cert -days 365 -nodes -subj "/CN=Kafka-Security-CA"

echo "2. Generate Kafka Broker Keystore and Certificate"
# Generate a key and keystore for the broker
keytool -genkey -noprompt \
    -alias kafka-broker \
    -dname "CN=kafka, OU=IT, O=MyCompany, L=City, S=State, C=US" \
    -keystore secrets/kafka.keystore.jks \
    -keyalg RSA \
    -storepass confluentsesecret \
    -keypass confluentsesecret \
    -validity 365

# Create a certificate signing request (CSR) for the broker
keytool -keystore secrets/kafka.keystore.jks -alias kafka-broker -certreq -file secrets/kafka-broker.csr -storepass confluentsesecret

# Sign the broker CSR with the CA
openssl x509 -req -CA secrets/ca-cert -CAkey secrets/ca-key -in secrets/kafka-broker.csr -out secrets/kafka-broker-ca-signed.crt -days 365 -CAcreateserial -passin pass:confluentsesecret

# Import the CA cert into the broker keystore (so it trusts the CA)
keytool -keystore secrets/kafka.keystore.jks -alias CARoot -import -file secrets/ca-cert -storepass confluentsesecret -noprompt

# Import the signed broker cert into the broker keystore
keytool -keystore secrets/kafka.keystore.jks -alias kafka-broker -import -file secrets/kafka-broker-ca-signed.crt -storepass confluentsesecret -noprompt

echo "3. Generate Client Truststore"
# Import the CA cert into a truststore for the client (Python app)
keytool -keystore secrets/kafka.truststore.jks -alias CARoot -import -file secrets/ca-cert -storepass confluentsesecret -noprompt

echo "4. Create Credential Files for Docker"
echo "confluentsesecret" > secrets/kafka_keystore_password.txt
echo "confluentsesecret" > secrets/kafka_truststore_password.txt

echo "----------------------------------------------------------------"
echo "Certificates generated in 'secrets/' folder:"
echo " - kafka.keystore.jks   (Mount this to Kafka Broker)"
echo " - kafka.truststore.jks (Use this for Java clients or if Broker needs to trust clients)"
echo " - ca-cert              (Use this for Python 'ssl_cafile')"
echo "----------------------------------------------------------------"