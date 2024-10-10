# CS744-Project

In this project, we aim to investigate the effects of spatially and temporally co-locating different ML workloads across GPUs and across nodes on a cluster. 

We begin by broadly categorizing the workloads we evaluate into two categories – memory-intensive worloads and compute-intensive workloads – based on the profiling metrics gathered using NSight Compute. 

We then study the spatial and temporal effects by considering different placements for both memory-intensive and compute-intensive workloads on TACC Frontera. In our experiments, we measure the power, temperature, GPU Utilization and frequency for each run using nvidia-smi.

We also present experiments that introduce cooldown periods between different workload runs to check if that can improve the thermal efficiency and overall system performance. Based on the results, we then comment on the effectiveness of different placement strategies for memory-intensive and compute-intensive workloads.

Paths to files:

- Report: gpu-spatiotemporal-colocation/gpu_temporal_spatial_colocation.pdf
- Poster Presentation: gpu-spatiotemporal-colocation /poster-presentation.jpg
- Spatial Colocation Simulation Results: gpu-spatiotemporal-colocation/spatial-colocation
- Temporal Colocation Simulation Results: gpu-spatiotemporal-colocation/temporal-colocation
- Colocation and Plotting Scripts: gpu-spatiotemporal-colocation/src
- Profiling Results: gpu-spatiotemporal-colocation/src/similarity.png
