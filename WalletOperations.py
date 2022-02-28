from fastapi.responses import JSONResponse
from fastapi import status

from WalletDB import WalletDB
from web3 import Web3

from TokenOperations import TokenOperations

gaj_token_address = "0x30c192788496fAC4BB212d2f733409755051C648"
gaj_token_abi = '[{"inputs": [{"internalType": "string", "name": "name", "type": "string"}, {"internalType": "string", "name": "symbol", "type": "string"}, {"internalType": "uint256", "name": "initialSupply", "type": "uint256"}], "stateMutability": "nonpayable", "type": "constructor"}, {"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "owner", "type": "address"}, {"indexed": true, "internalType": "address", "name": "spender", "type": "address"}, {"indexed": false, "internalType": "uint256", "name": "value", "type": "uint256"}], "name": "Approval", "type": "event"}, {"inputs": [{"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "subtractedValue", "type": "uint256"}], "name": "decreaseAllowance", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "addedValue", "type": "uint256"}], "name": "increaseAllowance", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "to", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "transfer", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}, {"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "from", "type": "address"}, {"indexed": true, "internalType": "address", "name": "to", "type": "address"}, {"indexed": false, "internalType": "uint256", "name": "value", "type": "uint256"}], "name": "Transfer", "type": "event"}, {"inputs": [{"internalType": "address", "name": "from", "type": "address"}, {"internalType": "address", "name": "to", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "transferFrom", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "owner", "type": "address"}, {"internalType": "address", "name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "decimals", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "name", "outputs": [{"internalType": "string", "name": "", "type": "string"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "symbol", "outputs": [{"internalType": "string", "name": "", "type": "string"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "totalSupply", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]'


class WalletOperations(object):
    def __init__(self):
        self.token_operation = TokenOperations(gaj_token_address, gaj_token_abi)
        self.tokens_managed = ["GAJ", "ETH", "TT"]

    # def get_address_from_index(self, index):
    #     master_key = HDPrivateKey.master_key_from_mnemonic(self.mnemonic)
    #     root_keys = HDKey.from_path(master_key, self.path)
    #     acct_priv_key = root_keys[-1]
    #     keys = HDKey.from_path(acct_priv_key, '{change}/{index}'.format(change=0, index=index))
    #     private_key = keys[-1]
    #     public_key = private_key.public_key
    #     return public_key.address()

    @staticmethod
    def get_address_from_user_id(user_id):
        wdb = WalletDB()
        pub_key = wdb.get_public_key(user_id)
        return pub_key

    def add_address(self, user_id):
        wdb = WalletDB()
        if not isinstance(wdb.get_public_key(user_id), JSONResponse):
            return JSONResponse(status_code=status.HTTP_200_OK, content="Address already exist")
        index = int(wdb.get_max_address_index()) + 1
        print("index ", index)
        public_address = self.token_operation.get_address_from_index(index)
        wdb.add_entry(index, user_id, public_address)
        return public_address

    def get_balance_of_account(self, public_address):
        token_balance = self.token_operation.contract.functions.balanceOf(Web3.toChecksumAddress(public_address)).call()
        return token_balance

    def withdraw(self, user_id, withdraw_account, amount):
        """
        :return:
        """
        amount = int(amount)
        wdb = WalletDB()
        if int(wdb.get_balance(wdb.get_public_key(user_id))) < amount:
            return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content="Insufficient amount")
        token_address, to, _from, txn_hash = self.token_operation.transfer_from_central_wallet(withdraw_account, amount)
        wdb.reduce_balance(user_id, amount)
        return wdb.add_txn(amount, token_address, to, _from, txn_hash.hex(), txn_type="withdraw")

    def transfer_to_central_wallet(self, public_key, new_balance):
        wdb = WalletDB()
        cw_public_key = "0x6f54AE0A9EF914C71bce845054C4922ceA6a01Bd".lower()
        index = wdb.get_index(public_key)
        if index is None:
            return
        if self.token_operation.rinkeby.eth.get_balance(Web3.toChecksumAddress(public_key)) < Web3.toWei(0.001, 'ether'):
            self.token_operation.transfer_gas_fund_to_wallet(public_key)
        return self.token_operation.transfer_to_central_wallet(index, public_key.lower(), cw_public_key, new_balance)
