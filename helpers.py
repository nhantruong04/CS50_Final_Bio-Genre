from functools import wraps

codon_usage = {
    "UUU": "F", "UUC": "F", "UUA": "L", "UUG": "L",
    "UCU": "S", "UCC": "S", "UCA": "S", "UCG": "S",
    "UAU": "Y", "UAC": "Y", "UAA": "Stop", "UAG": "Stop",
    "UGU": "C", "UGC": "C", "UGA": "Stop", "UGG": "W",
    "CUU": "L", "CUC": "L", "CUA": "L", "CUG": "L",
    "CCU": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "CAU": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "CGU": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "AUU": "I", "AUC": "I", "AUA": "I", "AUG": "M",
    "ACU": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "AAU": "N", "AAC": "N", "AAA": "K", "AAG": "K",
    "AGU": "S", "AGC": "S", "AGA": "R", "AGG": "R",
    "GUU": "V", "GUC": "V", "GUA": "V", "GUG": "V",
    "GCU": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "GAU": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "GGU": "G", "GGC": "G", "GGA": "G", "GGG": "G"
}

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def translate(sequence):
    # transcript DNA to mRNA:
    s = sequence.replace('T', 'U')
    aa = ""
    for i in range(0, len(s) // 3):
        if codon_usage[s[3*i:3*i + 3]] == 'Stop':
            aa += "_"
        else:
            aa += codon_usage[s[3*i:3*i + 3]]
    return aa

def find_motif(sequence, motif):
    repeat_time = 0
    position = []
    for i in range(len(sequence) - len(motif) + 1):
        if sequence[i: i + len(motif)] == motif:
            position.append(str(i + 1))
            repeat_time += 1

    return ' '.join(position), str(repeat_time), motif

def reverse_complement(sequence):
    output = ''
    dct = {'A': 'T',
           'G': 'C',
           'C': 'G',
           'T': 'A'}
    for i in reversed(sequence):
        output += dct[i]
    return output

def transcript(sequence):
    output = ''
    dct = {'A': 'U',
           'G': 'C',
           'C': 'G',
           'T': 'A'}
    for i in sequence:
        output += dct[i]
    return output

def gc_content(sequence):
    gc_count = 0
    for nt in sequence:
        if nt in ['G', 'C']:
            gc_count += 1
    gc_percent = round(gc_count * 100 / len(sequence), 6)
    return gc_percent

def isRNA(sequence):
    if 'U' in sequence:
        return True
    else:
        return False
def orf_search(sequence):
    # convert DNA to mRNA:
    if isRNA(sequence):
        sequence = sequence.replace('U', 'T')

    fw_frame = sequence.replace("T", "U") # 5' - 3' forward for codon usage table
    rv_frame = reverse_complement(sequence).replace("T", "U")

    orf = []
    output = [{'Frame 1': [], 'Frame 2': [], 'Frame 3': []}, {'Frame 1': [], 'Frame 2': [], 'Frame 3': []}] # fw_frame and rv_frame
    for index, seq in enumerate([fw_frame, rv_frame]):
        for i in range(3):
            s = seq[i:]
            seq_aa = ""
            for n in range(len(s) // 3):
                try:
                    x = codon_usage[s[3*n:3*n + 3]]
                    if x == 'Stop':
                        x = '@'
                    seq_aa += x
                except(IndexError):
                    break

            # sliding window to find valid ORF sequence

            for m, a in enumerate(seq_aa):
                if a == 'M':
                    for r in range(m, len(seq_aa)):
                        if seq_aa[r] == '@':
                            orf.append(seq_aa[m:r])
                            output[index][f'Frame {i + 1}'].append(seq_aa[m:r])
                            break

    return '\n'.join(set(orf)), output
