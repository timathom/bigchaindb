#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later

"""Illustration of how the blockchain database BigchainDB might be 
deployed as a shared cataloging database for academic and research 
libraries. 

Uses the BigchainDB Role-Based Access Control extension (available in the 
rbac branch of the BigchainDB GitHub repository) to show how user roles and 
permissions might be managed in this context. 

Adapted from:
     - https://github.com/bigchaindb/project-jannowitz/tree/master/rbac

@author: timathom@indiana.edu
"""

import json

from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
from rbac import BigchainRbac

# Set constants and generate keypairs for admin users.
BDB_ROOT_URL = "http://localhost:9984"
YUL = generate_keypair()
HLS = generate_keypair()
DLC = generate_keypair()
IUL = generate_keypair()
APP_NAME = "Shared Library Catalog"
NAMESPACE = "org.library.catalog"

# Connection to BigchainDB
bdb = BigchainDB(BDB_ROOT_URL)
     
# Stub data for creating assets for demo library catalog entries in 
# BigchainDB.
bf_work = {"data": {
    "@context": {
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "schema": "http://schema.org/"
    },
    "@type": [
        "http://id.loc.gov/ontologies/bibframe/Work",
        "http://id.loc.gov/ontologies/bibframe/Text"
    ],
    "rdfs:label": "Bible. Latin. Vulgate. 1454."
}}

bf_instance = {"data": {
    "@context": {
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "schema": "http://schema.org/"
    },
    "@type": "http://id.loc.gov/ontologies/bibframe/Instance",
    "rdfs:label": "Biblia latina."
}}

bf_item = {"data": {    
    "@context": {
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "schema": "http://schema.org/"
    },
    "@type": "http://id.loc.gov/ontologies/bibframe/Item"
}}

with open('../../project-data/gutenberg-work.json') as work:
    work_data = json.load(work)

with open('../../project-data/gutenberg-iul-instance.json') as instance:
    instance_data = json.load(instance)   

with open('../../project-data/gutenberg-iul-item.json') as item:
    item_data = json.load(item)


def main():
    """Examples of managing user permissions in BigchainDB."""
    
    # Instantiate the RBAC interface
    iul = BigchainRbac(bdb, NAMESPACE, APP_NAME, IUL, [YUL.public_key, 
                                                       HLS.public_key, 
                                                       DLC.public_key, 
                                                       IUL.public_key])        
    
    # User keypairs. IUL, etc., represent Admin keypairs.
    iul_cataloger = generate_keypair()
    iul_technician = generate_keypair()
        
    public_keys = (iul.admin_kp.public_key, iul_cataloger.public_key, 
                   iul_technician.public_key)

    # Print public keys for reference.    
    print("Public keys: ", public_keys)
    
    # Create assets for App and Users.
    # Create Admin user type: represents the Admin group.
    admin_group_id = iul.bootstrap_admin_group()["id"]
    
    print("Admin Group: ", admin_group_id)
    
    # Create the asset representing the top-level App.
    app_id = iul.bootstrap_app(admin_group_id)["id"]

    print(APP_NAME + ": ", app_id)
    
    # Create an individual Admin user asset, linked to the Admin group.
    iul_admin_user_id = iul.create_new_user(admin_group_id, "admins", 
                                            IUL.public_key)["id"]
    
    print("Lilly Library Admin User: ", iul_admin_user_id)     
    
    # Create a new user type for catalogers.
    cataloging_group_id = iul.create_type("catalogers", app_id, 
                                          admin_group_id)["id"]    
    
    print("Catalogers Group: ", cataloging_group_id)
    
    # Create an asset to represent an individual cataloger.
    iul_cataloger_id = iul.create_new_user(cataloging_group_id, 
                                           "catalogers", 
                                           iul_cataloger.public_key)["id"]
    
    print("IUL Cataloger: ", iul_cataloger_id)
    
    # Create a new user type for paraprofessionals.
    technician_group_id = iul.create_type("paraprofessionals", app_id,
                                          admin_group_id)["id"]    
    
    print("Paraprofessionals Group: ", technician_group_id)
    
    # Create an asset to represent an individual paraprofessional.
    iul_technician_id = iul.create_new_user(technician_group_id,
                                            "paraprofessionals",
                                            iul_technician.public_key)["id"]
    
    print("IUL Paraprofessional: ", iul_technician_id)
    
    
    # Create assets for cataloging resources.
    # Create a new type for BIBFRAME Work descriptions.
    bf_works_group_id = iul.create_type("BIBFRAME_works", app_id, 
                                        cataloging_group_id)["id"]
    
    print("BIBFRAME Works Group: ", bf_works_group_id)

    # Test RBAC permissions.
    # A cataloger should be able to create a new asset representing
    # an instance of the Work type.
    try:
        cataloger_work_asset = iul.create_type_instance("BIBFRAME_work", 
                                                        bf_works_group_id, 
                                                        bf_work, work_data, 
                                                        iul_cataloger)        
        
        print("BIBFRAME Work (IUL Catalogers): ", cataloger_work_asset["id"])
        
    except Exception as e:
        print(e)
    
    # A paraprofessional should not be able to create a new asset 
    # representing an instance of the Work type. This transaction
    # should fail with a ValidationError.
    try:        
        technician_work_asset = iul.create_type_instance("BIBFRAME_work",
                                                         bf_works_group_id, 
                                                         bf_work, work_data, 
                                                         iul_technician)    
        
        print("BIBFRAME Work (IUL Paraprofessionals): ", 
              technician_work_asset["id"])
        
    except Exception as e:        
        print("BIBFRAME Work (IUL Paraprofessionals): ", e)
    
    # Create local cataloging resource assets (Instance and Item)
    # and associate them with two "owners": the Admin user and
    # the cataloger.
    try:
        instance_data["@graph"][0].update(
                {"parent": cataloger_work_asset["id"]})
        
        iul_instance_asset = iul.create_new_asset(bf_instance, instance_data,
                                                  iul_cataloger,
                                                  (iul_cataloger.public_key,
                                                   IUL.public_key))
        
        print("IUL BIBFRAME Instance: ", iul_instance_asset["id"])
        
    except Exception as e:
        print(e)
    
    try:    
        item_data["@graph"][0].update(
                {"parent": iul_instance_asset["id"]})
        
        iul_item_asset = iul.create_new_asset(bf_item, item_data, 
                                              iul_cataloger,
                                              (iul_cataloger.public_key, 
                                               IUL.public_key))
        
        print("IUL BIBFRAME Item: ", iul_item_asset["id"])
        
    except Exception as e:
        print(e)
        
    
if __name__ == "__main__":
    # Execute only if run as a script
    main()
