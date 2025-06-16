                        #________________BASIC LOCAL ALIGNMENT SEARCH TOOL_________________#

'''
1. Break the query sequence into small substring (seeds), length = 3 (seed_size)
2. Hash the position of each seed into a dict e.g 'AGCTA' -> {'AGC': 0, 'GCT': 1, 'CTA': 2}.
3. Do the above step for the database sequence (db_seq)
4. Define a scoring matrix:
    - (match, mismatch, gap) -> depend on user and this implementation not support affine gap
    - high-score segment pair (hssp) = 0.7*len(query)*match (BLAST will search for regioin that have score >= hssp)
    - window_pad = 10
    - x_drop = 5. The stop signal when extend a seed
5. Look up each seed of query in the db_seq.
   Repetitive and low-complexity sequences (such as AAAAAA or TTTTCTTT) cause problems for search and clustering algorithms based on matching words
   So seeds with high frequency ( >= 20) will be ignore.
6. If found, start to extend from both direction and calculate score of both side. Until max_score - current_score >= x-drop
7. Then allow gapped BLAST:
    - From the extended sequence, continue to expand it with a window_pad, left + 10 bases and right + 10 base (for simple).Because, we may have more similarity when expand the window and allow gapped BLAST.
      The padding may depend on the expected gap or other algorithm parameters.
    - Note that the size expanded window is also depend on the start and end point of both query and db_sequence.
8. After expand both sequences, align them into matrix. Using Smith-waterman algorithm to calculate the score and traceback the alignment
   Before pass the window into Smith-Watermant function we need to check wheter this window is already aligned
9. Collect positions that are high score and significant ( >= hssp)
10. Two different seeds might lead to overlapping or very similar windows, but with slightly different start or end values.
    We need to filter the results to remove multiple similar result in the output.

'''

# required library
from collections import defaultdict
import numpy as np


# threshold for to manage gapped or ungapped
window_pad = 10
x_drop = 5

# generate k-mers of sequence, indexing the location of each k-mer in  query/db_sequence
def k_mers_dict(sequence, k):
    # hash the k-substrings (k_mers) in the sequence and its index
    hash_table = defaultdict(list)
    for i in range(len(sequence) - k + 1):
        k_mer = sequence[i:i + k]
        hash_table[k_mer].append(i)
    return hash_table



# define a function for safety window expending
def window_expand(seq, left, right, pad =10):
    start = max(0, left - pad)
    end = min(len(seq), right + pad + 1)
    return (start,end) # not subtract for 1

# function to check to nucleotide is match or mismatch
def match_check(a, b, match, mismatch):
    return match if a == b else mismatch

# function for left and right extension without gap
def extend_left(query, db_seq, left_query, left_subject, match, mismatch):
    max_score_left = 0
    score_left = 0
    start_q = 0
    start_s  = 0
    while left_query >= 0 and left_subject >= 0:
        score_left += match_check(query[left_query], db_seq[left_subject], match, mismatch)
        if max_score_left - score_left < x_drop:
            max_score_left = max(score_left, max_score_left)
            start_q = left_query
            start_s = left_subject
        elif max_score_left - score_left >= x_drop:
            break
        left_query -= 1
        left_subject -= 1

    return {"max_score": max_score_left, "start_q": start_q, "start_s": start_s}

def extend_right(query, db_seq, right_query, right_subject,  match, mismatch):
    max_score_right = 0
    score_right = 0
    end_q = len(query) - 1
    end_s  = len(db_seq) - 1
    while right_query < len(query) and right_subject < len(db_seq):
        score_right += match_check(query[right_query], db_seq[right_subject], match, mismatch)
        if max_score_right - score_right < x_drop:
            max_score_right = max(score_right, max_score_right)
            end_q = right_query
            end_s = right_subject
        elif max_score_right - score_right >= x_drop:
            break
        right_query += 1
        right_subject += 1

    return {"max_score": max_score_right, "end_q": end_q, "end_s": end_s}


# smith_waterman algorithm for gapped BLAST
def smith_waterman(query, db_seq, match, mismatch, gap, hssp, star_q, start_s):
    # create matrix and calculate the score
    matrix = np.zeros((len(query) + 1, len(db_seq) + 1), int)
    max_score = 0
    for row in range(1,len(matrix)):
        for col in range(1,len(matrix[0])):
            matrix[row][col] = max(
                0,
                matrix[row - 1][col] + gap,
                matrix[row][col - 1] + gap,
                matrix[row - 1][col - 1] + match_check(query[row - 1], db_seq[col - 1], match, mismatch)
            )

            max_score = max(matrix[row][col], max_score)
    # find max_score region index in matrix

    candidate_index = []
    for row in range(len(matrix)):
        for col in range(len(matrix[0])):
            if matrix[row][col] == max_score and matrix[row][col] >= hssp: # just select the aligment with significant score
                candidate_index.append((row, col))

    result = []
    # for each max_score position trace back until hit zero
    for row, col in candidate_index:
        score = int(matrix[row][col])
        align_query = ""
        align_db_seq = ""
        exact_match = 0
        gap_count = 0
        while(matrix[row][col] > 0):

            if matrix[row][col] == matrix[row - 1][col - 1] + match_check(query[row - 1], db_seq[col -1], match, mismatch):
                align_query = query[row - 1] + align_query
                align_db_seq = db_seq[col - 1] + align_db_seq
                exact_match += 1
                row -= 1
                col -= 1

            elif matrix[row][col] == matrix[row - 1][col] + gap: # move up, gap in db_seq
                align_query = query[row - 1] + align_query
                align_db_seq = '-' + align_db_seq
                gap_count += 1
                row -= 1

            elif matrix[row][col] == matrix[row][col - 1] + gap: # move left, gap in query
                align_query = '-' + align_query
                align_db_seq = db_seq[col - 1] + align_db_seq
                gap_count += 1
                col -= 1

        identity = f'{exact_match}/{len(align_query)} ({(exact_match * 100/len(align_query)):.2f} %)'
        gap_ratio = f'{gap_count}/{len(align_query)} ({(gap_count * 100/len(align_query)):.2f} %)'
        query_start= star_q + row + 1
        query_end =  query_start + len(align_query.replace('-',"")) - 1
        subject_start = start_s + col + 1
        subject_end = subject_start + len(align_db_seq.replace('-',"")) - 1

        align_print = ""
        for i in range(len(align_query)):
            if align_query[i] == align_db_seq[i]:
                align_print += '|'
            else:
                align_print += ' '

        # pre-processing the space in start location, to format ouput printing
        space_start = len(str(subject_start)) - len(str(query_start))
        if space_start > 0:
            print_start_location = (f"{space_start*' '}{str(query_start)}",str(subject_start)) # insert space into query
        elif space_start < 0:
            print_start_location = (str(query_start), f"{space_start*' '}{str(subject_start)}")
        else:
            print_start_location = (str(query_start), str(subject_start))
        space_align = len(str(max(query_start, subject_start)))
        result.append({'align':
                       {"query": align_query,
                        "subject": align_db_seq,
                        "query_align_location": (query_start, query_end), "subject_align_location": (subject_start,subject_end),
                        "score": score,
                        "identity": identity,
                        "gap": gap_ratio,
                        'align_print': f"{space_align*' '} {align_print}",
                        'print_start_location': print_start_location
                        }
                    })
    return result


# Interate through the sequence, find match and start to extend
def blastn (query, db_seq, match, mismatch, gap, seed_size = 3):
    hssp = 0.7*len(query)
    # Indexing the seed in query and db_sub_seq
    db_sub_seq = k_mers_dict(db_seq, seed_size)
    query_seed = {}

    if len(query) >= 5:
        query_seed = k_mers_dict(query, seed_size)

    else:
        return "Not support sequences with length < 3"

    seen = set() # to avoid multiple repeat of blastn for a same region, keep track the already blastn-ed position into a tupple
    best_align = []

    # interate through the db_seq to find high similarity regions (alignments)
    for seed, seed_index in query_seed.items():
        if seed in db_sub_seq.keys():
            # low-complexity masking. Skipping high-frequency seeds filters out low-quality, repetitive alignments
            if len(db_sub_seq[seed]) >= 20 or len(query_seed[seed]) >= 20:
                continue
            # seed found, start to align each seed index in each matched position i db_seq (subject)
            # interate throug each posion of k-mer for each position in db_seq
            for q in seed_index:
                for s in db_sub_seq[seed]:
                    query_left = q - 1
                    query_right =  q + seed_size
                    subject_left = s - 1
                    subject_right = s + seed_size

                    left_part = extend_left(query, db_seq, query_left, subject_left, match, mismatch)
                    right_part = extend_right(query, db_seq, query_right, subject_right, match, mismatch)

                    query_expand_index = window_expand(query,left_part["start_q"],right_part["end_q"])
                    subject_expand_index = window_expand(db_seq,left_part["start_s"], right_part["end_s"])

                    # Avoid the already gapped blast region
                    key = (query_expand_index, subject_expand_index)
                    if key in seen:
                        continue
                    seen.add((query_expand_index, subject_expand_index))

                    align_result = smith_waterman(query[query_expand_index[0]:query_expand_index[1]], db_seq[subject_expand_index[0]:subject_expand_index[1]], match, mismatch, gap, hssp, query_expand_index[0],subject_expand_index[0])

                    for s in align_result:
                        best_align.append(s)

    if not best_align:
        return ["No significant similarity found!"]
    total_score = 0
    unique_align = []
    align_seen = set()
    for result in best_align:
        for val in result.values():
            sig = (val["query"],val["subject"], val["query_align_location"], val["subject_align_location"])
            if sig not in align_seen:
                align_seen.add(sig)
                total_score += result['align']['score']
                unique_align.append(result)
    # sort the result by score:
    sorted_align = sorted(unique_align, key=lambda x:x["align"]["score"],reverse=True)
    max_score = sorted_align[0]['align']['score']

    return {'max_score': max_score, 'total_score': total_score, 'result': sorted_align}



# output = blastn("AGTCCACGTCAG", "CGGGCTCCGAGTTCAGTCAGCAGCCCAACGCAGGATGCTCGTGCTAGACGTCTAGCTCGTGAGCTCCAACGTCAGCTATCCAGTCAGTCAGCTAGTGAGCTCCAACGTCAGGTACCATGCTAGCTAGCTACGTAGTCATCTAGCTAGCGATCGTAGCTA", 1, -1, -1)
# print(output)
