from hashlib import md5
from zlib import crc32
def sim_hash(frequencies):
    hashes = dict()
    for key in frequencies.keys():
        # hash = md5(key.encode()).digest() # byte representation
        hash = crc32(key.encode())
        hashes[key] = hash

    binary_vector = []
    # for bit_index in range(32):
    #     value = 0
    #     byte_index = bit_index // 8
    #     for key, hash in hashes.items():
    #         if (hash[byte_index] >> (bit_index%8)) & 1:
    #             value += frequencies[key]
    #         else:
    #             value -= frequencies[key]
    #     if value >= 0:
    #         binary_vector.append(1)
    #     else:
    #         binary_vector.append(0)
    
    for bit_index in range(32):
        value = 0
        byte_index = bit_index
        for key, hash in hashes.items():
            if (hash >> bit_index) & 1:
                value += frequencies[key]
            else:
                value -= frequencies[key]
        if value >= 0:
            binary_vector.append(1)
        else:
            binary_vector.append(0)
    return tuple(binary_vector)

def compute_sim_hash_similarity(vector1, vector2):
    count = 0
    for i in range(32):
        if vector1[i] == vector2[i]:
            count += 1
    return count / 32

if __name__ == "__main__":
    d1 = {"high":2, "low":2, "begging":1}
    d2 = {"high":2, "low":1, "begging":3}
    hash1 = sim_hash(d1)
    hash2 = sim_hash(d2)
    
    print(hash1,hash2)
    print(compute_sim_hash_similarity(hash1, hash2))
