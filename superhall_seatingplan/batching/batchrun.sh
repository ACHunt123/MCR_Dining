#!/bin/bash

# Usage: ./run_seeds.sh MAX_SEED
# Example: ./run_seeds.sh 10

if [ -z "$1" ]; then
    echo "Please provide the maximum seed as the first argument."
    exit 1
fi

MAX_SEED=$1
DATAFOLDER="data"
quiet=''
quiet='> /dev/null 2>&1'
SCRIPT="python3 /home/ach221/software/MCR_Dining/superhall_seatingplan/generate_seatingplan.py"
NPARALLEL=30   # Number of parallel processes

commands=()

for SEED in $(seq 1 $MAX_SEED); do
    FOLDER="$DATAFOLDER/seed_$SEED"
    mkdir -p "$FOLDER"
    
    # Command to run simulation in its folder
    cmd="cd $FOLDER && $SCRIPT --seed $SEED $quiet"
    commands+=("$cmd")
done

# Ask before running
printf "Do you want to run %d commands in parallel (limit %d)?\n" ${#commands[@]} $NPARALLEL
read -r -p "Press Enter to continue, or type anything to cancel: " answer
[[ -z "$answer" ]] || { echo "Aborted."; exit 1; }

# Run all commands in parallel
printf "%s\n" "${commands[@]}" | xargs -P "$NPARALLEL" -I {} bash -c '{}'

echo "All simulations completed."
