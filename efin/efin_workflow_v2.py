#!/usr/bin/env python3

import os
import sys
import subprocess
import glob
import math
import re

def run_command(cmd, shell=True):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, check=True)
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error: {e.stderr}")
        return None, e.stderr

def step1_prep():
    """Execute prep.sh functionality"""
    print("\n" + "="*60)
    print("STEP 1: Preparing protein structure")
    print("="*60)
    
    # Find p*.pdb files
    pdb_files = glob.glob("p*.pdb")
    if not pdb_files:
        print("Error: No p*.pdb files found in current directory!")
        return False
    
    print(f"Found {len(pdb_files)} PDB file(s): {', '.join(pdb_files[:5])}...")
    
    # Copy first p*.pdb to prot.pdb (or you can modify logic here)
    first_pdb = sorted(pdb_files)[0]
    print(f"Using {first_pdb} as template -> prot.pdb")
    run_command(f"cp {first_pdb} prot.pdb")
    
    # Remove HETATM and MOL lines
    print("Removing HETATM and MOL lines...")
    run_command("sed -i '/HETATM/d' prot.pdb")
    run_command("sed -i '/MOL/d' prot.pdb")
    
    # Check if leap.in exists
    if not os.path.exists("leap.in"):
        print("Warning: leap.in not found. Skipping tleap step.")
        print("If you need tleap, please ensure leap.in exists.")
    else:
        print("Running tleap...")
        run_command("tleap -f leap.in")
    
    # Run pdb4amber if prot_l.pdb exists
    if os.path.exists("prot_l.pdb"):
        print("Running pdb4amber...")
        run_command("pdb4amber -i prot_l.pdb -o prot_la.pdb")
    else:
        print("Warning: prot_l.pdb not found. Using prot.pdb as prot_la.pdb")
        run_command("cp prot.pdb prot_la.pdb")
    
    # Modify terminal residues
    print("Modifying terminal residues...")
    modify_terminal_residues_inplace("prot_la.pdb")
    
    # Create copies
    print("Creating prot_la_oc.pdb and prot_la_ox.pdb...")
    run_command("cp prot_la.pdb prot_la_oc.pdb")
    run_command("cp prot_la.pdb prot_la_ox.pdb")
    
    print("✓ Step 1 completed successfully!")
    return True

def modify_terminal_residues_inplace(pdb_file):
    """ncTER.py functionality"""
    if not os.path.exists(pdb_file):
        print(f"Warning: {pdb_file} not found, skipping terminal modification")
        return
    
    with open(pdb_file, 'r') as f:
        lines = [line.rstrip('\n') for line in f if line.startswith(('ATOM', 'HETATM'))]

    if not lines:
        print("No ATOM or HETATM records found.")
        return

    n_term_line = lines[0]
    c_term_line = lines[-1]

    n_chain = n_term_line[21]
    c_chain = c_term_line[21]

    n_res_seq = n_term_line[22:26]
    n_res_name = n_term_line[17:20].strip()
    n_new_res_name = f"N{n_res_name}"

    c_res_seq = c_term_line[22:26]
    c_res_name = c_term_line[17:20].strip()
    c_new_res_name = f"C{c_res_name}"

    modified_lines = []
    with open(pdb_file, 'r') as f:
        for line in f:
            if line.startswith(('ATOM', 'HETATM')):
                res_name = line[17:20]
                chain_id = line[21]
                res_seq = line[22:26]

                if chain_id == n_chain and res_seq == n_res_seq:
                    line = line[:17] + n_new_res_name.rjust(3) + line[20:]
                elif chain_id == c_chain and res_seq == c_res_seq:
                    line = line[:17] + c_new_res_name.rjust(3) + line[20:]

            modified_lines.append(line.rstrip('\n'))

    with open(pdb_file, 'w') as f:
        for line in modified_lines:
            f.write(line + '\n')

def step2_grep():
    """Execute grep.sh functionality"""
    print("\n" + "="*60)
    print("STEP 2: Searching for specific atoms in PDB files")
    print("="*60)
    
    # List of files to search
    # Edit the file_list below to match your directory's PDB files
    # Previous file lists are kept commented for reference
    
    # File list (current):
    file_list = [
        "p1.pdb", "p1a.pdb", "p1b.pdb", "p1c.pdb", "p1d.pdb", "p1e.pdb", 
        "p1f.pdb", "p1g.pdb", "p1h.pdb", "p2.pdb", "p3.pdb", "p3a.pdb", 
        "p3b.pdb", "p3c.pdb", "p3d.pdb", "p3e.pdb", "p3f.pdb", "p3g.pdb",
        "p3h.pdb", "p3i.pdb", "p3j.pdb", "p3k.pdb", "p3l.pdb", "p3m.pdb",
        "p3n.pdb", "p3o.pdb", "p3p.pdb", "p3q.pdb", "p3r.pdb", "p3s.pdb",
        "p3t.pdb", "p3u.pdb", "p3v.pdb", "p3w.pdb", "p3x.pdb", "p4.pdb",
        "p5.pdb", "p5a.pdb", "p5b.pdb", "p5c.pdb", "p5d.pdb", "p5e.pdb",
        "p5f.pdb", "p5g.pdb", "p5h.pdb", "p5i.pdb", "p5j.pdb", "p5k.pdb",
        "p5l.pdb", "p5m.pdb", "p6.pdb", "p7.pdb", "p8.pdb", "p9.pdb",
        "p10.pdb", "p10a.pdb", "p10b.pdb", "p11.pdb", "p12.pdb", "p13.pdb",
        "p14.pdb", "p15.pdb"
    ]
    
    # Example: To use a different file list, comment the above and uncomment below:
    # file_list = [
    #     "p1.pdb", "p2.pdb", "p3.pdb"
    # ]
    
    # Filter to only existing files
    existing_files = [f for f in file_list if os.path.exists(f)]
    
    if not existing_files:
        print("Error: No p*.pdb files found!")
        return []
    
    print(f"Searching in {len(existing_files)} files...")
    
    # Pattern to search for
    pattern = r'C1  MOL B|Br8  MOL B|OD1 ASP A (124|108|123|144|106|105|125|103|129)|OD2 ASP A (103|123|109|118|124| 92)'
    
    all_matches = []
    for pdb_file in existing_files:
        stdout, _ = run_command(f"grep -s -E '{pattern}' {pdb_file}")
        if stdout:
            lines = stdout.strip().split('\n')
            for line in lines:
                all_matches.append(f"{pdb_file}:{line}")
    
    if all_matches:
        print(f"✓ Found {len(all_matches)} matching lines")
        for line in all_matches[:10]:  # Show first 10
            print(f"  {line}")
        if len(all_matches) > 10:
            print(f"  ... and {len(all_matches) - 10} more")
    else:
        print("No matches found!")
    
    return all_matches

def parse_pdb_line(line):
    """Parse coordinates from a PDB line"""
    if ':' in line:
        line = line.split(':', 1)[1]
    
    try:
        x = float(line[30:38].strip())
        y = float(line[38:46].strip())
        z = float(line[46:54].strip())
        return x, y, z
    except (ValueError, IndexError):
        try:
            parts = line.split()
            for i in range(len(parts) - 2):
                try:
                    x = float(parts[i])
                    y = float(parts[i + 1])
                    z = float(parts[i + 2])
                    if all(abs(coord) < 1000 for coord in [x, y, z]):
                        return x, y, z
                except ValueError:
                    continue
        except:
            pass
        return None

def calculate_distance(coord1, coord2):
    """Calculate Euclidean distance between two 3D points"""
    x1, y1, z1 = coord1
    x2, y2, z2 = coord2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)

def identify_atom_type(line):
    """Identify what type of atom this line represents"""
    line_upper = line.upper()
    
    if ("OD1" in line_upper or "OD2" in line_upper) and "ASP" in line_upper:
        return "oxygen"
    
    if ("C1" in line_upper and "MOL" in line_upper):
        return "carbon"
    
    if ("BR8" in line_upper or "BR1" in line_upper) and "MOL" in line_upper:
        return "halogen"
    
    if (re.search(r'\b(BR|I|CL|F)\b', line_upper) and "MOL" in line_upper):
        return "halogen"
    
    return "unknown"

def step3_generate_efin(grep_lines):
    """Execute gen_efin.py functionality"""
    print("\n" + "="*60)
    print("STEP 3: Generating efin input files")
    print("="*60)
    
    if not grep_lines:
        print("Error: No grep lines to process!")
        return False, None, None
    
    # Categorize all lines by atom type
    oxygen_lines = []
    carbon_lines = []
    halogen_lines = []
    
    print("\nAnalyzing grep results:")
    for i, line in enumerate(grep_lines):
        atom_type = identify_atom_type(line)
        coords = parse_pdb_line(line)
        
        # Extract atom serial number for display
        serial_num = None
        if ':' in line:
            clean_line = line.split(':', 1)[1]
        else:
            clean_line = line
        
        try:
            serial_num = clean_line[6:11].strip()
        except:
            serial_num = str(i+1)
        
        print(f"[{serial_num}] {atom_type}: {coords}")
        
        if atom_type == "oxygen" and coords:
            oxygen_lines.append((serial_num, coords, line))
        elif atom_type == "carbon" and coords:
            carbon_lines.append((serial_num, coords, line))
        elif atom_type == "halogen" and coords:
            halogen_lines.append((serial_num, coords, line))
    
    # Handle oxygen selection
    if len(oxygen_lines) == 0:
        print("\nError: No oxygen (OD1/OD2) coordinates found!")
        return False, None, None
    elif len(oxygen_lines) == 1:
        oxygen_coords = oxygen_lines[0][1]
        print(f"\nUsing oxygen atom: {oxygen_lines[0][0]}")
    else:
        print(f"\nFound {len(oxygen_lines)} oxygen atoms:")
        for serial, coords, line in oxygen_lines:
            print(f"  [{serial}] {coords}")
        
        while True:
            choice = input(f"Enter oxygen atom number to use [{oxygen_lines[0][0]}]: ").strip()
            if not choice:
                choice = oxygen_lines[0][0]
            
            selected = None
            for serial, coords, line in oxygen_lines:
                if serial == choice:
                    selected = coords
                    break
            
            if selected:
                oxygen_coords = selected
                print(f"Selected oxygen: {choice}")
                break
            else:
                print(f"Invalid choice. Please enter one of: {', '.join([s[0] for s in oxygen_lines])}")
    
    # Handle carbon selection
    if len(carbon_lines) == 0:
        print("\nError: No carbon coordinates found!")
        return False, None, None
    elif len(carbon_lines) == 1:
        carbon_coords = carbon_lines[0][1]
        print(f"Using carbon atom: {carbon_lines[0][0]}")
    else:
        print(f"\nFound {len(carbon_lines)} carbon atoms:")
        for serial, coords, line in carbon_lines:
            print(f"  [{serial}] {coords}")
        
        while True:
            choice = input(f"Enter carbon atom number to use [{carbon_lines[0][0]}]: ").strip()
            if not choice:
                choice = carbon_lines[0][0]
            
            selected = None
            for serial, coords, line in carbon_lines:
                if serial == choice:
                    selected = coords
                    break
            
            if selected:
                carbon_coords = selected
                print(f"Selected carbon: {choice}")
                break
            else:
                print(f"Invalid choice. Please enter one of: {', '.join([s[0] for s in carbon_lines])}")
    
    # Handle halogen selection
    if len(halogen_lines) == 0:
        print("\nError: No halogen coordinates found!")
        return False, None, None
    elif len(halogen_lines) == 1:
        halogen_coords = halogen_lines[0][1]
        print(f"Using halogen atom: {halogen_lines[0][0]}")
    else:
        print(f"\nFound {len(halogen_lines)} halogen atoms:")
        for serial, coords, line in halogen_lines:
            print(f"  [{serial}] {coords}")
        
        while True:
            choice = input(f"Enter halogen atom number to use [{halogen_lines[0][0]}]: ").strip()
            if not choice:
                choice = halogen_lines[0][0]
            
            selected = None
            for serial, coords, line in halogen_lines:
                if serial == choice:
                    selected = coords
                    break
            
            if selected:
                halogen_coords = selected
                print(f"Selected halogen: {choice}")
                break
            else:
                print(f"Invalid choice. Please enter one of: {', '.join([s[0] for s in halogen_lines])}")
    
    if not oxygen_coords:
        print("\nError: Oxygen (OD1/OD2) coordinates not found!")
        return False, None, None
    if not carbon_coords:
        print("\nError: Carbon coordinates not found!")
        return False, None, None
    if not halogen_coords:
        print("\nError: Halogen (Br/I/Cl/F) coordinates not found!")
        return False, None, None
    
    print()  # blank line for readability
    
    v1x, v1y, v1z = oxygen_coords
    v2x_oc, v2y_oc, v2z_oc = carbon_coords
    v2x_ox, v2y_ox, v2z_ox = halogen_coords
    
    distance_oc = calculate_distance(oxygen_coords, carbon_coords)
    distance_ox = calculate_distance(oxygen_coords, halogen_coords)
    
    point_x_oc = (v1x + v2x_oc) / 2
    point_y_oc = (v1y + v2y_oc) / 2
    point_z_oc = (v1z + v2z_oc) / 2
    
    point_x_ox = (v1x + v2x_ox) / 2
    point_y_ox = (v1y + v2y_ox) / 2
    point_z_ox = (v1z + v2z_ox) / 2
    
    template = """TYPE = QUANT
FILE_TYPE = PDB
UNIT = ANS
NAME = {name}
CHARGE_SELECT = ALL
DIRECTION = MANUAL
V1X = {v1x:.3f}
V1Y = {v1y:.3f}
V1Z = {v1z:.3f}
V2X = {v2x:.3f}
V2Y = {v2y:.3f}
V2Z = {v2z:.3f}
POINT_X = {point_x:.3f}
POINT_Y = {point_y:.3f}
POINT_Z = {point_z:.3f}
FORCE_FIELD = AMBER
N_TERMINAL = 1
C_TERMINAL = 300
"""
    
    # Create efin_oc.inp
    oc_content = template.format(
        name="prot_la_oc",
        v1x=v1x, v1y=v1y, v1z=v1z,
        v2x=v2x_oc, v2y=v2y_oc, v2z=v2z_oc,
        point_x=point_x_oc, point_y=point_y_oc, point_z=point_z_oc
    )
    
    with open("efin_oc.inp", "w") as f:
        f.write(oc_content)
    
    # Create efin_ox.inp
    ox_content = template.format(
        name="prot_la_ox",
        v1x=v1x, v1y=v1y, v1z=v1z,
        v2x=v2x_ox, v2y=v2y_ox, v2z=v2z_ox,
        point_x=point_x_ox, point_y=point_y_ox, point_z=point_z_ox
    )
    
    with open("efin_ox.inp", "w") as f:
        f.write(ox_content)
    
    print("\n*****efin_oc.inp & efin_ox.inp files created successfully!*****")
    print(f"\nDistance between O (OD1/OD2) and C: {distance_oc:.3f} Å")
    print(f"Distance between O (OD1/OD2) and halogen: {distance_ox:.3f} Å")
    
    return True, distance_oc, distance_ox

def step4_run_titan():
    """Run TITAN on generated efin files"""
    print("\n" + "="*60)
    print("STEP 4: Running TITAN")
    print("="*60)
    
    # Check if efin files exist
    if not os.path.exists("efin_oc.inp"):
        print("Error: efin_oc.inp not found!")
        return False
    if not os.path.exists("efin_ox.inp"):
        print("Error: efin_ox.inp not found!")
        return False
    
    titan_script = "/opt/compchem/TITAN-2.0.8/stand-alone scripts/run_titan.py"
    
    # Check if TITAN script exists
    if not os.path.exists(titan_script):
        print(f"Warning: TITAN script not found at {titan_script}")
        print("Skipping TITAN execution. Please run manually if needed:")
        print(f"  python3 '{titan_script}' efin_oc.inp efin_ox.inp &")
        return True
    
    print("Running TITAN on efin_oc.inp...")
    cmd_oc = f"python3 '{titan_script}' efin_oc.inp"
    stdout_oc, stderr_oc = run_command(cmd_oc)
    if stdout_oc:
        print(stdout_oc)
    
    print("\nRunning TITAN on efin_ox.inp...")
    cmd_ox = f"python3 '{titan_script}' efin_ox.inp"
    stdout_ox, stderr_ox = run_command(cmd_ox)
    if stdout_ox:
        print(stdout_ox)
    
    print("\n✓ TITAN execution completed!")
    
    return True

##def fix_pdb_for_titan():
##    """Fix PDB files for TITAN compatibility by removing chain identifiers"""
##    pdb_files = ["prot_la_oc.pdb", "prot_la_ox.pdb"]
##    
##    for pdb_file in pdb_files:
##        if not os.path.exists(pdb_file):
##            print(f"Warning: {pdb_file} not found, skipping...")
##            continue
##            
##        print(f"Fixing {pdb_file} for TITAN compatibility...")
##        
##        with open(pdb_file, 'r') as f:
##            lines = f.readlines()
##        
##        fixed_lines = []
##        for line in lines:
##            if line.startswith(('ATOM', 'HETATM')):
##                # Remove chain identifier (column 21) by replacing with space
##                if len(line) > 21:
##                    line = line[:21] + ' ' + line[22:]
##            fixed_lines.append(line)
##        
##        with open(pdb_file, 'w') as f:
##            f.writelines(fixed_lines)
##        
##        print(f"✓ Fixed {pdb_file}")
##
##def step4_run_titan():
##    """Run TITAN on generated efin files"""
##    print("\n" + "="*60)
##    print("STEP 4: Running TITAN")
##    print("="*60)
##    
##    # Check if efin files exist
##    if not os.path.exists("efin_oc.inp"):
##        print("Error: efin_oc.inp not found!")
##        return False
##    if not os.path.exists("efin_ox.inp"):
##        print("Error: efin_ox.inp not found!")
##        return False
##    
##    # Apply TITAN compatibility fix
##    fix_pdb_for_titan()
##    
##    titan_script = "/opt/compchem/TITAN-2.0.8/stand-alone scripts/run_titan.py"
##    
##    # Check if TITAN script exists
##    if not os.path.exists(titan_script):
##        print(f"Warning: TITAN script not found at {titan_script}")
##        print("Skipping TITAN execution. Please run manually if needed:")
##        print(f"  python3 '{titan_script}' efin_oc.inp efin_ox.inp &")
##        return True
##    
##    success = True
##    
##    print("Running TITAN on efin_oc.inp...")
##    cmd_oc = f"python3 '{titan_script}' efin_oc.inp"
##    stdout_oc, stderr_oc = run_command(cmd_oc)
##    if stdout_oc:
##        print(stdout_oc)
##    if stderr_oc and "Error" in stderr_oc and "Traceback" in stderr_oc:
##        print(f"TITAN failed with error: {stderr_oc}")
##        success = False
##    
##    print("\nRunning TITAN on efin_ox.inp...")
##    cmd_ox = f"python3 '{titan_script}' efin_ox.inp"
##    stdout_ox, stderr_ox = run_command(cmd_ox)
##    if stdout_ox:
##        print(stdout_ox)
##    if stderr_ox and "Error" in stderr_ox and "Traceback" in stderr_ox:
##        print(f"TITAN failed with error: {stderr_ox}")
##        success = False
##    
##    if success:
##        print("\n✓ TITAN execution completed successfully!")
##    else:
##        print("\n⚠ TITAN execution completed with errors!")
##    
##    return success

def step5_grep_ef_results():
    """Grep for EF results from .ef files"""
    print("\n" + "="*60)
    print("STEP 5: Extracting Electric Field Results")
    print("="*60)
    
    # Check if any .ef files exist
    ef_files = glob.glob("*.ef")
    if not ef_files:
        print("Warning: No .ef files found. TITAN may not have completed successfully.")
        return
    
    print(f"Found {len(ef_files)} .ef file(s)")
    
    # Grep for total strength
    print("\n--- TOTAL STRENGTH OF THE EF ---")
    stdout_strength, _ = run_command("grep -R ' TOTAL STRENGTH OF THE EF:' *.ef")
    if stdout_strength:
        print(stdout_strength.strip())
    else:
        print("No results found")
    
    # Grep for direction vector
    print("\n--- THE DIRECTION VECTOR V ---")
    stdout_direction, _ = run_command("grep -ri ' THE DIRECTION VECTOR V IS' *.ef")
    if stdout_direction:
        print(stdout_direction.strip())
    else:
        print("No results found")

def main():
    print("\n" + "="*60)
    print("COMBINED WORKFLOW SCRIPT")
    print("Combines: prep.sh -> grep.sh -> gen_efin.py -> run_titan")
    print("="*60)
    
    # Step 1: Prepare protein structure
    if not step1_prep():
        print("\nWorkflow failed at Step 1")
        sys.exit(1)
    
    # Step 2: Grep for specific atoms
    grep_results = step2_grep()
    
    # Step 3: Generate efin files
    success, distance_oc, distance_ox = step3_generate_efin(grep_results)
    if not success:
        print("\nWorkflow failed at Step 3")
        sys.exit(1)
    
    # Step 4: Run TITAN
    if not step4_run_titan():
        print("\nWorkflow failed at Step 4")
        sys.exit(1)
    
    # Step 5: Extract EF results
    step5_grep_ef_results()
    
    #print("\n" + "="*60)
    #print("✓ ALL STEPS COMPLETED SUCCESSFULLY!")
    #print("="*60)
    #print("\nGenerated files:")
    #print("  - prot_la.pdb")
    #print("  - prot_la_oc.pdb")
    #print("  - prot_la_ox.pdb")
    #print("  - efin_oc.inp")
    #print("  - efin_ox.inp")
    print(f"\nDistance between O (OD1/OD2) and C: {distance_oc:.3f} Å")
    print(f"Distance between O (OD1/OD2) and halogen: {distance_ox:.3f} Å")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
