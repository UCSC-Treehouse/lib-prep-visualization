# Issue #7: High Memory Usage During `process_data.py` script

When running the `process_data.py` script on the full riboD and polyA compendia, we observed that the script was consuming an excessive amount of memory, leading to system instability and crashes. Crashes will occur when the system runs out of available disk for swap space.

## Steps to Recreate the Issue

This issue can be recreated by executing the script in a docker container with limited memory resources.

Using the following `Dockerfile`, we can create a docker image for testing:
```Dockerfile
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && apt-get install -y procps


COPY . .

RUN pip install --no-cache-dir -e .

CMD ["bash"]
```

Build the docker container:
```bash
docker build -t lib-prep-visualization .
```

Launch the docker container with limited memory using this command:
```bash
docker run -it --memory=16g --memory-swap=4g lib-prep-visualization
```

The memory and swap settings may differ based on your system's available resources. Docker defaults to a swap limit of 1GB if not specified. To increase swap space,
you can edit the settings inside of the docker desktop application Settings -> Resources -> Advanced -> Swap Size. Increasing past 4GB will require manually adjusting
the Docker VM via the command line.

This system would ideally be enough to run the `process_data.py` script, but due to the current high memory implemtnentation of the script, it will crash.

## Visualizing the Memory Usage Overflow

Open 2 terminal windows on your host machine. Start the docker container in one terminal window using the command above. Exec into the running container from the second terminal window:

```bashdocker ps
docker exec -it <container_id> bash
```

In the exec'd terminal window, run the following commands to monitor memory usage:

```bash
watch -n 1 "cat /proc/meminfo | grep -E 'Mem|Swap' | awk '{printf \"%s %.2f GB\n\", \$1, \$2/1024/1024}'"
```

In the original terminal window where the docker container is running, execute the `process_data.py` script:

```bash
python scripts/process_data.py --config configs/process_data/polyA_vs_riboD_v25.01
```

The physical memory can handle loading the majority of the data from .tsv files, but when it reaches the step where it needs to perform UMAP dimensionality reduction, the memory usage spikes and exceeds the available memory and swap space, leading to a crash.

## Diagnosing the Crash

To diagnose the crash, we can exit the interactive container terminal and run the following script to capture the Exit Code of the last run process:

```bash
docker inspect <container_id> --format='{{.State.ExitCode}}'
```

This will result in an Exit Code of `137`, which indicates that the process was killed due to an out-of-memory (OOM) condition.

Exit code 137 = 128 + 9:
- 128 → base for a process terminated by a signal
- 9 → signal number SIGKILL

To confirm that it was a memory issue, we can check that it was killed by the OOM killer:
```bash
docker inspect <container_id> --format='{{.State.OOMKilled}}'
```

We get `true`, confirming that the process was indeed killed due to an out-of-memory condition.

## Conclusion and Next Steps

The high memory usage (>20GB) during the execution of the `process_data.py` script seems unreasonable. The merged file is ~6-8GB, so it should be feasible to process it within a 16GB memory limit. We need to investigate the memory management within the script. It may be possible that concatenating the dataframes as anndata objects is causing excessive memory overhead. It may also be possible that setting
some of the scanpy functions to the low memory setting may help reduce memory usage and dependence on swap space.