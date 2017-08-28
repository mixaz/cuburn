FROM nvidia/cuda:8.0-runtime-ubuntu16.04

LABEL com.nvidia.volumes.needed="nvidia_driver"

ENV PATH /usr/local/nvidia/bin:${PATH}
ENV LD_LIBRARY_PATH /usr/local/nvidia/lib:/usr/local/nvidia/lib64:${LD_LIBRARY_PATH}

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && apt-get upgrade -y && apt-get install -y git net-tools nvidia-375 cuda && apt-get clean all

RUN cd /root &&git clone git://github.com/novnc/noVNC && cp /root/noVNC/vnc.html /root/noVNC/index.html && mkdir /root/.vnc

RUN git clone --recursive http://git.tiker.net/trees/pycuda.git
RUN git clone --recursive https://github.com/twobombs/cuburn.git

RUN cd /pycuda&&configure&&make&&make install

RUN add-apt-repository universe
RUN apt-get update
RUN apt-get install -y libboost-all-dev python-pycuda python-pip && apt-get clean all

RUN pip install numpy scipy

EXPOSE 5900 6080
