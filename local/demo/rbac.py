#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later

"""This module provides a simple interface to the BigchainDB Role-Based
Access Control extension (available in the rbac branch of the 
BigchainDB GitHub repository).

Adapted from:
     - https://github.com/bigchaindb/project-jannowitz/tree/master/rbac

@author: timathom@indiana.edu
"""

import time
import datetime

class BigchainRbac():
    """Provides an interface to create new assets, users, types, and
    type instances for Role-Based Access Control in BigchainDB.
    
    """
    
    def __init__(self, conn, namespace, app_name, admin_kp, admin_pks):
        """Initialize a new RBAC interface.
        
        Args:
            conn: A connection to a BigchainDB server.
            namespace (str): A namespace for the RBAC application.
            app_name (str): Name of the app.
            admin_kp (str): The public/private keypair of the admin
                user. The admin creates roles and assigns permissions.
            admin_pks (list): The public keys of all admin users for the network.
                    
        """
        
        self.conn = conn
        self.namespace = namespace
        self.app_name = app_name
        self.admin_kp = admin_kp
        self.admin_pks = admin_pks

    
    def bootstrap_admin_group(self):
        
        asset = {"data": {
            "@context": {
                "foaf": "http://xmlns.com/foaf/0.1/",
                "schema": "http://schema.org/"
            },
            "@type": "foaf:Group",
            "schema:name": self.app_name + " Admin User Group Asset",
            "schema:identifier": {
                "@type": "PropertyValue",
                "schema:name": "namespace",
                "schema:value": self.namespace + ".admin"
            }        
        }}
            
        data = {
            "@context": {
                "foaf": "http://xmlns.com/foaf/0.1/",
                "schema": "http://schema.org/"
            },
            "@type": "foaf:Group",
            "schema:name": self.app_name + " Admin User Group Metadata",
            "can_link": self.admin_pks
        }
        
        return self.create_new_asset(asset, data)  
    
        
    def bootstrap_app(self, admin_group_id):
        
        asset = {"data": {
            "@context": "http://schema.org",
            "@type": "SoftwareApplication",
            "name": self.app_name,
            "identifier": {
                "@type": "PropertyValue",
                "name": "namespace",
                "value": self.namespace
            }
        }}
        
        data = {
            "@context": {
                "foaf": "http://xmlns.com/foaf/0.1/",
                "schema": "http://schema.org/"
            },
            "@type": "foaf:Group",
            "schema:name": self.app_name + " Metadata",
            "can_link": admin_group_id
        }
            
        return self.create_new_asset(asset, data)    
    
    
    def create_new_asset(self, asset, data, keypair=None, multiple=False):
        """Create a new BigchainDB asset.
        
        Args:
            asset (dict): a Python dictionary for the asset data.
            data (dict, optional): additional metadata to describe
                the asset.
            keypair: Public/private keypair for nonadmin user when
                creating a new asset without access restrictions
                (default: None).
            multiple (list or tuple): public keys of users assigned as
                "owners" of an asset, when there is more than one
                owner (default: False).
        
        """
        
        if keypair == None:
            keypair = self.admin_kp
        if multiple == False:
            tx = self.conn.transactions.prepare(
                    operation="CREATE",
                    signers=keypair.public_key,
                    asset=asset,
                    metadata=data)                
        else:
            # Muliple owners are specified with the "recipients"
            # keyword arg.
            tx = self.conn.transactions.prepare(
                    operation="CREATE",
                    signers=keypair.public_key,
                    recipients=multiple,
                    asset=asset,
                    metadata=data)
            
        # "Fulfill" the transaction by signing with a private key.
        signed_tx = self.conn.transactions.fulfill(
                tx, private_keys=keypair.private_key)                    
        
        # Commit the prepared transaction to the BigchainDB server.
        return self.conn.transactions.send_commit(signed_tx)
    
    
    def create_new_user(self, type_id, type_name, user_pubkey):
        """Create a new user and assign permissions.
        
        Args:
            type_id (str): Transaction ID of a group asset, used with
                the special link key to restrict a user to a specific
                group.
            type_name (str): Name of the user group.
            user_pubkey: Public key of the user. This is passed to a
                TRANSFER transaction to transfer ownership of the user
                asset from the admin to the user.
            
        """
        
        # Asset and metadata for the new user asset, created by 
        # the admin.
        asset = {"data": {
            "@context": {
                "name": "http://schema.org/name",
                "creator": "http://purl.org/dc/terms/creator",
                "label": "http://www.w3.org/2000/01/rdf-schema#label"
            },
            "name": type_name,
            "link": type_id,
            "creator": self.admin_kp.public_key,     
            "label": "UserAsset"                        
        }}
            
        data = {
            "@context": {
                "date": "http://purl.org/dc/terms/date",
                "schema": "http://schema.org/"
            },
            "@type": "Action",
            "schema:name": "User Added",
            "date": str(datetime.datetime.now()),
            "schema:additionalProperty": [
                {
                    "@type": "schema:PropertyValue",
                    "schema:name": "timestamp",
                    "schema:value": int(time.time())
                },
                {
                    "@type": "schema:PropertyValue",
                    "schema:name": "UserType",
                    "schema:value": type_name
                },
                {
                    "@type": "schema:PropertyValue",
                    "schema:name": "PublicKey",
                    "schema:value": user_pubkey
                }
            ]
        }
        
        # Instantiate the user as a new asset.
        user_tx = self.create_new_asset(asset, data)
        
        # Update the TRANSFER transaction metadata with a new description.
        data["schema:name"] = "User Assigned to Group"
        
        # Transfer the asset to the user it represents.
        self.transfer_asset(user_tx, user_pubkey, data)
        return user_tx
    
    
    def create_type(self, type_name, app_id, can_link_asset_id):
        
        asset = {"data": {
            "@context": {
                "schema": "http://schema.org/"
            },
            "schema:name": type_name,
            "link": app_id,
            "schema:identifier": {
                "@type": "PropertyValue",
                "schema:name": "namespace",
                "schema:value": self.namespace + "." + type_name
            }                     
        }}
        data = {
            "can_link": can_link_asset_id                
        }
        return self.create_new_asset(asset, data)
    
    
    def create_type_instance(self, type_name, type_id, asset, data, 
                             keypair):
        """Creates an instance of an asset type under RBAC regime.
        
        Args:
            type_name (str): Name of the asset type.
            type_id (str): Transaction ID of the type asset, used for
                linking.
            asset (dict): Asset to be created.
            data (dict): Additional description of asset to be created.
        
        """
        
        # Update the asset dict to include the "link" field and the
        # namespace qualifed by type name.
        asset["data"].update({"link": type_id})
        asset["data"].update({"schema:identifer": {
             "@type": "PropertyValue",
             "schema:name": "namespace",
             "schema:value": self.namespace + "." + type_name 
        }})                
        
        # Create the new asset under RBAC regime.
        return self.create_new_asset(asset, data, keypair=keypair)
    
    
    def transfer_asset(self, tx, user_pubkey, user_data):
        """Transfer user asset to pub key of the user it represents.
        
        Args:
            tx (dict): CREATE transaction object representing a new
                user.
            user_pubkey: Public key of the new user.
            user_data: Metadata to describe user permissions.
                
        """
        
        asset = {
            "id": tx["id"]
        }
        output_index = 0
        output = tx["outputs"][output_index]
        transfer_input = {
            "fulfillment": output["condition"]["details"],
            "fulfills": {
                "output_index": output_index,
                "transaction_id": tx["id"]
            },
            "owners_before": output["public_keys"]        
        }
        transfer_tx = self.conn.transactions.prepare(
            operation="TRANSFER",
            asset=asset,
            metadata=user_data,
            inputs=transfer_input,
            recipients=user_pubkey
        )
        signed_transfer_tx = self.conn.transactions.fulfill(
            transfer_tx,
            private_keys=self.admin_kp.private_key
        )
        return self.conn.transactions.send_commit(signed_transfer_tx)
    
   