from hashlib import sha256
import binascii
import itertools


def get_bip39_words_list():
    lines = None
    # downloaded from https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt
    with open('./english.txt') as file:
        lines = [line.rstrip() for line in file]
    assert(len(lines) == 2048)
    return lines


def checksum_chars_to_add(seed_len):
    chars_for_checksum = None
    if seed_len == 12:
        chars_for_checksum = 1
    elif seed_len == 24:
        chars_for_checksum = 2
    return chars_for_checksum


def bits_to_add(seed_len):
    chars_for_checksum = None
    if seed_len == 12:
        chars_for_checksum = 7
    elif seed_len == 24:
        chars_for_checksum = 3
    return chars_for_checksum


def handle_one_pad(bip39_words_list, num_added_pads):
    while True:
        try:
            msg = '\nYou added already {} pads. Insert all the words of another pad or 0 to stop: '
            f_msg = msg.format(num_added_pads)
            seed_string = input(f_msg).lower()
        except KeyboardInterrupt:
            quit()

        if seed_string == '0':
            return False
        
        # convert string to list
        seed_list = seed_string.split(' ')
        # remove eventual whitespaces in list
        seed_list = [word for word in seed_list if word]

        # check if all words are in bip39 list
        all_words_in_bip39_list = True
        for word in seed_list:
            if word not in bip39_words_list:
                all_words_in_bip39_list = False
                print('\n!! ERROR: word {} not in bip39 words list'.format(word))
        
        # prevent going ahead if not all words in bip39 list
        if not all_words_in_bip39_list:
            continue

        # check that words inserted must be 12 or 24
        if len(seed_list) != 12 and len(seed_list) != 24:
            print('\n!! ERROR: {} words inserted'.format(len(seed_list)))
            continue

        break


    whole_mnemonic = seed_list.copy()
    last_word = seed_list.pop()
    bits_string = ''
    for word in seed_list:
        decimal_index = bip39_words_list.index(word)
        binary_index = bin(decimal_index)[2:].zfill(11)
        bits_string += binary_index


    combos = itertools.product(['0', '1'], repeat=bits_to_add(len(whole_mnemonic)))
    combos = [ ''.join(list(i)) for i in combos]
    combos = sorted(combos, key=lambda x: int(x, 2))
    
    last_word_bits = None
    for combo in combos:
        entropy = '{}{}'.format(bits_string, combo)
        hexstr = "{0:0>4X}".format(int(entropy,2)).zfill(int(len(entropy)/4))
        data = binascii.a2b_hex(hexstr)
        hs = sha256(data).hexdigest()
        last_bits = ''.join([ str(bin(int(hs[i], 16))[2:].zfill(4)) for i in range(0, checksum_chars_to_add(len(whole_mnemonic))) ])
        last_word_bin = '{}{}'.format(combo, last_bits)
        word = bip39_words_list[int(last_word_bin, 2)]
        if (word == last_word):
            last_word_bits = combo

    
    return {
        'mnemonic': whole_mnemonic,
        'bits_string': bits_string+last_word_bits
    }



def main():
    print('\n\nSEED XOR CALCULATOR\n\n')
    bip39_words_list = get_bip39_words_list()
    added_pads = []

    while True:
        pad = handle_one_pad(bip39_words_list, len(added_pads))

        # he stopped adding pads
        if pad is False:
            # at least 2 pads are required
            if len(added_pads) < 2:
                print('\n!! ERROR: At least 2 pads are required. You added {} pads'.format(len(added_pads)))
                continue
            print('\nPads completed! I will calculate the XOR seed...')
            break
        else:
            # following pads should have the same amount of words of the first one
            if len(added_pads) > 0 and len(pad['mnemonic']) != len(added_pads[0]['mnemonic']):
                msg = '\n!! ERROR: first pad added has {} words. All the following ones should have the same amount of words'
                f_msg = msg.format(len(added_pads[0]['mnemonic']))
                print(f_msg)
                continue
            added_pads.append(pad)
    

    print('\nCalculating... You inserted these pads:')
    for idx, pad in enumerate(added_pads):
        print('\n{}) {}'.format(idx+1, ' '.join(pad['mnemonic'])))

    xor = None
    for i in range(0, len(added_pads)-1):
        if i == 0:
            xor = added_pads[0]['bits_string']
        str1 = xor
        str2 = added_pads[i+1]['bits_string']
        xor = ''.join([str(ord(a) ^ ord(b)) for a,b in zip(str1, str2)])

    entropy = xor
    hexstr = "{0:0>4X}".format(int(entropy,2)).zfill(int(len(entropy)/4)) 
    data = binascii.a2b_hex(hexstr)
    hs = sha256(data).hexdigest()

    chars_for_checksum = checksum_chars_to_add(len(added_pads[0]['mnemonic']))

    last_bits = ''.join([ str(bin(int(hs[i], 16))[2:].zfill(4)) for i in range(0, chars_for_checksum) ])
    entropy += last_bits

    bits_per_word = 11
    splitted = [entropy[i:i+bits_per_word] for i in range(0, len(entropy), bits_per_word)]
    words = [ bip39_words_list[int(i, 2)] for i in splitted ]
    
    print('\nXOR SEED CALCULATED:\n\n{}\n'.format(' '.join(words)))
        

if __name__ == "__main__":
    main()
