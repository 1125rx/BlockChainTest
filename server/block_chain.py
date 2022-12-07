import hashlib
import json
import requests
from time import time
from urllib.parse import urlparse


class BlockChain:
    def __init__(self):
        # 储存交易
        self.current_transactions = []
        # 储存区块链
        self.chain = []
        # 储存节点
        self.nodes = set()
        # 创建创世块
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
        向节点列表中添加新节点
        :param address: 节点地址. 例： 'http://localhost:5000'
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        确定给定的区块链是否有效
        :param chain: A block_chain
        :return: True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # 检查块的hash是否正确
            if block['previous_hash'] != self.hash(last_block):
                return False

            # 检查PoW是否正确
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        共识算法解决冲突
        使用网络中最长的链.
        :return:  如果链被取代返回 True, 否则为False
        """
        neighbours = self.nodes
        new_chain = None

        # 寻找更长的链
        max_length = len(self.chain)

        # 获取并验证网络中所有节点的链
        for node in neighbours:
            response = requests.get('http://{}/chain'.format(node))

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash):
        """
        生成新块
        :param proof: 工作证明算法给出的工作证明
        :param previous_hash: 前一个块的Hash值
        :return: 新的区块
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        生成新交易信息，信息将加入到下一个待挖的区块中
        :param sender: 发送者的地址
        :param recipient: 接收者的地址
        :param amount: 账户
        :return: 保存此事物的块的索引
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        生成块的 SHA-256 hash值
        :param block: Block
        """
        # 必须确保字典是有序的，否则会有不一致的哈希值
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        """
        简单的工作量证明:
         查找一个 p' 使得 hash(pp') 以5结尾
         p 是上一个块的证明,  p' 是当前的证明
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        验证证明: 是否hash(last_proof, proof)以5结尾
        :param last_proof: 前一个工作量证明
        :param proof: 现在的工作量证明
        :return: True if correct, False if not.
        """
        guess = '{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        # 此处为便于测试结果，设置一个比较容易获得的数字
        return guess_hash[:1] == "5"
