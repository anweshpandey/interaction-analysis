#!/bin/bash

# Define the template content
template="""
TYPE = QUANT
FILE_TYPE = TXT
UNIT = ANS
NAME = mod1
CHARGE_SELECT = ALL
DIRECTION = MANUAL
V1X = 6.14378723 
V1Y = 31.35654381
V1Z = 21.22712489
V2X = 4.54978723 
V2Y = 31.38754381
V2Z = 21.63412489
POINT_X = 5.34678
POINT_Y = 31.37204
POINT_Z = 21.43062
#FORCE_FIELD = AMBER
#N_TERMINAL = 1
#C_TERMINAL = 189
"""

# List of names to replace "mod1"
names=(
    "rmg2w-ge0" "rmg2w-ge78" "rmg2w-ge4" 
    "a166mg2w-ge0" "a166mg2w-ge4" "a166mg2w-ge78"
    "a189mg2w-ge0" "a189mg2w-ge4" "rmg2w-gn0"
    "a189mg2w-ge78" "rmg2w-gn4" "rmg2w-gn78"
    "a166mg2w-gn0" "a166mg2w-gn4" "a166mg2w-gn78"
    "a189mg2w-gn0" "a189mg2w-gn78" "a189mg2w-gn4"
)

# Loop through names and generate files
for name in "${names[@]}"; do
    output_file="${name}.inp"
    echo "Generating $output_file"
    echo "${template//mod1/$name}" > "$output_file"
done

echo "All files generated successfully."

