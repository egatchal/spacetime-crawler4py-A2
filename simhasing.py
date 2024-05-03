from hashlib import md5
from zlib import crc32
def sim_hash(frequencies):
    """Compute a similarity hash for the passed in dict.
    
    Parameters
    ----------
    frequencies : dict
        a dict containing URL tokens (key) and the corresponding count (value)
    
    Returns
    -------
    tuple
        a tuple containing a binary vector representation of the dict passed in
    """
    # NOTE: Implementation for md5 below
    hashes = dict()
    for key in frequencies.keys():
        hash_v = md5(key.encode()).digest()[:8] # byte representation
        hashes[key] = hash_v # store hash values into hashes

    binary_vector = []
    for bit_index in range(64):
        value = 0
        byte_index = bit_index // 8 # create a byte_index using bit_index in the range
        for key, hash_v in hashes.items():
            # preform bit-shift operation (which is shifting bit_index % 8 spots) 
            # on the hash's byte value to target a specific bit
            # then use that bit with the AND operation
            if (hash_v[byte_index] >> (bit_index%8)) & 1:
                value += frequencies[key] # if bit is 1 then we add the frequency to the value
            else:
                value -= frequencies[key] # if bit is 0 we subtract the frequency to the value
        if value >= 0:
            binary_vector.append(1) # append 1 if value is non-negative
        else:
            binary_vector.append(0) # append 0 if value is negative
    
    # NOTE: Implementation for crc32 below
    # for bit_index in range(32):
    #     value = 0
    #     byte_index = bit_index
    #     for key, hash in hashes.items():
    #         if (hash >> bit_index) & 1:
    #             value += frequencies[key]
    #         else:
    #             value -= frequencies[key]
    #     if value >= 0:
    #         binary_vector.append(1)
    #     else:
    #         binary_vector.append(0)
    return tuple(binary_vector)

def compute_sim_hash_similarity(vector1, vector2):
    """Compute the sim hash similarity between two tuples.
    
    Parameters
    ----------
    vector1 : tuple
        a tuple containing binary vector representation of it's similarity score
    vector2 : tuple
        a tuple containing binary vector representation of it's similarity score
        
    Returns
    -------
    int
        an int indicating the number of bits similar between the two tuple hash vectors (vector1 & vector2)
    """
    count = 0
    for i in range(64):
        if vector1[i] == vector2[i]:
            count += 1
    return count

if __name__ == "__main__":
    d1 = {"high":1, "low":1, "begging":1}
    d2 = {"high":6, "low":20, "begging":1}
    hash1 = sim_hash(d1)
    hash2 = sim_hash(d2)
    
    print(hash1,hash2)
    print(compute_sim_hash_similarity(hash1, hash2))