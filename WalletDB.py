from fastapi.responses import JSONResponse
from fastapi import status
import sqlite3


class WalletDB(object):
    def __init__(self):
        self.db_connection = sqlite3.connect("wallet.db")
        self.cursor = self.db_connection.cursor()

    @staticmethod
    def sql_commands():
        """create table transaction_table(
        id integer primary key autoincrement,
        type text,
        amount text,
        sender text,
        recepient text,
        txn_hash text,
        token_address text);"""

        """create table wallet_table(
        address_index integer,
        userId text,
        public_key text,
        balance text,
        UNIQUE(userId, address_index, public_key),
        primary key(userId, address_index));"""

    def add_entry(self, address_index, user_id, public_key):
        query_string = f"insert into wallet_table(address_index, userId, public_key, balance) values({address_index}, " \
                       f"'{user_id}', '{public_key}', '0');"
        with self.db_connection:
            self.cursor.execute(query_string)

    def get_max_address_index(self):
        query_string = "select max(address_index) from wallet_table;"
        with self.db_connection:
            self.cursor.execute(query_string)
        value = self.cursor.fetchall()[0][0]
        if value is None:
            return 0
        return value

    def get_public_key(self, user_id):
        query_string = f"select public_key from wallet_table where userId='{user_id}';"
        with self.db_connection:
            self.cursor.execute(query_string)
        value = self.cursor.fetchall()
        if not value:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User id doesn't exist")
        return value[0][0]

    def add_txn(self, value, token_address, to, _from, txn_hash, txn_type="deposit"):
        to = to.lower()
        print("types - {}".format((type(to), type(_from), type(txn_hash))))
        print(f"to is {to}")
        self.add_transaction(value, token_address, to, _from, txn_hash)
        transfer_amount = (self.get_balance(to) or 0) + value
        print(f"transfer_amount {transfer_amount}")
        threshold = 1*10**18
        update_query = f"update wallet_table set balance = '{transfer_amount}' where public_key='{to}';"
        with self.db_connection:
            self.cursor.execute(update_query)
        if txn_type.lower() == "deposit" and transfer_amount > threshold:
            from WalletOperations import WalletOperations
            wo = WalletOperations()
            return wo.transfer_to_central_wallet(to, transfer_amount)
        else:
            return True

    def add_transaction(self, value, token_address, to, _from, txn_hash):
        print("txn_hash - {}".format(txn_hash))
        _type = "Deposit" if _from != "0x6f54AE0A9EF914C71bce845054C4922ceA6a01Bd" else "Withdraw"
        query_string = f"insert into transaction_table(type, amount, sender, recepient, txn_hash, token_address) " \
                       f"values('{_type}', '{value}', '{_from}', '{to}', '{txn_hash}', '{token_address}');"
        print(f"query_string is {query_string}")
        with self.db_connection:
            self.cursor.execute(query_string)

    def get_balance(self, public_key):
        query_string = f"select balance from wallet_table where public_key='{public_key}';"
        with self.db_connection:
            self.cursor.execute(query_string)
        value = self.cursor.fetchall()
        if not value:
            return None
        value = value[0][0]
        return int(value or 0)

    def reduce_balance(self, user_id, balance_change):
        pk = self.get_public_key(user_id)
        if not pk:
            raise Exception("user_id not found")
        new_balance = self.get_balance(pk) - balance_change
        query_str = f"update wallet_table set balance = '{new_balance}' where userId='{user_id}';"
        with self.db_connection:
            self.cursor.execute(query_str)

    def get_index(self, public_key):
        public_key = public_key.lower()
        query_string = f"select address_index from wallet_table where public_key='{public_key}';"
        with self.db_connection:
            self.cursor.execute(query_string)
        value = self.cursor.fetchall()
        if not value:
            return None
        return value[0][0]

    def __del__(self):
        self.cursor.close()
        self.db_connection.close()