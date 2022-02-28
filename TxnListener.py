# import the following dependencies
import json
import logging
import traceback

from web3 import Web3
from GAJ_token import gaj_token_address, gaj_token_abi
import asyncio

from WalletDB import WalletDB

rinkeby = Web3(Web3.HTTPProvider("https://eth-rinkeby.alchemyapi.io/v2/AfLxt6Bv1wBDTR1RCHSgER_00yqnYnW4"))
from web3.middleware import geth_poa_middleware

rinkeby.middleware_onion.inject(geth_poa_middleware, layer=0)
rinkeby.isConnected()

# uniswap address and abi
contract = rinkeby.eth.contract(address=gaj_token_address, abi=gaj_token_abi)


# define function to handle events and print to the console
def handle_event(event):
    # event_dict = Web3.toJSON(event)
    print(dir(event))
    print(type(event.transactionHash), event.transactionHash)
    # print(dir(event.args))
    # print(Web3.toJSON(event.args))
    try:
        wdb = WalletDB()
        wdb.add_txn(event.args.value, event.address, event.args.to,
                    json.loads(Web3.toJSON(event.args))['from'],
                    event.transactionHash.hex())
        # wdb.watch_and_act(event.args.to, event.address)
    except Exception as err:
        logging.error(f"Exception while handling event with txn_has - {event.transactionHash.hex()} is {err}")
        logging.error(f'traceback is {traceback.format_exc()}')


# asynchronous defined function to loop
# this loop sets up an event filter and is looking for new entires for the "PairCreated" event
# this loop runs on a poll interval
async def log_loop(event_filter, poll_interval):
    print("started listening")
    while True:
        for Transfer in event_filter.get_new_entries():
            handle_event(Transfer)
        await asyncio.sleep(poll_interval)


# when main is called
# create a filter for the latest block and look for the "PairCreated" event for the uniswap factory contract
# run an async loop
# try to run the log_loop function above every 2 seconds
def main():
    event_filter = contract.events.Transfer.createFilter(fromBlock='latest')
    # block_filter = web3.eth.filter('latest')
    # tx_filter = web3.eth.filter('pending')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(
                log_loop(event_filter, 2)))
        # log_loop(block_filter, 2),
        # log_loop(tx_filter, 2)))
    finally:
        # close loop to free up system resources
        loop.close()


if __name__ == "__main__":
    main()
