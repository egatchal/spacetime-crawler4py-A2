from hashlib import md5
def sim_hash(frequencies):
    hashes = dict()
    for key in frequencies.keys():
        hash = md5(key.encode()).digest() # byte representation
        hashes[key] = hash
    
    binary_vector = []
    for bit_index in range(128):
        value = 0
        byte_index = bit_index // 8
        for key, hash in hashes.items():
            if (hash[byte_index] >> (bit_index%8)) & 1:
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
    for i in range(128):
        if vector1[i] == vector2[i]:
            count += 1
    return count / 128

if __name__ == "__main__":
    d = {"high":1, "low":2, "begging":3}
    sim_hash(d)
