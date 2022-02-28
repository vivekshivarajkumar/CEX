import json
import time

from web3 import Web3
from web3.middleware import geth_poa_middleware
from GAJ_token import  gaj_token_address, gaj_token_abi

from crypto.crypto import HDPrivateKey, HDKey


class TokenOperations(object):
    def __init__(self, contract_address, abi):
        details = json.load(open("/Users/gajendraks/Documents/workspace/Taro/storage/secret.json"))
        self.mnemonic = details['mnemonic']
        self.path = "m/44'/60'/0'"
        self.rinkeby = Web3(Web3.HTTPProvider("https://eth-rinkeby.alchemyapi.io/v2/AfLxt6Bv1wBDTR1RCHSgER_00yqnYnW4"))
        self.rinkeby.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.rinkeby.isConnected()
        self.token_contracts = {
            "gaj_token": self.rinkeby.eth.contract(address=gaj_token_address, abi=abi)
        }
        self.contract = self.rinkeby.eth.contract(address=contract_address, abi=abi)

    def get_address_from_index(self, index):
        master_key = HDPrivateKey.master_key_from_mnemonic(self.mnemonic)
        root_keys = HDKey.from_path(master_key, self.path)
        acct_priv_key = root_keys[-1]
        keys = HDKey.from_path(acct_priv_key, '{change}/{index}'.format(change=0, index=index))
        private_key = keys[-1]
        public_key = private_key.public_key
        return public_key.address()

    def transfer_to_central_wallet(self, index, from_adddress, to_address, value):
        master_key = HDPrivateKey.master_key_from_mnemonic(self.mnemonic)
        root_keys = HDKey.from_path(master_key, self.path)
        acct_priv_key = root_keys[-1]
        keys = HDKey.from_path(acct_priv_key, '{change}/{index}'.format(change=0, index=index))
        private_key = keys[-1]
        central_public_key = private_key.public_key.address()
        if private_key.public_key.address() == from_adddress:
            print(f'info - {to_address} - {central_public_key}')
            txn = self.contract.functions.transfer(Web3.toChecksumAddress(to_address), value).buildTransaction({
                'from': Web3.toChecksumAddress(central_public_key)
            })
            txn.update({'nonce': self.rinkeby.eth.get_transaction_count(Web3.toChecksumAddress(central_public_key))})
            print(f'txn is {txn}')
            signed_tx = self.rinkeby.eth.account.sign_transaction(txn, private_key._key.key)
            txn_hash = self.rinkeby.eth.send_raw_transaction(signed_tx.rawTransaction)
            txn_receipt = self.rinkeby.eth.wait_for_transaction_receipt(txn_hash)
            curr_time = time.time()
            while time.time() < curr_time+600:
                if txn_receipt.status:
                    return True
            return txn_receipt.status
        else:
            raise Exception("public key is not matching with index")

    def transfer_gas_fund_to_wallet(self, dest_address):
        """ Transfer fund for gas from the fund wallet """
        private_key = "1910f87dbccc6bfaaf937e7a4f3f6b5a0f77df7e2befab292224f82edcfd7958"
        public_key = Web3.toChecksumAddress("0xAEf63a9A8fe5EAcf8d15f9916d77eCb95b805513")
        nonce = self.rinkeby.eth.get_transaction_count(public_key)
        txn = {
            'to': Web3.toChecksumAddress(dest_address),
            'value': int(0.05*10**18),
            'nonce': nonce,
            'gasPrice': self.rinkeby.toWei(40, 'gwei'),
            # 'maxPriorityFeePerGas': self.rinkeby.eth.max_priority_fee,
        }
        txn['gas'] = self.rinkeby.eth.estimate_gas(txn)

        signed_tx = self.rinkeby.eth.account.sign_transaction(txn, private_key)
        txn_hash = self.rinkeby.eth.send_raw_transaction(signed_tx.rawTransaction)
        txn_receipt = self.rinkeby.eth.wait_for_transaction_receipt(txn_hash)
        curr_time = time.time()
        while time.time() < curr_time + 600:
            if txn_receipt.status:
                return True, txn_hash
        return txn_hash, txn_receipt.status

    def transfer_from_central_wallet(self, withdraw_account, amount):
        cw_private_key = "a26350fdedddc98cc196c569bb0c6347846ba2154ea00a32f1a2db7652722aa4".lower()
        cw_public_key = Web3.toChecksumAddress("0x6f54AE0A9EF914C71bce845054C4922ceA6a01Bd")
        withdraw_account = Web3.toChecksumAddress(withdraw_account)
        txn = self.contract.functions.transfer(withdraw_account, amount).buildTransaction({
            'from': cw_public_key
        })
        txn.update({'nonce': self.rinkeby.eth.get_transaction_count(cw_public_key)})
        signed_tx = self.rinkeby.eth.account.sign_transaction(txn, cw_private_key)
        txn_hash = self.rinkeby.eth.send_raw_transaction(signed_tx.rawTransaction)
        txn_receipt = self.rinkeby.eth.wait_for_transaction_receipt(txn_hash)

        if txn_receipt.status:
            return self.contract.address, withdraw_account, cw_public_key, txn_hash
        else:
            raise Exception("Waited for txn receipt but failed")

