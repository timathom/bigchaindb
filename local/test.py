#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 12 17:41:14 2018

@author: tat2
"""
from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair

bdb_root_url = 'http://localhost:9984'
bdb = BigchainDB(bdb_root_url)
alice = generate_keypair()

test = {'data': {'message': 'Hello!'}}

tx = bdb.transactions.prepare(operation='CREATE', signers=alice.public_key, asset=test, metadata=None,)
signed_tx = bdb.transactions.fulfill(tx, private_keys=alice.private_key)
sent_tx = bdb.transactions.send_commit(signed_tx)
print(sent_tx)

