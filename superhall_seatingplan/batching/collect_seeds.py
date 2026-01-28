import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

pd.set_option('display.max_columns', None)   # show all columns
pd.set_option('display.width', None)         # auto-adjust width
# ==== CONFIGURATION ====
Nmax = 10000               # change this to however many seeds you expect
nfinished=0
# ========================
verbose=0
data_rows = []
base_dirs=['data']

for base_dir in base_dirs: # where the seed_1, seed_2, ... folders live
    for n in range(1, Nmax + 1):
        seed_dir = os.path.join(base_dir, f"seed_{n}")
        results_path = os.path.join(seed_dir, "results.txt")
        if not os.path.exists(results_path):
            if verbose: print(f'{results_path} not found')
            continue

        # open the file and load up the metrics
        values=np.loadtxt(results_path)
        headers=["score1","total1","score2","total2","number_pissed_off","total_hapiness","seed"]
        
        # add to a dictionary
        row = dict(zip(headers, values))
        if base_dir == 'data': row["seed"] = n
        nfinished+=1
        data_rows.append(row)

# Convert to DataFrame for convenience
if data_rows:
    df = pd.DataFrame(data_rows)
    df = df.sort_values("seed").reset_index(drop=True)


    # print(df)
    
    filtered = df[(df["score1"] == df["total1"]) & (df["number_pissed_off"] == 0)] #the ones with no pissed off people and all guests adjacent to hosts
    # filtered = df[(df["score1"] == df["total1"])]

    with pd.option_context('display.max_rows', None, 'display.max_columns', None):

        
        n_accepted=len(filtered["score1"])
        print(f'{n_accepted} acccepted out of {nfinished}')
        if n_accepted:
            filtered = filtered.copy()  # ensures this is a new DataFrame
            filtered['ratio'] = filtered['score2'] / filtered['total2']  # compute the ratio
            # print(filtered)

            # find the maximum ratio
            max_ratio = filtered['ratio'].max()

            # select all rows that have this max ratio
            best_ratio_rows = filtered[filtered['ratio'] == max_ratio]

            # among these, pick the row with the maximum total_hapiness
            best = best_ratio_rows.loc[best_ratio_rows['total_hapiness'].idxmax()]
            print('the best:')
            print(best)
            print(best['seed'])
            seed_dir = os.path.join(base_dir, f"seed_{int(best['seed'])}")

            os.system(f"cp {seed_dir}/* .")

        if(1): #do a histogram showing the happiness for all vs the filtered data
            plt.figure()
            plt.hist(df['total_hapiness'], bins=50,label='before filtering')
            plt.hist(filtered['total_hapiness'], bins=50,label='after filtering')
            plt.axvline(best['total_hapiness'],label='The best seed',zorder=10,color='red',linestyle='--')
            plt.xlabel('Total happiness')
            plt.ylabel('Count')
            plt.title('Histogram of total happiness (all vs accepted runs)')
            plt.legend()
            plt.show()