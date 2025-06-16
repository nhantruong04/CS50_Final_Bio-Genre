from cs50 import SQL
import random

# GENOME GENERATION
def seq_generate(length):
    sequence = ""
    nt = {
        0: 'A',
        1: 'C',
        2: 'T',
        3: 'G'
    }
    for i in range(length):
        sequence += nt[random.randint(0,3)]
    return sequence

db = SQL("sqlite:///bio-genre.db")
# db.execute("INSERT INTO species (sci_name, common_name, habitat, life_span, location, description) VALUES('Ailuropoda melanoleuca', 'Giant Panda - Panda bear - Panda',  'Forest','26 years', 'China (Sichuan, Shaanxi, Gansu)', 'The giant panda (Ailuropoda melanoleuca), also known as the panda bear or simply panda, is a bear species endemic to China. It is characterised by its white coat with black patches around the eyes, ears, legs and shoulders. Its body is rotund; adult individuals weigh 100 to 115 kg (220 to 254 lb) and are typically 1.2 to 1.9 m (3 ft 11 in to 6 ft 3 in) long. It is sexually dimorphic, with males being typically 10 to 20% larger than females. A thumb is visible on its forepaw, which helps in holding bamboo in place for feeding. It has large molar teeth and expanded temporal fossa to meet its dietary requirements. It can digest starch and is mostly herbivorous with a diet consisting almost entirely of bamboo and bamboo shoots.') ")
# db.execute(''' INSERT INTO species (sci_name, common_name, habitat, life_span, location, description) VALUES('Udara blackburni', 'Koa Butterfly', 'Forest','2 months','United States (Hawaiian Is.)', "Udara blackburni, the Koa butterfly, is a butterfly in the family Lycaenidae that is endemic to Hawaii. It is also known as Blackburn's butterfly, Blackburn's bluet, Hawaiian blue or green Hawaiian blue. The wingspan is 22–29 mm.Udara blackburni is one of only two butterfly species that are native to Hawai'i, the other being Vanessa tameamea. These butterflies have wings that are blue on the upper side and green on the under side.") ''')

# collect species_id from databse
# species_id = db.execute("SELECT id FROM species")
# for id in species_id:
#     for chromosome in range(1,random.randint(6, 11)):
#         length = random.randrange(1500, 2500, 101)
#         db.execute("INSERT INTO db_sequence (species_id, name, seq_nu, seq_length) VALUES (?,?,?,?)", id["id"], f'chromosome {chromosome}', seq_generate(length), length)

