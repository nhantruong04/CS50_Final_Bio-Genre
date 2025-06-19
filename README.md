# BIO-GENRE
#### Video Demo:  <URL HERE>
#### Description:
    This website is combine a bioinformatic toolkit with different useful features to get the analysis of sequence, DNA sequence query, species query and developer tool.

### Sequence calculator
    This tool help user get general information about their DNA or RNA sequence. Caluclate length and the percentage of G and C nucleotide. Transcript DNA sequence into RNA sequence. Translate DNA/RNA sequence into amino acid sequence. If the user use DNA sequence, the web will first transript it into RNA then translate into amino acid sequence.

    Motif search and ORF search is tool to find specific region in the sequence. Motif is a sub-sequence inside your sequence that have repeat time = k. Our website will help you the find its frequency. ORF is open reading frame in sequence. It is defined as a region started which a start codon and end with a stop codon. There total three ORF in a sequence, one start at first index, one at second index and one at third index. Because DNA strand is complement thus both of two strand can be the coding strand and is possible to have ORF inside it.
**TO USE:**
Enter a DNA or RNA sequence into the sequence input, choose your calculation option then submit the sequence. The ruslt will be display below.

### BLAST (Basic local alignment search tool)
    We construct a heuristic BLASTN (only support DNA sequence) algorithm for high similarity region searching in the query and the database sequence to find out biological relation.This algorithm generate smaller words (seed, size = 5) generated from the query sequence and the database sequence and indexing them.

    Then we find each seed with in the database sequence. Once a seed is found, it will be extended from both direction to find the most optimal region to align. After that, we perform local alignment using Smith-Waterman algorithm for this region and collect the high scoring region.
    High scoring region is considered to be greater than or equal to the 70 % of max score (0.7*query_length*match).

    Repetitive and low-complexity sequences (such as AAAAAA or TTTTCTTT) cause problems for search and clustering algorithms based on matching words. Low-complexity sequences cause certain words to have high frequencies, which can cause performance problems if they are not masked. Therefore, these seeds which the frequency that are greater than or equal to 20 will be ignored.

**TO USE:**
 Enter your DNA sequence (length from 5 to 1,000 bp). Then select scoring parameter for match/mismatch and gap in the alignment. The result will be display into two option
* A summaries table of sequence that match your query. This give an overview of sequence name, related species, max score and total score in this sequence.
* Alignment details of each matched sequence. This will help you to get the position infor, score, identity and gap of each alignment.

#### The algorithm work as follow:
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
So seeds with high frequency ( >= 30) will be ignore.
6. If found, start to extend from both direction and calculate score of both side. Until max_score - current_score >= x-drop
7. Then allow gapped BLAST:
    - From the extended sequence, continue to expand it with a window_pad, left + 10 bases and right + 10 base (for simple).Because, we may have more similarity when expand the window and allow gapped BLAST.
    The padding may depend on the expected gap or other algorithm parameters.
    - Note that the size expanded window is also depend on the start and end point of both query and db_sequence.
8. After expand both sequences, align them into matrix. Using Smith-waterman algorithm to calculate the score and traceback the alignment
Before pass the window into Smith-Watermant function we need to check wheter this window is already aligned
9. Collect positions that are high score and significant ( >= hssp)
10. Two different seeds might lead to overlapping or very similar windows, but with slightly different start or end values. We need to filter the results to remove multiple similar result in the output.

### Species data/query
    This feature is used to access to information about species through different searching parameters.  The information includes scientific name, common name, lifespan, habitat,... and the general introduction about the species. Result will be presented in as summaries page with different species tag. To see full details about species, click "read more" button

### Species data/add species
    This feature is for admin only and it is used to add new species information into the database The sever will check user role before move them to this feature. Only activated when admin login and use the correct security key (123456). We recognize an admin by their role that are already generated in the users database. Once admin has typed the correct key, a random will be assign to session["access_granted"] for security purpose. Whenever an admin try to access /species-manage or add new species, the sever will check for the correct session["access_granted"] key.

* Admin account: Eren, password: eren50%

### Developers
    This is an API document for developers to access our species information. The request using GET method and year is set to 2025 as default. The respond will return into a json file with result code and respond status. Other parameters are scientific name, common name, location, and species ID. To see more detail, read our document at "/api-docs".
