#!/bin/bash

NAME=${1}
KEY_NAME=$NAME/payment
MAGIC="--testnet-magic 1097911063"

mkdir $NAME
cardano-cli address key-gen \
    --verification-key-file ${KEY_NAME}.vkey \
    --signing-key-file ${KEY_NAME}.skey

cardano-cli address build \
    --payment-verification-key-file ${KEY_NAME}.vkey \
    --out-file ${KEY_NAME}.addr \
    ${MAGIC}

cardano-cli address key-hash \
    --payment-verification-key-file ${KEY_NAME}.vkey \
    --out-file $KEY_NAME.pkh
