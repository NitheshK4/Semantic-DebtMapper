#!/bin/bash
cd "/Users/nitheshkumar/Documents/Semantic Debt Mapper /backend"
export DATABASE_URL=sqlite:///./sdm.db
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8005 --reload
