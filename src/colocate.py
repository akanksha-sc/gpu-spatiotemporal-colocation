import os
import subprocess
import argparse
import csv
import shutil


time_stamp = """
    ts=$(date +%s%N)   
"""

base_run = """#!/bin/bash
uarch=$(uname -m)
NUM_KERN=500
DEVICE_ID=0
SIZE=25536

if [[ "$uarch" == *ppc64le* ]]; then
    echo "Base image (nvcr.io/nvidia/pytorch) only supports LINUX/AMD64 and LINUX/ARM64 architectures. Aborting." 
else
"""

preprocess_resnet = """
    singularity run --nv docker://nvcr.io/nvidia/pytorch:22.06-py3 ./dataloader.sh
"""

preprocess_bert="""
    singularity run --nv docker://nvcr.io/nvidia/pytorch:22.06-py3 scripts/install.sh
"""

preprocess_pagerank="""
    ./fetch-input.sh
    ./build-pagerank.sh
"""

run_pagerank = """
    ./run-pagerank.sh 0 0
"""

run_knn = """
    echo "RUNNING KNN!! " 
    singularity run --nv docker://nvcr.io/nvidia/rapidsai/rapidsai:cuda10.1-runtime-centos7 python3 knn.py 
    echo "KNN run completed."    
"""

run_sgemm = """
    echo "RUNNING SGEMM!! "
    singularity run --nv docker://nvidia/cuda:12.4.1-devel-rockylinux8 ./sgemm_nvidia ${SIZE} ${NUM_KERN} ${DEVICE_ID}
    echo "SGEMM run completed."   
"""
    
run_resnet="""
    echo "RUNNING RESNET!! " 
    singularity run --nv docker://nvcr.io/nvidia/pytorch:22.06-py3 ./run-resnet-single.sh 0 1
    echo "ResNet run completed."
"""

run_bert="""

    singularity run --nv docker://nvcr.io/nvidia/pytorch:22.06-py3 scripts/run_pretraining_lamb.sh 0
    echo "Bert run completed."
"""

def get_slurm_node_names(partition_name):
    # Command to get node names from the specified partition
    command = ['sinfo', '-N', '-h', '-p', partition_name, '--format=%N']

    # Execute the command and capture the output
    result = subprocess.run(command, capture_output=True, text=True)

    # Check if the command was successful
    if result.returncode != 0:
        print("Error executing sinfo command:", result.stderr)
        return None

    # Split the output into a list of node names
    node_names = result.stdout.strip().split('\n')

    return node_names

def create_script_run(run_list, node, runtime_out):
    
    script = base_run 

    if 'resnet' in run_list:
        script += preprocess_resnet

    if 'bert' in run_list:
        script += preprocess_bert

    if 'pagerank' in run_list:
        script += preprocess_pagerank

    for i in run_list:
        script += time_stamp
        if (i=='knn'):
            script += run_knn
            script += """
    echo \"{},$((($(date +%s%N) - $ts)/1000000))\" >> {}
            """.format(i,runtime_out)
        elif (i=='resnet'):
            script += run_resnet
            script += """
    echo \"{},$((($(date +%s%N) - $ts)/1000000))\" >> {}
            """.format(i,runtime_out)
        elif (i=='sgemm'):
            script += run_sgemm
            script += """
    echo \"{},$((($(date +%s%N) - $ts)/1000000))\" >> {}
            """.format(i,runtime_out)
        elif (i=='bert'):
            script += run_bert
            script += """
    echo \"{},$((($(date +%s%N) - $ts)/1000000))\" >> {}
            """.format(i,runtime_out)
        elif (i=='pagerank'):
            script += run_pagerank
            script += """
    echo \"{},$((($(date +%s%N) - $ts)/1000000))\" >> {}
            """.format(i,runtime_out)
        elif (len(i)==0):
            script += """
    sleep 60s
"""
        elif (i.isdigit()):
            script += """
    sleep {}s
""".format(i)
        elif (i=="idle"):
            script += """
    sleep 60s
"""
    script += """
fi
"""
    script_path = "colocate/run_job_{}.sh".format(node)

    with open(script_path, 'w') as f:
        f.write(script)
    os.chmod(script_path, 0o0777)

def create_evaluate(node):
    
    script = """
#!/bin/bash
ts=$(date +%Y%m%d_%H%M%S)

mkdir -p $2/profiling
echo "Dumping Stats to $2/profiling/metrics_gpu_$ts_$1.csv"
{{
echo "PROFILING..."
nvidia-smi --query-gpu=timestamp,temperature.gpu,power.draw,clocks.sm,utilization.gpu,clocks.mem,fan.speed,clocks.gr --format=csv -lms 100 &> $2/profiling/metrics_gpu_${{ts}}_$1.csv 
}} & ./run_job_{0}.sh
sleep 5s
echo "Workload Run finished! Killing background nvidia-smi process"
pkill nvidia-smi
echo "Finished!"
    """.format(node)
    
    script_path = "colocate/evaluate_{}.sh".format(node)

    with open(script_path, 'w') as f:
        f.write(script)

    os.chmod(script_path, 0o0777)

DICT_NODE_RUN = {}

def main():
    count = 0
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_file', type=str)
    parser.add_argument('--cluster', type=str, default='frontera')
    parser.add_argument('--output', type=str, default='test')
    parser.add_argument('--email', type=str, default='tanand5@wisc.edu')
    parser.add_argument('--partition', type=str, default=None)
    parser.add_argument('--job-name', type=str, default='')
    args = parser.parse_args()
    

    partition_name = 'rtx'

    if (args.partition==None):
        if(args.cluster=='frontera'):
            partition_name = 'rtx'
        elif(args.cluster=='lonestar'):
            partition_name = 'gpu-a100'
    else:   
        partition_name = args.partition

    prefix = """#!/bin/bash
#SBATCH -J Colocation-{0}              # Job name
#SBATCH -o ../debug/Colocation-{0}.%j.out     # Name of stdout output file
#SBATCH -e ../debug/Colocation-{0}.%j.err     # Name of stderr error file
#SBATCH -p {1}                  # Queue (partition) name
#SBATCH -N 1                     # Total # of nodes (must be 1 for serial)
#SBATCH -n 1                     # Total # of mpi tasks (should be 1 for serial)
#SBATCH -t 02:00:00              # Run time (hh:mm:ss)
#SBATCH --mail-user={2}
#SBATCH --mail-type=all          # Send email at begin and end of job
#SBATCH --chdir=/work/10000/tanmayanand2903/colocate
""".format(args.job_name, partition_name, args.email)

    node_names = get_slurm_node_names(partition_name)

    visited_nodes = []
    with open(args.csv_file) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            visited_nodes.append(row[0].strip())
            DICT_NODE_RUN[row[0].strip()] = row[1:]

    for node in visited_nodes: 

        if (node not in node_names) and (node != 'any'):
            print("INVALID NODE ID {} ON THIS CLUSTER!!".format(node))
            continue

        specify_node = f'#SBATCH -w {node}'
        if (node=='any'):
            specify_node = ""

        n_ = node
        suffix = """
        
node=$SLURM_JOB_NODELIST
module load tacc-apptainer
module load cuda
echo "Node Number: ${{node}}"
./evaluate_{0}.sh ${{node}} ../{1}
""".format(n_, args.output)

        script = prefix + specify_node + suffix
        script_path = f'slurm-{node}-run-colocation-multi.slurm'

        if not os.path.exists(args.output):
            os.makedirs(args.output)
        shutil.copyfile(args.csv_file, os.path.join(args.output,'input.csv'))

        create_evaluate(node)
        create_script_run(DICT_NODE_RUN[node],node,os.path.join('../',args.output,'{}_runtime.txt'.format(node)))

        with open(script_path, 'w') as f:
            f.write(script)
                
        result = subprocess.run(['sbatch', script_path],capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Job successfully submitted for node {node}")
        else:
            print(f"Failed to submit job for node {node}. Error: {result.stderr}")

        if os.path.exists(script_path):
            os.remove(script_path)
        
        count+=1

    print("{} jobs have been submitted.".format(count))

if __name__ == '__main__':
    main()
