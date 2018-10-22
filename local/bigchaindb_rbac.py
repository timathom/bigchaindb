#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 21 22:33:04 2018

@author: tat2
"""

class BigchainDB_RBAC():
    ''' '''    
    def __init__(self, conn, admin_keypair):
        self.conn = conn
        self.admin_keypair = admin_keypair    
        
    def create_new_asset(self, asset, metadata, keypair=None, multiple=False):
        print(multiple)
        print(keypair)
        if keypair == None:            
            keypair = self.admin_keypair        
        if multiple == False:
            tx = self.conn.transactions.prepare(
                    operation="CREATE",
                    signers=keypair.public_key,
                    asset=asset,
                    metadata=metadata)        
        else:
            tx = self.conn.transactions.prepare(
                    operation="CREATE",
                    signers=keypair.public_key,
                    recipients=multiple,
                    asset=asset,
                    metadata=metadata)
        signed_tx = self.conn.transactions.fulfill(
                tx, private_keys=keypair.private_key)                    
        
        return self.conn.transactions.send_commit(signed_tx)
