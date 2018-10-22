#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 21 09:20:58 2018

@author: tat2
"""

from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
from bigchaindb_rbac import BigchainDB_RBAC

BDB_ROOT_URL = "http://localhost:9984"
IUL = generate_keypair()

bdb = BigchainDB(BDB_ROOT_URL)

bf_item = {"data": {    
    "@type": "http://id.loc.gov/ontologies/bibframe/Item"
}}

iul_bf_item_metadata = {
    "@context": {
        "bf": "http://id.loc.gov/ontologies/bibframe/",
        "bflc": "http://id.loc.gov/ontologies/bflc/",
        "rdfs": "rdfs:"
    },
    "@graph": [
        {
            "@id": "http://example.org/ocm05084045#Item050-8",
            "@type": ["bf:Item"],
            "bf:heldBy": [{"@id": "http://id.loc.gov/vocabulary/organizations/inuli"}],
            "bf:itemOf": [{"@id": "http://example.org/ocm05084045#Instance"}],
            "bf:note": [
                {"@id": "_:N981e348f02414549b1f45d3c4fd27c9f"},
                {"@id": "_:Ne3fc3e8f6e114267a9c92869846eacaa"},
                {"@id": "_:N5d07eeca480f4e49a76445d0b017b5cb"},
                {"@id": "_:N0d5051ba76e24fcfab1392c5105f4981"},
                {"@id": "_:N3047d53d3f1c4e77a5c432c5ae5118f2"},
                {"@id": "_:N0194bf02bfc2457db18150714c9e9fd4"},
                {"@id": "_:Nc7fe3b12110a4d24b842a787acbe3ba5"},
                {"@id": "_:Nae49e8c1a2724cb3a1e32b9caabaab87"}
            ],
            "bf:shelfMark": [{"@id": "_:N86583b665c5a48bea6e69601f242ca82"}]
        },
        {
            "@id": "_:N981e348f02414549b1f45d3c4fd27c9f",
            "@type": ["bf:Note"],
            "rdfs:label": [{"@value": "First book printed from movable types in Europe; New Testament only from v. 2,in itself imperfect. GKW 4201 (\"not after Aug. 1456\"). BMC I, p. 17; Lilly Library Publication V, no. 1 (this copy, described in extenso); Goff B-526. Removed in 1953 from copy of v. 2 known as Trier II, in censuses as De Ricci 15 [b], Schwenke 14, Lazare 42, Norman 34."}]
        },
#        {
#            "@id": "_:N981e348f02414549b1f45d3c4fd27c9f",
#            "@type": ["http://id.loc.gov/ontologies/bibframe/Note"],
#            "http://www.w3.org/2000/01/rdf-schema#label": [{"@value": "First book printed from movable types in Europe; New Testament only from v. 2,in itself imperfect. GKW 4201 (\"not after Aug. 1456\"). BMC I, p. 17; Lilly Library Publication V, no. 1 (this copy, described in extenso); Goff B-526. Removed in 1953 from copy of v. 2 known as Trier II, in censuses as De Ricci 15 [b], Schwenke 14, Lazare 42, Norman 34."}]
#        },
        {
            "@id": "_:N86583b665c5a48bea6e69601f242ca82",
            "@type": ["bf:ShelfMarkLcc"],
            "rdfs:label": [{"@value": "BS75 1454"}]
        },
        {
            "@id": "_:Ne3fc3e8f6e114267a9c92869846eacaa",
            "@type": ["bf:Note"],
            "rdfs:label": [{"@value": "Provenance: Trier--Wiernick--Rosenbach--Houghton--Scribner--Poole."}]
        },
        {
            "@id": "_:N5d07eeca480f4e49a76445d0b017b5cb",
            "@type": ["bf:Note"],
            "rdfs:label": [{"@value": "Misbound. Collates (as GKW): [II--t9 ( -t10) v-xp10s yp10s ( -y6,9) zp10s Ap10s ( -A4) B-Cp10s Ep11s ( -E2,6) Dp12s ( -D1) F-Gp10s Hp5s ( -H1) Ip10s ( -I5-10)]. Missing leaves replaced with blanks."}]
        },
        {
            "@id": "_:N0d5051ba76e24fcfab1392c5105f4981",
            "@type": ["bf:Note"],
            "rdfs:label": [{"@value": "A few contemporary and later marginalia; ms. table of contents v. 2 dated 1569; later notes by Wyttenbach and others of Trier Stadtbibliothek."}]
        },
        {
            "@id": "_:N3047d53d3f1c4e77a5c432c5ae5118f2",
            "@type": ["bf:Note"],
            "rdfs:label": [{"@value": "Assigned title; first leaf present begins: Beatissimo pape damaso ieronim(us) ..."}]
        },
        {
            "@id": "_:N0194bf02bfc2457db18150714c9e9fd4",
            "@type": ["bf:Note"],
            "rdfs:label": [{"@value": "Initials supplied in colors, incipits in red, chapter numbers red and/or black."}]
        },
        {
            "@id": "_:Nc7fe3b12110a4d24b842a787acbe3ba5",
            "@type": ["bf:Note"],
            "rdfs:label": [{"@value": "Imperfect: lacks all before II:190; for numbers and text of missing N.T. leaves, cf. Lilly Library Publication V."}]
        },
        {
            "@id": "_:Nae49e8c1a2724cb3a1e32b9caabaab87",
            "@type": ["bf:Note"],
            "rdfs:label": [{"@value": "Bound in 16th-century calf over wooden boards, tooled in blind, defective; rebacked."}]
        }
    ]
}

def main():
      
    iul = BigchainDB_RBAC(bdb, IUL)
       
    iul_cataloger = generate_keypair()
    
    try:        
        sample_iul_item = iul.create_new_asset(bf_item, 
                                               iul_bf_item_metadata, 
                                               iul_cataloger, 
                                               (iul_cataloger.public_key, 
                                                IUL.public_key)) 
        print("Sample IUL Item: ", sample_iul_item)
    except Exception as e:
        print(e)
        
if __name__ == "__main__":
    # Execute only if run as a script
    main()
