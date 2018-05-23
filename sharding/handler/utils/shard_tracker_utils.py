from eth_utils import (
    event_abi_to_log_topic,
    to_dict,
    to_checksum_address,
    decode_hex,
    big_endian_to_int,
)

from sharding.contracts.utils.smc_utils import (
    get_smc_json,
)


class LogParser(object):
    def __init__(self, *, event_name, log):
        event_abi = self._extract_event_abi(event_name=event_name)

        topics = []
        datas = []
        for inp in event_abi["inputs"]:
            if inp['indexed'] is True:
                topics.append((inp['name'], inp['type']))
            else:
                datas.append((inp['name'], inp['type']))

        self._set_topic_value(topics=topics, log=log)
        self._set_data_value(datas=datas, log=log)

    def _extract_event_abi(self, *, event_name):
        for func in get_smc_json()['abi']:
            if func['name'] == event_name and func['type'] == 'event':
                return func
        raise Exception("Can not find event {}".format(event_name))

    def _set_topic_value(self, *, topics, log):
        if len(topics) != len(log['topics'][1:]):
            raise Exception(
                "Error parsing log topics, expect"
                "{} topics but get {}.".format(len(topics), len(log['topics'][1:]))
            )
        for (i, topic) in enumerate(topics):
            val = self._parse_value(val_type=topic[1], val=log['topics'][i + 1])
            setattr(self, topic[0], val)

    def _set_data_value(self, *, datas, log):
        data_bytes = decode_hex(log['data'])
        if len(datas) * 32 != len(data_bytes):
            raise Exception(
                "Error parsing log data, expect"
                "{} data but get {}.".format(len(datas), len(data_bytes))
            )
        for (i, data) in enumerate(datas):
            val = self._parse_value(val_type=data[1], val=data_bytes[i * 32: (i + 1) * 32])
            setattr(self, data[0], val)

    def _parse_value(self, *, val_type, val):
        if val_type == 'bool':
            return bool(big_endian_to_int(val))
        elif val_type == 'address':
            return to_checksum_address(val[-20:])
        elif val_type == 'bytes32':
            return val
        elif 'int' in val_type:
            return big_endian_to_int(val)
        else:
            raise Exception(
                "Error parsing the type of given value. Expect bool/address/bytes32/int*"
                "but get {}.".format(val_type)
            )


@to_dict
def parse_register_notary_log(log):
    notary = log['topics'][1][-20:]
    data_bytes = decode_hex(log['data'])
    index_in_notary_pool = big_endian_to_int(data_bytes[:32])
    yield 'index_in_notary_pool', index_in_notary_pool
    yield 'notary', to_checksum_address(notary)


@to_dict
def parse_deregister_notary_log(log):
    notary = log['topics'][1][-20:]
    data_bytes = decode_hex(log['data'])
    index_in_notary_pool = big_endian_to_int(data_bytes[:32])
    deregistered_period = big_endian_to_int(data_bytes[32:])
    yield 'index_in_notary_pool', index_in_notary_pool
    yield 'notary', to_checksum_address(notary)
    yield 'deregistered_period', deregistered_period


@to_dict
def parse_release_notary_log(log):
    notary = log['topics'][1][-20:]
    data_bytes = decode_hex(log['data'])
    index_in_notary_pool = big_endian_to_int(data_bytes[:32])
    yield 'index_in_notary_pool', index_in_notary_pool
    yield 'notary', to_checksum_address(notary)


@to_dict
def parse_add_header_log(log):
    shard_id = big_endian_to_int(log['topics'][1])
    data_bytes = decode_hex(log['data'])
    period = big_endian_to_int(data_bytes[:32])
    chunk_root = data_bytes[32:]
    yield 'period', period
    yield 'shard_id', shard_id
    yield 'chunk_root', chunk_root


@to_dict
def parse_submit_vote_log(log):
    shard_id = big_endian_to_int(log['topics'][1])
    data_bytes = decode_hex(log['data'])
    period = big_endian_to_int(data_bytes[:32])
    chunk_root = data_bytes[32:64]
    notary = data_bytes[-20:]
    yield 'period', period
    yield 'shard_id', shard_id
    yield 'chunk_root', chunk_root
    yield 'notary', to_checksum_address(notary)


def get_event_signature_from_abi(event_name):
    for function in get_smc_json()['abi']:
        if function['name'] == event_name and function['type'] == 'event':
            return event_abi_to_log_topic(function)
