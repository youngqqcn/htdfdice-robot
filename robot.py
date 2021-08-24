# coding:utf8

# author: yqq
# date: 2021/08/24
# descriptions:

from binascii import unhexlify
import json
import time
from pprint import pprint
from eth_utils import remove_0x_prefix, to_checksum_address
from htdfsdk import HtdfRPC, Address, HtdfPrivateKey, HtdfTxBuilder, HtdfContract, htdf_to_satoshi
import coincurve
import os
import requests
import urllib
import random

PARAMETERS_INNER = {
    'CHAINID': 'mainchain',
    'ADDRESSES':[
        ['htdf153s24ytf8yppyjwgtyzf0qnzgneqzd7ppza2j4', '354894d90d2634d95c9bf99394816fd898eaca8af00898304894c0581803a0af'],
        # ['htdf14hmedh4k5nkknd9cxd44xap57pkpx4hf3tglmq', '35c18f20a139dbb1bf4cc8e2ffe1e98e39033355173adcc2036c2bc3e44c0417'],
        # ['htdf1cgttvkveda4nh505smww4cge6st050nrrvurz7', '45a766778f1d95f6fa4944943b71435a66018cded9f0664346c3b7b3615953e4'],
        # ['htdf1j5mrg7a8f67c8vmm6yt3gt27lzxffhd9pepvv3', 'ee0d56da7711069e61ba38b4e8c6092f23e0b6a6d5fb96cee9bb0a29e209b371'],
        # ['htdf1t5pmycu9dgamt6r0n3q6zdkff4pdclr40hwvve', '37159db6ba92bc5cdce58338072a13afeb308b807d2429938907211fe69aa7d4'],
        # ['htdf1xsr63as7jfklugeljwque5tur89vyuys3tywwh', '04b7c165b51565f23865a531d780ae724b3d31bc0fa69892ff038bff505c9c7c'],
        # ['htdf13ap5jz3f4dgy7sju24933tffdp9wr4mr4jjn2q', 'e348545c169dd8e1119baf0c575ba089d243900a27fa93fad9b2f4a023e44805'],
        # ['htdf1fhkmsacy424qds604rhx2vvuy8gk8y3j3cthz0', 'e3ad0e9a580438a568715d97a0fd17ca5a205d35083e749af63fe5760359ded5'],
        # ['htdf15p9tq45x5atx9kacq36394uum6286tce6qssh0', 'c2188df3497b340d9ec28106c2e5992a6863fee0e80010664f8202fc22cf0da0'],
        # ['htdf19w3u747se39xurn7vs9uc3llm8eqds65ql3p9j', '1c79909384e4c06eda903fd3c16760943bd5876a50d01499c61ed7e397b399a1'],
    ],
    'RPC_HOST': 'htdf2020-node03.orientwalt.cn',
    'RPC_PORT': 1317,
    'SLEEP_SECS': 3600,    # 一个小时1笔
    'CONTRACT_ADDRESS': 'htdf166666662sqxwuj2yzv7mnuqny8cwrvz5fgnypr', # 智能合约地址
    'GAS_PRICE': 100,
    'GAS_WANTED': 200000,
    'BET_AMOUNT_RANGE': [1, 2] , #下注金额范围， 1~2HTDF
}


def parse_truffe_compile_outputs(json_path: str):
    with open(json_path, 'r') as infile:
        compile_outputs = json.loads(infile.read())
        abi = compile_outputs['abi']
        bytecode = compile_outputs['bytecode']
        bytecode = bytecode.replace('0x', '')
        return abi, bytecode


def get_bet_data(type, bet, money=1, addrto = '', addrfrom = ''):
    url = 'https://dapp.htdfscan.me/-/blockchain/htdf/dapp/server/bet'

    if isinstance(bet, list):
        bet = ','.join( [ str(x) for x in bet ] )

    form_data = {
        'from': addrfrom,
        'to': addrto,
        'money': money,
        'type': type,
        'bet': bet,
    }
    rsp = requests.post(url, data=form_data)
    if rsp.status_code != 200:
        return None
    rsp = rsp.json()
    return rsp['data']['data']


def get_random_bet():
    bet_type = random.choice([1, 2, 3])
    if 1 == bet_type:
        return bet_type, random.choice([1, 2]) # 抛硬币
    elif 2 == bet_type:
        return bet_type, random.sample(range(1, 7), random.randint(1, 5)) # 一个骰子
    elif 3 == bet_type:
        return bet_type, random.sample(range(2, 12), random.randint(1, 10)) # 两个骰子
    else:
        raise Exception("Invalid bet type")
    pass


def placeBet(conftest_args, abi):
    """
    自动下注
    """

    htdfrpc = HtdfRPC(
        chaid_id=conftest_args['CHAINID'],
        rpc_host=conftest_args['RPC_HOST'],
        rpc_port=conftest_args['RPC_PORT'])

    bet_amount_range = conftest_args['BET_AMOUNT_RANGE']

    gas_price = conftest_args['GAS_PRICE']
    gas_wanted = conftest_args['GAS_WANTED']
    bet_amount_satoshi = htdf_to_satoshi(random.randint(bet_amount_range[0], bet_amount_range[1])) + random.randint(0, 9) * 10**7

    contract_address = Address(conftest_args['CONTRACT_ADDRESS'])
    hc = HtdfContract(rpc=htdfrpc, address=contract_address, abi=abi)

    from_addr = None
    private_key = None
    from_acc = None

    addrs = conftest_args['ADDRESSES']
    while True:
        item = random.choice(addrs)
        from_acc = htdfrpc.get_account_info(address=item[0])
        if from_acc.balance_satoshi >= gas_price * gas_wanted + bet_amount_satoshi:
            from_addr = Address(item[0])
            private_key = HtdfPrivateKey(item[1])
            break

        print("======>WARNING: 地址 {} 余额不足, 当前余额: {}satoshi"
                    .format(from_acc.address, from_acc.balance_satoshi))

        addrs = addrs.remove(item)
        if len(addrs) == 0:
            raise Exception("======>ERROR： 所有的地址余额不足")


    bet_type, bets = get_random_bet()
    print('bet_type: {}, bets: {}'.format(bet_type, bets))
    data = get_bet_data(type=bet_type, bet=bets)
    # print('======')
    # print(data)
    # print('======')
    # return
    signed_tx = HtdfTxBuilder(
        from_address=from_addr,
        to_address=contract_address,
        amount_satoshi=bet_amount_satoshi,
        sequence=from_acc.sequence,
        account_number=from_acc.account_number,
        chain_id=htdfrpc.chain_id,
        gas_price=gas_price,
        gas_wanted=gas_wanted,
        data=data,
        memo=''
    ).build_and_sign(private_key=private_key)

    tx_hash = htdfrpc.broadcast_tx(tx_hex=signed_tx)
    print('tx_hash: {}'.format(tx_hash))

    tx = htdfrpc.get_transaction_until_timeout(transaction_hash=tx_hash)
    pprint(tx)
    pass


def main():
    abi, bytecode = parse_truffe_compile_outputs('./Dice2Win.json')
    sleep_secs = PARAMETERS_INNER['SLEEP_SECS']
    while True:
        try:
            placeBet(conftest_args=PARAMETERS_INNER, abi=abi)
        except Exception as e:
            print(e)
        finally:
            time.sleep(sleep_secs)
    pass


if __name__ == '__main__':
    main()
    pass
