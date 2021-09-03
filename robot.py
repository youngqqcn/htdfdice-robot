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
        ['htdf14hmedh4k5nkknd9cxd44xap57pkpx4hf3tglmq', '35c18f20a139dbb1bf4cc8e2ffe1e98e39033355173adcc2036c2bc3e44c0417'],
        ['htdf1cgttvkveda4nh505smww4cge6st050nrrvurz7', '45a766778f1d95f6fa4944943b71435a66018cded9f0664346c3b7b3615953e4'],
        ['htdf1j5mrg7a8f67c8vmm6yt3gt27lzxffhd9pepvv3', 'ee0d56da7711069e61ba38b4e8c6092f23e0b6a6d5fb96cee9bb0a29e209b371'],
        ['htdf1t5pmycu9dgamt6r0n3q6zdkff4pdclr40hwvve', '37159db6ba92bc5cdce58338072a13afeb308b807d2429938907211fe69aa7d4'],
        ['htdf1xsr63as7jfklugeljwque5tur89vyuys3tywwh', '04b7c165b51565f23865a531d780ae724b3d31bc0fa69892ff038bff505c9c7c'],
        ['htdf13ap5jz3f4dgy7sju24933tffdp9wr4mr4jjn2q', 'e348545c169dd8e1119baf0c575ba089d243900a27fa93fad9b2f4a023e44805'],
        ['htdf1fhkmsacy424qds604rhx2vvuy8gk8y3j3cthz0', 'e3ad0e9a580438a568715d97a0fd17ca5a205d35083e749af63fe5760359ded5'],
        ['htdf15p9tq45x5atx9kacq36394uum6286tce6qssh0', 'c2188df3497b340d9ec28106c2e5992a6863fee0e80010664f8202fc22cf0da0'],
        ['htdf19w3u747se39xurn7vs9uc3llm8eqds65ql3p9j', '1c79909384e4c06eda903fd3c16760943bd5876a50d01499c61ed7e397b399a1'],
        ['htdf1mlczk2j3qp5gr72v6xg863k274axrkwf25333x', 'd8b33f6fc3a1613ab95f064c5fb00513ff33fe6bb955c7ee81b075ef8e75f388'],
        ['htdf1p4ayzdx3ktrvffystxq93uq2rasx0g9rzajmlv', 'bdde39cd27f23a2af806cbdec63fb2f611956916e27dd6672b400feab5dbfea5'],
        ['htdf1kz4tzzdx9xtdcru57d47mjy73kg5eh68rpefqd', 'f7986cc87c1987ae73daf04e9bb8494ce8704838e92cf96e603caf2048792e01'],
        ['htdf1jr072u2ymrh7ffh8ej55840y4ywkrrgm23k4sf', '9b5e14f9dc98e48a916194f7be065f203409385214ec81f8b0f0030657bd3402'],
        ['htdf1v2dpkae6lnrg0k3lhg752cqkrn8wpvxu6jdlfn', 'dd64d64205a0263c232a1314b87b56cb7b11899c18315879a97001c15c475a36'],
        ['htdf1ug2q5mgp7tp0cagftu5furqavk6j3aqqpv3xsy', 'bd3f7e932231e67811510adc794eea0cbccfd1b7525fc18fe00d236e2e79691e'],
        ['htdf1yt748zpkx9mhd2yucjclf927ent8n7gzdtp5sh', '0aedf09fb01ca510bb51139a761951e43f90c1c5016396ef664dde16e9ff84c6'],
        ['htdf1fna0l6fc7t3pvv664s25jrsgldwqfznktdqame', '1859bf5a7dc1aa2eaaedd570bea6ee661246b4f46f37abcd03faff582ff8a972'],
        ['htdf1cvkwpe6py350257qe4p32nrnq2zrj80sx5xytf', '0c9e1ab2f4b5221480a9a2d61747e02d8a4ef457188986d46f32869356859f03'],
        ['htdf1j2vqweddjaxx0m2vw6szk8n9e2z9vwa6pxggnk', '9b8eab16ef677b6b74b107b33a710aa9e8d1e65af75d4b916206fedeb3f7325b'],
        # ['htdf14u9q8lnj9c92j6ezfnvuqkvg2dakxlc5622ekn', 'bf39ea45e1045471e8f113f05d6d7cb48a921daafc4682368db7c96a2c36559d'],
    ],
    'RPC_HOST': 'htdf2020-node03.orientwalt.cn',
    'RPC_PORT': 1317,
    'SLEEP_SECS': 1200,    # 多少秒1笔
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
