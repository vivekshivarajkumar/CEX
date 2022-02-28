from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from WalletDB import WalletDB
from WalletOperations import WalletOperations

app = FastAPI()


class Address(BaseModel):
    address: str


@app.post("/createAccount")
async def add_account(main_address: Address):
    wo = WalletOperations()
    return wo.add_address(main_address.address)


@app.get("/getPublicAddress/{main_address}")
async def get_public_address(main_address):
    wo = WalletOperations()
    try:
        return wo.get_address_from_user_id(main_address)
    except:
        raise HTTPException(status_code=404, detail="main address not found")


@app.get("/getBalance/{main_address}")
async def get_balance(user_id):
    wdb = WalletDB()
    return wdb.get_balance(wdb.get_public_key(user_id))


@app.post("/withdraw")
async def withdraw(user_id, target_address, amount):
    return WalletOperations().withdraw(user_id, target_address, amount)
