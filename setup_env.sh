#!/bin/bash

# 激活虚拟环境
source /home/zhang/carla_env/bin/activate

# 设置CARLA根目录，请根据你的安装路径修改
CARLA_ROOT=/home/zhang/下载/CARLA_0.9.16

# 设置Scenario Runner根目录
SCENARIO_RUNNER_ROOT=/home/zhang/scenario_runner

# 查找carla的egg文件，因为可能版本和Python版本不同，这里使用通配符
EGG_FILE=$(ls $CARLA_ROOT/下载/CARLA_0.9.16/PythonAPI/carla/dist/carla-0.9.16-cp310-cp310-manylinux_2_31_x86_64.whl | head -1)

# 设置PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$EGG_FILE
export PYTHONPATH=$PYTHONPATH:$CARLA_ROOT/PythonAPI/carla
export PYTHONPATH=$PYTHONPATH:$CARLA_ROOT/PythonAPI/agents
export PYTHONPATH=$PYTHONPATH:$SCENARIO_RUNNER_ROOT

echo "环境变量设置完成"
echo "PYTHONPATH: $PYTHONPATH"