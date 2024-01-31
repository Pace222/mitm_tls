#!/bin/bash
CERT="$PWD/certs/$1"
CA="$PWD/CA/interCA"

openssl req -new -nodes -out $CERT.csr -newkey rsa:4096 -keyout $CERT.key -subj "/C=CH/L=Zürich/O=$2/CN=$1" -addext "subjectAltName = DNS:$1"

cp $PWD/CA/v3_site $CERT.ext
echo "subjectAltName = DNS:$1" >> $CERT.ext

openssl x509 -req -in $CERT.csr -CA $CA.pem -CAkey $CA.key -CAcreateserial -out $CERT.pem -days 730 -sha256 -extfile $CERT.ext

cat $CERT.pem $CA.pem > ${CERT}_chain.pem