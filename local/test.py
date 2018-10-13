#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 12 17:41:14 2018

@author: tat2
"""
from bigchaindb_driver.crypto import generate_keypair

print("Testing")

alice = generate_keypair()

print(alice)

