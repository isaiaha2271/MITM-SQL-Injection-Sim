# MITM-SQL-Injection-Sim
Final Project for CECS 478



## Overview
This project simulates a combined Man-in-the-Middle (MITM) and SQL Injection attack using Docker containers. It demonstrates how attackers can intercept user credentials over a network and exploit vulnerable web applications to access or modify database data.


## Architecture
The system consists of:
- A vulnerable web server
- A MySQL database storing user data
- An attacker container using mitmproxy as a transparent proxy
- A victim/client interacting with the system

## Goals
- Demonstrate credential interception via MITM
- Show SQL injection exploitation
- Complete a full attack chain resulting in data exfiltration

## Data Flow
victim → attacker (mitmproxy) → destination server
         ↓
     logs flows.jsonl
         ↓
   export_summary.py
         ↓
   summary.json (artifacts)
